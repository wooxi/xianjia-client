"""
闲管家 API 自定义异常类

定义客户端可能遇到的各种异常情况，便于调用方进行精确的错误处理。
"""

from typing import Optional, Any, Dict


class XianjiaException(Exception):
    """
    闲管家 API 基础异常类

    所有自定义异常的基类，用于标识来自闲管家客户端的错误。

    Attributes:
        message: 错误描述信息
        code: 错误代码（如果有）
        details: 额外的错误详情（如果有）
    """

    def __init__(
        self,
        message: str = "闲管家 API 错误",
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化基础异常

        Args:
            message: 错误描述信息
            code: 错误代码
            details: 额外的错误详情字典
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        """返回异常的可读字符串表示"""
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class SignatureError(XianjiaException):
    """
    签名相关异常

    当签名生成或验证失败时抛出此异常。

    常见场景：
    - 签名参数缺失（appKey 或 appSecret 为空）
    - 签名计算错误
    - 时间戳过期（超过 5 分钟有效性窗口）
    """

    def __init__(
        self,
        message: str = "签名错误",
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化签名异常

        Args:
            message: 错误描述信息
            code: 错误代码
            details: 额外的错误详情
        """
        super().__init__(message=message, code=code, details=details)


class RequestError(XianjiaException):
    """
    HTTP 请求相关异常

    当网络请求失败或请求参数无效时抛出此异常。

    常见场景：
    - 网络连接失败
    - 请求超时
    - HTTP 状态码错误（4xx）
    - 请求参数验证失败
    """

    def __init__(
        self,
        message: str = "请求错误",
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> None:
        """
        初始化请求异常

        Args:
            message: 错误描述信息
            code: 错误代码
            details: 额外的错误详情
            status_code: HTTP 响应状态码
            response_body: HTTP 响应体内容
        """
        super().__init__(message=message, code=code, details=details)
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        """返回包含状态码的异常字符串表示"""
        parts = [super().__str__()]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        return " ".join(parts)


class ResponseError(XianjiaException):
    """
    响应解析相关异常

    当 API 响应无法解析或响应内容不符合预期时抛出此异常。

    常见场景：
    - 响应不是有效的 JSON 格式
    - 响应缺少必需字段
    - 响应数据结构异常
    - 业务逻辑错误（API 返回 error 字段）
    """

    def __init__(
        self,
        message: str = "响应错误",
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        raw_response: Optional[Any] = None,
    ) -> None:
        """
        初始化响应异常

        Args:
            message: 错误描述信息
            code: 错误代码
            details: 额外的错误详情
            raw_response: 原始响应内容（用于调试）
        """
        super().__init__(message=message, code=code, details=details)
        self.raw_response = raw_response

    def __str__(self) -> str:
        """返回异常字符串表示"""
        base = super().__str__()
        if self.raw_response is not None:
            return f"{base} - 原始响应：{self.raw_response}"
        return base


class TimestampExpiredError(SignatureError):
    """
    时间戳过期异常

    当请求时间戳超过 5 分钟有效性窗口时抛出此异常。

    这是 SignatureError 的子类，便于调用方专门处理时间戳过期场景。
    """

    def __init__(
        self,
        message: str = "时间戳已过期，请重新生成请求",
        code: str = "TIMESTAMP_EXPIRED",
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None,
        current_time: Optional[int] = None,
    ) -> None:
        """
        初始化时间戳过期异常

        Args:
            message: 错误描述信息
            code: 错误代码
            details: 额外的错误详情
            timestamp: 原始请求时间戳（毫秒）
            current_time: 当前时间（毫秒）
        """
        super().__init__(message=message, code=code, details=details)
        self.timestamp = timestamp
        self.current_time = current_time

        if timestamp and current_time:
            diff_seconds = (current_time - timestamp) / 1000
            self.details["timestamp"] = timestamp
            self.details["current_time"] = current_time
            self.details["diff_seconds"] = diff_seconds

    def __str__(self) -> str:
        """返回包含时间差信息的异常字符串表示"""
        base = super().__str__()
        if self.timestamp and self.current_time:
            diff_seconds = (self.current_time - self.timestamp) / 1000
            return f"{base} (已过期 {diff_seconds:.1f} 秒)"
        return base
