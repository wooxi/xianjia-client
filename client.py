"""
闲管家 API HTTP 客户端

提供异步 HTTP 请求封装，包含签名生成、请求发送、响应解析和错误处理。
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Type, Union

import httpx

from .config import Config
from .exceptions import RequestError, ResponseError, SignatureError, TimestampExpiredError
from .utils.signature import (
    generate_body_md5,
    generate_signature,
    generate_signed_params,
    get_timestamp,
    validate_timestamp,
)

logger = logging.getLogger(__name__)


class XianjiaClient:
    """
    闲管家 API 异步 HTTP 客户端

    提供完整的 API 交互能力，包括自动签名、请求重试、响应解析等。
    使用 asyncio + httpx 实现高性能异步请求。

    Attributes:
        config: 配置实例，包含 appKey、appSecret 等参数
        timeout: HTTP 请求超时时间（秒）
        max_retries: 最大重试次数

    Example:
        >>> async def main():
        ...     config = Config(app_key="key", app_secret="secret")
        ...     client = XianjiaClient(config)
        ...     result = await client.request("POST", "/v1/orders", {"action": "create"})
        ...     print(result)
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        config: Config,
        session: Optional[httpx.AsyncClient] = None,
    ) -> None:
        """
        初始化客户端

        Args:
            config: 配置实例
            session: 可选的 httpx 异步会话，用于连接池复用
        """
        self.config = config
        self._session = session
        self._owns_session = session is None  # 标记是否由本客户端管理会话生命周期

    async def __aenter__(self) -> "XianjiaClient":
        """异步上下文管理器入口"""
        if self._owns_session:
            self._session = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                follow_redirects=False,
            )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """异步上下文管理器出口"""
        if self._owns_session and self._session:
            await self._session.aclose()

    async def request(
        self,
        method: str,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        发送 API 请求

        自动处理签名生成、请求发送、响应解析和错误重试。

        Args:
            method: HTTP 方法（GET、POST、PUT、DELETE 等）
            endpoint: API 端点路径（如 "/v1/orders"）
            body: 请求体字典（用于 POST/PUT 请求）
            params: URL 查询参数
            headers: 额外的 HTTP 请求头
            retry_count: 当前重试次数（内部使用，调用方无需设置）

        Returns:
            Dict[str, Any]: 解析后的响应数据

        Raises:
            SignatureError: 签名生成失败
            RequestError: HTTP 请求失败
            ResponseError: 响应解析失败或业务错误
            TimestampExpiredError: 时间戳过期

        Example:
            >>> async with XianjiaClient(config) as client:
            ...     result = await client.request(
            ...         method="POST",
            ...         endpoint="/v1/orders",
            ...         body={"action": "create", "order_id": "123"}
            ...     )
        """
        # 构建完整 URL
        url = self.config.get_api_url(endpoint)

        # 生成签名参数
        try:
            signed_params = generate_signed_params(
                app_key=self.config.app_key,
                app_secret=self.config.app_secret,
                body=body,
                timestamp=None,  # 使用当前时间
                include_body=False,  # body 单独作为 JSON 发送
            )
        except SignatureError as e:
            logger.error(f"签名生成失败：{e}")
            raise

        # 验证时间戳有效性
        try:
            validate_timestamp(signed_params["timestamp"], validity_ms=self.config.timestamp_validity)
        except TimestampExpiredError as e:
            logger.error(f"时间戳验证失败：{e}")
            raise

        # 合并请求头
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if headers:
            request_headers.update(headers)

        # 添加签名参数到请求头或 URL
        # 根据闲管家 API 规范，签名参数通常放在请求头或 URL 参数中
        # 这里选择放在 URL 参数中（query string）
        if params:
            params.update(signed_params)
        else:
            params = signed_params

        # 序列化请求体（无空格）
        json_content = None
        if body is not None:
            try:
                json_content = json.dumps(body, separators=(",", ":"))
            except (TypeError, ValueError) as e:
                raise RequestError(
                    message=f"请求体序列化失败：{str(e)}",
                    code="BODY_SERIALIZE_ERROR",
                )

        # 确保会话存在
        if self._session is None:
            self._session = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                follow_redirects=False,
            )

        # 发送请求
        try:
            logger.debug(
                f"发送请求：{method} {url}, params={params}, body={body}"
            )

            response = await self._session.request(
                method=method.upper(),
                url=url,
                params=params,
                content=json_content,
                headers=request_headers,
            )

            logger.debug(
                f"收到响应：{response.status_code}, body={response.text[:200]}..."
                if len(response.text) > 200
                else f"收到响应：{response.status_code}, body={response.text}"
            )

        except httpx.TimeoutException as e:
            logger.warning(f"请求超时：{method} {url}")
            if retry_count < self.config.max_retries:
                return await self._retry_request(
                    method, endpoint, body, params, headers, retry_count + 1
                )
            raise RequestError(
                message=f"请求超时（{self.config.timeout}秒）",
                code="TIMEOUT",
            ) from e

        except httpx.NetworkError as e:
            logger.warning(f"网络错误：{method} {url}, {str(e)}")
            if retry_count < self.config.max_retries:
                return await self._retry_request(
                    method, endpoint, body, params, headers, retry_count + 1
                )
            raise RequestError(
                message=f"网络错误：{str(e)}",
                code="NETWORK_ERROR",
            ) from e

        except httpx.HTTPError as e:
            logger.error(f"HTTP 错误：{method} {url}, {str(e)}")
            raise RequestError(
                message=f"HTTP 错误：{str(e)}",
                code="HTTP_ERROR",
            ) from e

        # 解析响应
        return await self._parse_response(response, retry_count, method, endpoint, body, headers)

    async def _retry_request(
        self,
        method: str,
        endpoint: str,
        body: Optional[Dict[str, Any]],
        params: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, str]],
        retry_count: int,
    ) -> Dict[str, Any]:
        """
        重试请求

        使用指数退避策略进行重试，每次重试都会重新生成签名（新的时间戳）。

        Args:
            method: HTTP 方法
            endpoint: API 端点
            body: 请求体
            params: URL 参数
            headers: 请求头
            retry_count: 当前重试次数

        Returns:
            Dict[str, Any]: 请求结果

        Raises:
            RequestError: 当超过最大重试次数时抛出
        """
        wait_time = min(2 ** retry_count, 10)  # 指数退避，最大 10 秒
        logger.info(f"重试请求（第 {retry_count}/{self.config.max_retries} 次），{wait_time}秒后重试")

        await asyncio.sleep(wait_time)

        # 重新生成签名（新的时间戳）并发送请求
        return await self.request(method, endpoint, body, params, headers, retry_count)

    async def _parse_response(
        self,
        response: httpx.Response,
        retry_count: int,
        method: str,
        endpoint: str,
        body: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        解析 HTTP 响应

        处理不同状态码的响应，解析 JSON 数据，检查业务错误。

        Args:
            response: httpx 响应对象
            retry_count: 当前重试次数
            method: HTTP 方法
            endpoint: API 端点
            body: 请求体
            headers: 请求头

        Returns:
            Dict[str, Any]: 解析后的响应数据

        Raises:
            RequestError: HTTP 状态码错误
            ResponseError: 响应解析失败或业务错误
        """
        status_code = response.status_code

        # 处理 HTTP 错误状态码
        if status_code >= 400:
            # 4xx 错误通常不需要重试
            if status_code < 500:
                raise RequestError(
                    message=f"请求失败：{response.text}",
                    code=f"HTTP_{status_code}",
                    status_code=status_code,
                    response_body=response.text,
                )

            # 5xx 错误可以尝试重试
            if retry_count < self.config.max_retries:
                return await self._retry_request(
                    method, endpoint, body, None, headers, retry_count + 1
                )

            raise RequestError(
                message=f"服务器错误：{response.text}",
                code=f"HTTP_{status_code}",
                status_code=status_code,
                response_body=response.text,
            )

        # 解析 JSON 响应
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise ResponseError(
                message=f"响应不是有效的 JSON：{str(e)}",
                code="INVALID_JSON",
                raw_response=response.text[:500],
            ) from e

        # 检查业务错误（根据闲管家 API 规范调整）
        # 假设响应格式为：{"code": 0, "message": "success", "data": {...}}
        # 或：{"error": {"code": "xxx", "message": "xxx"}}
        if isinstance(data, dict):
            # 检查错误字段
            if "error" in data and data["error"]:
                error = data["error"]
                error_code = error.get("code", "UNKNOWN_ERROR") if isinstance(error, dict) else str(error)
                error_message = error.get("message", str(error)) if isinstance(error, dict) else str(error)
                raise ResponseError(
                    message=error_message,
                    code=error_code,
                    details=error if isinstance(error, dict) else None,
                    raw_response=data,
                )

            # 检查 code 字段（另一种常见格式）
            if "code" in data:
                code = data["code"]
                if code != 0 and code != "0":
                    message = data.get("message", "未知错误")
                    raise ResponseError(
                        message=message,
                        code=str(code),
                        details={"data": data.get("data")},
                        raw_response=data,
                    )

        return data

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        发送 GET 请求

        Args:
            endpoint: API 端点
            params: URL 查询参数
            headers: 额外的请求头

        Returns:
            Dict[str, Any]: 响应数据

        Example:
            >>> result = await client.get("/v1/orders", params={"status": "pending"})
        """
        return await self.request("GET", endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        发送 POST 请求

        Args:
            endpoint: API 端点
            body: 请求体
            params: URL 查询参数
            headers: 额外的请求头

        Returns:
            Dict[str, Any]: 响应数据

        Example:
            >>> result = await client.post("/v1/orders", body={"action": "create"})
        """
        return await self.request("POST", endpoint, body=body, params=params, headers=headers)

    async def put(
        self,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        发送 PUT 请求

        Args:
            endpoint: API 端点
            body: 请求体
            params: URL 查询参数
            headers: 额外的请求头

        Returns:
            Dict[str, Any]: 响应数据
        """
        return await self.request("PUT", endpoint, body=body, params=params, headers=headers)

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        发送 DELETE 请求

        Args:
            endpoint: API 端点
            params: URL 查询参数
            headers: 额外的请求头

        Returns:
            Dict[str, Any]: 响应数据
        """
        return await self.request("DELETE", endpoint, params=params, headers=headers)

    async def close(self) -> None:
        """
        关闭客户端

        释放 HTTP 会话资源。如果客户端是通过异步上下文管理器创建的，
        则不需要手动调用此方法。

        Example:
            >>> client = XianjiaClient(config)
            >>> await client.post("/v1/orders", body={"action": "create"})
            >>> await client.close()
        """
        if self._owns_session and self._session:
            await self._session.aclose()
            self._session = None

    def __del__(self) -> None:
        """析构函数，确保资源被释放"""
        # 注意：异步资源最好通过异步上下文管理器管理
        # 这里只是作为最后的保障措施
        pass
