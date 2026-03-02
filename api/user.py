"""
闲管家用户/店铺 API 接口模块

提供用户和店铺相关的 API 接口实现，包括授权店铺查询等功能。
"""

import logging
from typing import List, Optional
from datetime import datetime

import httpx

from ..models.shop import ShopInfo

# 配置日志记录
logger = logging.getLogger(__name__)


# API 响应错误码定义
class APIErrorCode:
    """API 错误码常量定义"""
    SUCCESS = 0
    INVALID_TOKEN = 1001
    TOKEN_EXPIRED = 1002
    PERMISSION_DENIED = 1003
    RESOURCE_NOT_FOUND = 1004
    INTERNAL_ERROR = 5000
    RATE_LIMIT_EXCEEDED = 5001


# 自定义异常类
class APIError(Exception):
    """
    API 请求异常基类
    
    Attributes:
        code: 错误码
        message: 错误消息
        details: 详细错误信息（可选）
    """
    def __init__(self, code: int, message: str, details: Optional[str] = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(f"[Error {code}] {message}")


class TokenExpiredError(APIError):
    """Token 过期异常"""
    def __init__(self, message: str = "授权 Token 已过期"):
        super().__init__(APIErrorCode.TOKEN_EXPIRED, message)


class PermissionDeniedError(APIError):
    """权限不足异常"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(APIErrorCode.PERMISSION_DENIED, message)


class ResourceNotFoundError(APIError):
    """资源不存在异常"""
    def __init__(self, message: str = "资源不存在"):
        super().__init__(APIErrorCode.RESOURCE_NOT_FOUND, message)


def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """
    解析日期时间字符串
    
    Args:
        date_str: 日期时间字符串，支持多种格式
        
    Returns:
        Optional[datetime]: 解析后的 datetime 对象，解析失败返回 None
    """
    if not date_str:
        return None
    
    # 支持的日期格式列表
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"无法解析日期时间字符串：{date_str}")
    return None


def _handle_api_response(response: httpx.Response) -> dict:
    """
    处理 API 响应，检查错误并返回解析后的数据
    
    Args:
        response: HTTP 响应对象
        
    Returns:
        dict: 响应数据字典
        
    Raises:
        APIError: 当 API 返回错误时抛出相应异常
        httpx.HTTPStatusError: HTTP 状态码错误
    """
    # 检查 HTTP 状态码
    response.raise_for_status()
    
    # 解析响应体
    try:
        data = response.json()
    except ValueError as e:
        logger.error(f"响应体解析失败：{e}")
        raise APIError(
            code=APIErrorCode.INTERNAL_ERROR,
            message="响应体格式错误，无法解析为 JSON"
        )
    
    # 检查业务错误码（假设成功码为 0 或 success 为 true）
    error_code = data.get("code", data.get("error_code", 0))
    error_message = data.get("message", data.get("error", "未知错误"))
    
    if error_code != 0 and error_code != APIErrorCode.SUCCESS:
        logger.error(f"API 返回错误：code={error_code}, message={error_message}")
        
        # 根据错误码抛出特定异常
        if error_code == APIErrorCode.TOKEN_EXPIRED:
            raise TokenExpiredError(error_message)
        elif error_code == APIErrorCode.PERMISSION_DENIED:
            raise PermissionDeniedError(error_message)
        elif error_code == APIErrorCode.RESOURCE_NOT_FOUND:
            raise ResourceNotFoundError(error_message)
        else:
            raise APIError(code=error_code, message=error_message)
    
    return data


def _shop_from_dict(shop_data: dict) -> ShopInfo:
    """
    将字典数据转换为 ShopInfo 对象
    
    Args:
        shop_data: 包含店铺信息的字典
        
    Returns:
        ShopInfo: 店铺信息对象
    """
    # 解析有效期时间
    valid_end_time = None
    if "valid_end_time" in shop_data:
        valid_end_time = _parse_datetime(shop_data.get("valid_end_time"))
    
    # 构建 ShopInfo 对象
    return ShopInfo(
        authorize_id=shop_data.get("authorize_id", ""),
        user_identity=shop_data.get("user_identity", ""),
        user_name=shop_data.get("user_name", ""),
        user_nick=shop_data.get("user_nick", ""),
        shop_name=shop_data.get("shop_name", ""),
        is_pro=shop_data.get("is_pro", False),
        is_deposit_enough=shop_data.get("is_deposit_enough", False),
        is_valid=shop_data.get("is_valid", False),
        is_trial=shop_data.get("is_trial", False),
        valid_end_time=valid_end_time,
        service_support=shop_data.get("service_support", []),
        item_biz_types=shop_data.get("item_biz_types", [])
    )


def get_authorized_shops(
    api_base_url: str,
    access_token: str,
    timeout: int = 30
) -> List[ShopInfo]:
    """
    查询已授权店铺列表
    
    调用闲管家 API 获取当前用户已授权的所有店铺信息。
    
    Args:
        api_base_url: API 基础 URL，例如 "https://api.xianjia.com"
        access_token: 访问令牌，用于身份验证
        timeout: 请求超时时间（秒），默认 30 秒
        
    Returns:
        List[ShopInfo]: 已授权店铺信息列表
        
    Raises:
        TokenExpiredError: 当访问令牌过期时
        PermissionDeniedError: 当权限不足时
        ResourceNotFoundError: 当资源不存在时
        APIError: 其他 API 错误
        httpx.HTTPError: HTTP 请求错误（网络问题等）
        
    Example:
        >>> shops = get_authorized_shops(
        ...     api_base_url="https://api.xianjia.com",
        ...     access_token="your_access_token"
        ... )
        >>> for shop in shops:
        ...     print(f"店铺：{shop.shop_name}, 有效：{shop.is_valid}")
    """
    # 构建请求 URL
    endpoint = f"{api_base_url.rstrip('/')}/api/user/authorized_shops"
    
    # 设置请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "XianJia-Client/1.0"
    }
    
    logger.info(f"请求已授权店铺列表：{endpoint}")
    
    try:
        # 发送 HTTP GET 请求
        with httpx.Client() as client:
            response = client.get(
                url=endpoint,
                headers=headers,
                timeout=timeout
            )
        
        # 处理响应
        data = _handle_api_response(response)
        
        # 提取店铺列表数据（假设返回格式为 {"data": {"shops": [...]}} 或 {"data": [...]})
        shops_data = data.get("data", {})
        if isinstance(shops_data, dict):
            shops_data = shops_data.get("shops", [])
        elif not isinstance(shops_data, list):
            shops_data = []
        
        # 转换为 ShopInfo 对象列表
        shops = [_shop_from_dict(item) for item in shops_data]
        
        logger.info(f"成功获取 {len(shops)} 个已授权店铺")
        return shops
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP 状态码错误：{e.response.status_code}")
        if e.response.status_code == 401:
            raise TokenExpiredError("访问令牌无效或已过期")
        elif e.response.status_code == 403:
            raise PermissionDeniedError("无权访问该资源")
        elif e.response.status_code == 404:
            raise ResourceNotFoundError("API 端点不存在")
        else:
            raise APIError(
                code=e.response.status_code,
                message=f"HTTP 错误：{e.response.status_code}"
            )
    except httpx.RequestError as e:
        logger.error(f"网络请求错误：{e}")
        raise APIError(
            code=APIErrorCode.INTERNAL_ERROR,
            message=f"网络请求失败：{str(e)}"
        )


def get_shop_detail(
    api_base_url: str,
    access_token: str,
    authorize_id: str,
    timeout: int = 30
) -> ShopInfo:
    """
    获取单个店铺详细信息
    
    Args:
        api_base_url: API 基础 URL
        access_token: 访问令牌
        authorize_id: 授权 ID
        timeout: 请求超时时间（秒）
        
    Returns:
        ShopInfo: 店铺详细信息对象
        
    Raises:
        TokenExpiredError: 当访问令牌过期时
        PermissionDeniedError: 当权限不足时
        ResourceNotFoundError: 当店铺不存在时
        APIError: 其他 API 错误
    """
    endpoint = f"{api_base_url.rstrip('/')}/api/user/shop/{authorize_id}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "XianJia-Client/1.0"
    }
    
    logger.info(f"请求店铺详情：{endpoint}")
    
    try:
        with httpx.Client() as client:
            response = client.get(
                url=endpoint,
                headers=headers,
                timeout=timeout
            )
        
        data = _handle_api_response(response)
        shop_data = data.get("data", {})
        
        return _shop_from_dict(shop_data)
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise TokenExpiredError("访问令牌无效或已过期")
        elif e.response.status_code == 403:
            raise PermissionDeniedError("无权访问该资源")
        elif e.response.status_code == 404:
            raise ResourceNotFoundError(f"店铺不存在：{authorize_id}")
        else:
            raise APIError(
                code=e.response.status_code,
                message=f"HTTP 错误：{e.response.status_code}"
            )
    except httpx.RequestError as e:
        raise APIError(
            code=APIErrorCode.INTERNAL_ERROR,
            message=f"网络请求失败：{str(e)}"
        )
