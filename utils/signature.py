"""
闲管家 API 签名生成工具

实现 API 请求签名机制，确保请求的完整性和安全性。
签名算法：md5("appKey,bodyMd5,timestamp,appSecret")
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional

from ..exceptions import SignatureError, TimestampExpiredError


def get_timestamp() -> int:
    """
    获取当前时间戳（毫秒）

    返回 Unix 时间戳的毫秒表示，与 JavaScript 的 Date.now() 格式一致。

    Returns:
        int: 当前时间戳（毫秒）

    Example:
        >>> ts = get_timestamp()
        >>> isinstance(ts, int)
        True
        >>> ts > 0
        True
    """
    return int(time.time() * 1000)


def generate_body_md5(body: Optional[Dict[str, Any]]) -> str:
    """
    生成请求体的 MD5 哈希值

    对请求体进行 JSON 序列化（无空格），然后计算 MD5 值。
    如果请求体为空或 None，返回空字符串的 MD5。

    Args:
        body: 请求体字典，如果为 None 则视为空对象

    Returns:
        str: 32 位小写十六进制 MD5 字符串

    Raises:
        SignatureError: 当 body 无法序列化时抛出

    Example:
        >>> body = {"key": "value"}
        >>> md5 = generate_body_md5(body)
        >>> len(md5)
        32
    """
    try:
        # JSON 序列化必须无空格，使用 separators=(',', ':')
        body_json = json.dumps(body if body is not None else {}, separators=(",", ":"))
        body_md5 = hashlib.md5(body_json.encode("utf-8")).hexdigest()
        return body_md5
    except (TypeError, ValueError) as e:
        raise SignatureError(f"请求体序列化失败：{str(e)}", code="BODY_SERIALIZE_ERROR")


def generate_signature(
    app_key: str,
    app_secret: str,
    body: Optional[Dict[str, Any]] = None,
    timestamp: Optional[int] = None,
) -> str:
    """
    生成 API 请求签名

    签名算法严格按照闲管家文档要求：
    md5("appKey,bodyMd5,timestamp,appSecret")

    所有参数使用逗号连接（无空格），然后进行 MD5 计算。

    Args:
        app_key: 应用唯一标识（appKey）
        app_secret: 应用密钥（appSecret）
        body: 请求体字典，用于计算 bodyMd5
        timestamp: 时间戳（毫秒），如果为 None 则使用当前时间

    Returns:
        str: 32 位小写十六进制签名字符串

    Raises:
        SignatureError: 当 app_key 或 app_secret 为空时抛出

    Example:
        >>> signature = generate_signature(
        ...     app_key="my_app_key",
        ...     app_secret="my_app_secret",
        ...     body={"action": "query"}
        ... )
        >>> len(signature)
        32
    """
    # 验证必需参数
    if not app_key or not app_key.strip():
        raise SignatureError("app_key 不能为空", code="MISSING_APP_KEY")
    if not app_secret or not app_secret.strip():
        raise SignatureError("app_secret 不能为空", code="MISSING_APP_SECRET")

    # 获取时间戳（毫秒）
    if timestamp is None:
        timestamp = get_timestamp()

    # 计算请求体 MD5
    body_md5 = generate_body_md5(body)

    # 按照文档要求拼接：appKey,bodyMd5,timestamp,appSecret
    # 注意：使用逗号连接，无空格
    sign_string = f"{app_key},{body_md5},{timestamp},{app_secret}"

    # 计算 MD5 签名
    signature = hashlib.md5(sign_string.encode("utf-8")).hexdigest()

    return signature


def validate_timestamp(
    timestamp: int,
    current_time: Optional[int] = None,
    validity_ms: int = 300000,
) -> bool:
    """
    验证时间戳是否在有效期内

    检查请求时间戳与当前时间的差值是否在允许的时间窗口内。
    默认有效期为 5 分钟（300000 毫秒）。

    Args:
        timestamp: 请求时间戳（毫秒）
        current_time: 当前时间戳（毫秒），如果为 None 则使用当前时间
        validity_ms: 有效期（毫秒），默认 300000（5 分钟）

    Returns:
        bool: 如果时间戳有效返回 True，否则返回 False

    Raises:
        TimestampExpiredError: 当时间戳已过期时抛出（包含详细信息）

    Example:
        >>> current = get_timestamp()
        >>> validate_timestamp(current - 1000)  # 1 秒前
        True
        >>> validate_timestamp(current - 400000)  # 400 秒前，已过期
        Traceback (most recent call last):
            ...
        TimestampExpiredError: ...
    """
    if current_time is None:
        current_time = get_timestamp()

    # 计算时间差（毫秒）
    time_diff = abs(current_time - timestamp)

    # 检查是否超过有效期
    if time_diff > validity_ms:
        diff_seconds = time_diff / 1000
        raise TimestampExpiredError(
            message=f"时间戳已过期（相差 {diff_seconds:.1f} 秒，有效期 {validity_ms // 1000} 秒）",
            code="TIMESTAMP_EXPIRED",
            timestamp=timestamp,
            current_time=current_time,
        )

    return True


def generate_signed_params(
    app_key: str,
    app_secret: str,
    body: Optional[Dict[str, Any]] = None,
    timestamp: Optional[int] = None,
    include_body: bool = True,
) -> Dict[str, Any]:
    """
    生成包含签名信息的完整请求参数

    自动计算时间戳、bodyMd5 和 signature，返回可直接用于 API 请求的参数字典。

    Args:
        app_key: 应用唯一标识
        app_secret: 应用密钥
        body: 请求体字典
        timestamp: 时间戳（毫秒），如果为 None 则使用当前时间
        include_body: 是否在返回参数中包含 body 字段，默认 True

    Returns:
        Dict[str, Any]: 包含 appKey、timestamp、bodyMd5、signature 的字典
                       如果 include_body=True 且 body 不为空，还包含 body 字段

    Raises:
        SignatureError: 当签名生成失败时抛出

    Example:
        >>> params = generate_signed_params(
        ...     app_key="my_key",
        ...     app_secret="my_secret",
        ...     body={"action": "query"}
        ... )
        >>> "signature" in params
        True
        >>> "timestamp" in params
        True
        >>> "bodyMd5" in params
        True
    """
    # 获取时间戳
    if timestamp is None:
        timestamp = get_timestamp()

    # 计算 bodyMd5
    body_md5 = generate_body_md5(body)

    # 生成签名
    signature = generate_signature(
        app_key=app_key,
        app_secret=app_secret,
        body=body,
        timestamp=timestamp,
    )

    # 构建参数字典
    params: Dict[str, Any] = {
        "appKey": app_key,
        "timestamp": timestamp,
        "bodyMd5": body_md5,
        "signature": signature,
    }

    # 根据需要添加 body
    if include_body and body is not None:
        params["body"] = body

    return params


def verify_signature(
    signature: str,
    app_key: str,
    app_secret: str,
    body: Optional[Dict[str, Any]] = None,
    timestamp: Optional[int] = None,
) -> bool:
    """
    验证签名是否有效

    重新计算签名并与提供的签名进行比对，用于验证请求的完整性。
    注意：此函数主要用于调试或服务器端验证，客户端通常只需要生成签名。

    Args:
        signature: 待验证的签名字符串
        app_key: 应用唯一标识
        app_secret: 应用密钥
        body: 请求体字典
        timestamp: 时间戳（毫秒）

    Returns:
        bool: 如果签名有效返回 True，否则返回 False

    Raises:
        SignatureError: 当必需参数缺失时抛出
        TimestampExpiredError: 当时间戳已过期时抛出

    Example:
        >>> # 生成签名
        >>> sig = generate_signature("key", "secret", {"action": "test"})
        >>> # 验证签名
        >>> verify_signature(sig, "key", "secret", {"action": "test"})
        True
        >>> # 错误的签名
        >>> verify_signature("wrong_signature", "key", "secret")
        False
    """
    # 验证时间戳（如果提供）
    if timestamp is not None:
        validate_timestamp(timestamp)

    # 重新计算签名
    expected_signature = generate_signature(
        app_key=app_key,
        app_secret=app_secret,
        body=body,
        timestamp=timestamp,
    )

    # 比较签名（使用恒定时间比较防止时序攻击）
    return _safe_compare(signature, expected_signature)


def _safe_compare(a: str, b: str) -> bool:
    """
    安全地比较两个字符串是否相等

    使用恒定时间比较算法，防止时序攻击（timing attack）。

    Args:
        a: 第一个字符串
        b: 第二个字符串

    Returns:
        bool: 如果两个字符串相等返回 True，否则返回 False
    """
    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(a.encode("utf-8"), b.encode("utf-8")):
        result |= x ^ y

    return result == 0
