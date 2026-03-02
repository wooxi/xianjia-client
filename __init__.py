"""
闲管家 API 客户端基础框架

提供与闲管家 API 交互的完整客户端实现，包括配置管理、签名生成、
HTTP 请求封装和异常处理。
"""

from .client import XianjiaClient
from .config import Config
from .exceptions import XianjiaException, SignatureError, RequestError, ResponseError, TimestampExpiredError

__version__ = "0.1.0"
__all__ = [
    "XianjiaClient",
    "Config",
    "XianjiaException",
    "SignatureError",
    "RequestError",
    "ResponseError",
    "TimestampExpiredError",
]
