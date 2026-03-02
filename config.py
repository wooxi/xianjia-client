"""
闲管家 API 配置管理模块

提供配置类的定义和管理，包括 appKey、appSecret、domain 等核心参数。
支持从环境变量、配置文件或直接传入参数进行初始化。
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Config:
    """
    闲管家 API 配置类

    封装 API 访问所需的所有配置参数，提供默认值和验证逻辑。

    Attributes:
        app_key: 应用唯一标识，由闲管家平台分配
        app_secret: 应用密钥，用于生成请求签名，必须保密
        domain: API 服务域名，默认为官方域名
        timeout: HTTP 请求超时时间（秒），默认 30 秒
        max_retries: 请求失败时的最大重试次数，默认 3 次
        timestamp_validity: 时间戳有效期（毫秒），默认 5 分钟（300000ms）

    Example:
        >>> config = Config(
        ...     app_key="your_app_key",
        ...     app_secret="your_app_secret"
        ... )
        >>> print(config.domain)
        'https://api.xianjia.com'
    """

    app_key: str
    app_secret: str
    domain: str = "https://api.xianjia.com"
    timeout: int = 30
    max_retries: int = 3
    timestamp_validity: int = field(default=300000, init=False)  # 5 分钟，不可变

    def __post_init__(self) -> None:
        """
        初始化后验证配置有效性

        Raises:
            ValueError: 当必需参数（app_key 或 app_secret）为空时抛出
        """
        if not self.app_key or not self.app_key.strip():
            raise ValueError("app_key 不能为空")
        if not self.app_secret or not self.app_secret.strip():
            raise ValueError("app_secret 不能为空")
        if not self.domain or not self.domain.strip():
            raise ValueError("domain 不能为空")
        if self.timeout <= 0:
            raise ValueError("timeout 必须大于 0")
        if self.max_retries < 0:
            raise ValueError("max_retries 不能小于 0")

    @classmethod
    def from_env(cls, prefix: str = "XIANJIA") -> "Config":
        """
        从环境变量加载配置

        按照 {PREFIX}_APP_KEY, {PREFIX}_APP_SECRET, {PREFIX}_DOMAIN 等
        格式读取环境变量。如果必需的环境变量不存在，将抛出异常。

        Args:
            prefix: 环境变量前缀，默认为 "XIANJIA"

        Returns:
            Config: 配置实例

        Raises:
            ValueError: 当必需的环境变量不存在时抛出

        Example:
            >>> # 设置环境变量后调用
            >>> os.environ["XIANJIA_APP_KEY"] = "my_key"
            >>> os.environ["XIANJIA_APP_SECRET"] = "my_secret"
            >>> config = Config.from_env()
        """
        app_key = os.getenv(f"{prefix}_APP_KEY", "")
        app_secret = os.getenv(f"{prefix}_APP_SECRET", "")
        domain = os.getenv(f"{prefix}_DOMAIN", "https://api.xianjia.com")
        timeout = int(os.getenv(f"{prefix}_TIMEOUT", "30"))
        max_retries = int(os.getenv(f"{prefix}_MAX_RETRIES", "3"))

        return cls(
            app_key=app_key,
            app_secret=app_secret,
            domain=domain,
            timeout=timeout,
            max_retries=max_retries,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """
        从字典加载配置

        允许从配置文件（如 JSON、YAML）解析后的字典创建配置实例。
        字典键名支持驼峰和下划线两种命名风格。

        Args:
            data: 包含配置参数的字典

        Returns:
            Config: 配置实例

        Example:
            >>> config_data = {
            ...     "app_key": "my_key",
            ...     "app_secret": "my_secret",
            ...     "domain": "https://api.xianjia.com"
            ... }
            >>> config = Config.from_dict(config_data)
        """
        return cls(
            app_key=data.get("app_key") or data.get("appKey", ""),
            app_secret=data.get("app_secret") or data.get("appSecret", ""),
            domain=data.get("domain", "https://api.xianjia.com"),
            timeout=int(data.get("timeout", 30)),
            max_retries=int(data.get("max_retries", 3)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        将配置转换为字典（不包含敏感信息）

        返回的配置字典可用于日志记录或配置导出，但会隐藏 app_secret。

        Returns:
            Dict[str, Any]: 配置字典（app_secret 已脱敏）

        Example:
            >>> config.to_dict()
            {
                'app_key': 'my_key',
                'domain': 'https://api.xianjia.com',
                'timeout': 30,
                'max_retries': 3
            }
        """
        return {
            "app_key": self.app_key,
            "domain": self.domain,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }

    def get_api_url(self, endpoint: str) -> str:
        """
        构建完整的 API 请求 URL

        自动处理域名和端点之间的斜杠，确保 URL 格式正确。

        Args:
            endpoint: API 端点路径（如 "/v1/orders" 或 "v1/orders"）

        Returns:
            str: 完整的 API URL

        Example:
            >>> config = Config(app_key="key", app_secret="secret")
            >>> config.get_api_url("/v1/orders")
            'https://api.xianjia.com/v1/orders'
            >>> config.get_api_url("v1/orders")
            'https://api.xianjia.com/v1/orders'
        """
        domain = self.domain.rstrip("/")
        endpoint = endpoint.lstrip("/")
        return f"{domain}/{endpoint}"

    @property
    def timestamp_validity_seconds(self) -> int:
        """
        时间戳有效期（秒）

        返回时间戳有效期的秒数表示，便于日志记录或显示。

        Returns:
            int: 有效期秒数（默认 300 秒，即 5 分钟）
        """
        return self.timestamp_validity // 1000

    def __str__(self) -> str:
        """返回配置的可读字符串表示（敏感信息已脱敏）"""
        secret_masked = (
            self.app_secret[:3] + "****" + self.app_secret[-2:]
            if len(self.app_secret) > 5
            else "****"
        )
        return (
            f"Config(app_key={self.app_key}, app_secret={secret_masked}, "
            f"domain={self.domain}, timeout={self.timeout}s)"
        )
