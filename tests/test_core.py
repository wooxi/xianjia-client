"""
闲管家 API 客户端核心模块测试

测试配置管理、签名生成、HTTP 客户端等核心功能。
"""

import asyncio
import json
import hashlib
import pytest
from typing import Dict, Any

from xianjia_client import Config, XianjiaClient
from xianjia_client.exceptions import (
    SignatureError,
    RequestError,
    ResponseError,
    TimestampExpiredError,
)
from xianjia_client.utils.signature import (
    get_timestamp,
    generate_body_md5,
    generate_signature,
    generate_signed_params,
    validate_timestamp,
    verify_signature,
)


class TestConfig:
    """Config 类测试"""

    def test_basic_config(self):
        """测试基础配置创建"""
        config = Config(app_key="test_key", app_secret="test_secret")
        assert config.app_key == "test_key"
        assert config.app_secret == "test_secret"
        assert config.domain == "https://api.xianjia.com"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.timestamp_validity == 300000

    def test_custom_config(self):
        """测试自定义配置"""
        config = Config(
            app_key="custom_key",
            app_secret="custom_secret",
            domain="https://custom.api.com",
            timeout=60,
            max_retries=5,
        )
        assert config.domain == "https://custom.api.com"
        assert config.timeout == 60
        assert config.max_retries == 5

    def test_invalid_app_key(self):
        """测试无效 app_key"""
        with pytest.raises(ValueError, match="app_key 不能为空"):
            Config(app_key="", app_secret="secret")

    def test_invalid_app_secret(self):
        """测试无效 app_secret"""
        with pytest.raises(ValueError, match="app_secret 不能为空"):
            Config(app_key="key", app_secret="")

    def test_from_dict(self):
        """测试从字典加载配置"""
        data = {
            "app_key": "dict_key",
            "app_secret": "dict_secret",
            "domain": "https://dict.api.com",
            "timeout": 45,
        }
        config = Config.from_dict(data)
        assert config.app_key == "dict_key"
        assert config.domain == "https://dict.api.com"
        assert config.timeout == 45

    def test_to_dict(self):
        """测试导出配置（不包含敏感信息）"""
        config = Config(app_key="export_key", app_secret="export_secret")
        exported = config.to_dict()
        assert exported["app_key"] == "export_key"
        assert "app_secret" not in exported
        assert exported["domain"] == "https://api.xianjia.com"

    def test_get_api_url(self):
        """测试 API URL 构建"""
        config = Config(app_key="key", app_secret="secret")
        url = config.get_api_url("/v1/orders")
        assert url == "https://api.xianjia.com/v1/orders"

        url2 = config.get_api_url("v1/products")
        assert url2 == "https://api.xianjia.com/v1/products"


class TestSignature:
    """签名工具测试"""

    def test_get_timestamp(self):
        """测试时间戳生成"""
        ts = get_timestamp()
        assert isinstance(ts, int)
        assert ts > 0
        # 检查是否为毫秒级时间戳
        assert ts > 1000000000000  # 大于 2001 年

    def test_generate_body_md5_empty(self):
        """测试空请求体 MD5"""
        md5 = generate_body_md5(None)
        assert len(md5) == 32
        assert md5 == hashlib.md5(b"{}").hexdigest()

    def test_generate_body_md5_simple(self):
        """测试简单请求体 MD5"""
        body = {"key": "value"}
        md5 = generate_body_md5(body)
        expected_json = json.dumps(body, separators=(",", ":"))
        expected_md5 = hashlib.md5(expected_json.encode("utf-8")).hexdigest()
        assert md5 == expected_md5
        assert len(md5) == 32

    def test_generate_body_md5_nested(self):
        """测试嵌套请求体 MD5"""
        body = {"order": {"id": "123", "items": ["a", "b"]}}
        md5 = generate_body_md5(body)
        expected_json = json.dumps(body, separators=(",", ":"))
        expected_md5 = hashlib.md5(expected_json.encode("utf-8")).hexdigest()
        assert md5 == expected_md5

    def test_generate_signature(self):
        """测试签名生成"""
        app_key = "test_key"
        app_secret = "test_secret"
        body = {"action": "query"}
        timestamp = 1234567890000

        signature = generate_signature(app_key, app_secret, body, timestamp)
        assert len(signature) == 32

        # 验证签名算法
        body_md5 = generate_body_md5(body)
        sign_string = f"{app_key},{body_md5},{timestamp},{app_secret}"
        expected_signature = hashlib.md5(sign_string.encode("utf-8")).hexdigest()
        assert signature == expected_signature

    def test_generate_signature_missing_key(self):
        """测试缺少 app_key"""
        with pytest.raises(SignatureError, match="app_key 不能为空"):
            generate_signature("", "secret", {})

    def test_generate_signature_missing_secret(self):
        """测试缺少 app_secret"""
        with pytest.raises(SignatureError, match="app_secret 不能为空"):
            generate_signature("key", "", {})

    def test_generate_signed_params(self):
        """测试生成完整签名参数"""
        params = generate_signed_params(
            app_key="key", app_secret="secret", body={"action": "test"}
        )
        assert "appKey" in params
        assert "timestamp" in params
        assert "bodyMd5" in params
        assert "signature" in params
        assert "body" in params
        assert params["appKey"] == "key"

    def test_validate_timestamp_valid(self):
        """测试有效时间戳"""
        current = get_timestamp()
        assert validate_timestamp(current - 1000)  # 1 秒前
        assert validate_timestamp(current - 200000)  # 200 秒前

    def test_validate_timestamp_expired(self):
        """测试过期时间戳"""
        current = get_timestamp()
        with pytest.raises(TimestampExpiredError):
            validate_timestamp(current - 400000)  # 400 秒前，超过 5 分钟

    def test_verify_signature_valid(self):
        """测试验证有效签名"""
        app_key = "key"
        app_secret = "secret"
        body = {"action": "test"}
        timestamp = get_timestamp()

        signature = generate_signature(app_key, app_secret, body, timestamp)
        assert verify_signature(signature, app_key, app_secret, body, timestamp)

    def test_verify_signature_invalid(self):
        """测试验证无效签名"""
        assert not verify_signature(
            "wrong_signature", "key", "secret", {"action": "test"}
        )


class TestClient:
    """HTTP 客户端测试"""

    @pytest.mark.asyncio
    async def test_client_creation(self):
        """测试客户端创建"""
        config = Config(app_key="key", app_secret="secret")
        client = XianjiaClient(config)
        assert client.config == config
        assert client._session is None

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """测试异步上下文管理器"""
        config = Config(app_key="key", app_secret="secret")
        async with XianjiaClient(config) as client:
            assert client._session is not None
        # 退出上下文后会话应已关闭
        assert client._session is None or client._session.is_closed

    @pytest.mark.asyncio
    async def test_client_methods(self):
        """测试客户端方法"""
        config = Config(app_key="key", app_secret="secret")
        client = XianjiaClient(config)

        assert hasattr(client, "request")
        assert hasattr(client, "get")
        assert hasattr(client, "post")
        assert hasattr(client, "put")
        assert hasattr(client, "delete")
        assert hasattr(client, "close")

    @pytest.mark.asyncio
    async def test_client_close(self):
        """测试手动关闭客户端"""
        config = Config(app_key="key", app_secret="secret")
        client = XianjiaClient(config)
        await client.close()


class TestIntegration:
    """集成测试"""

    def test_signature_flow(self):
        """测试完整签名流程"""
        app_key = "integration_key"
        app_secret = "integration_secret"
        body = {"order_id": "12345", "action": "create"}

        # 生成签名参数
        params = generate_signed_params(app_key, app_secret, body)

        # 验证参数完整性
        assert params["appKey"] == app_key
        assert params["body"] == body
        assert len(params["signature"]) == 32
        assert len(params["bodyMd5"]) == 32

        # 验证签名
        assert verify_signature(
            params["signature"],
            app_key,
            app_secret,
            body,
            params["timestamp"],
        )

    def test_json_serialization_format(self):
        """测试 JSON 序列化格式（无空格）"""
        body = {"key": "value", "nested": {"a": 1, "b": 2}}
        json_str = json.dumps(body, separators=(",", ":"))

        # 确保没有空格
        assert " " not in json_str
        assert ": " not in json_str
        assert ", " not in json_str

        # 验证格式正确
        assert json_str == '{"key":"value","nested":{"a":1,"b":2}}'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
