"""
闲管家 API 客户端使用示例

演示如何使用 XianjiaClient 进行 API 调用。
"""

import asyncio
import logging
from typing import Dict, Any

from xianjia_client import Config, XianjiaClient
from xianjia_client.exceptions import (
    XianjiaException,
    SignatureError,
    RequestError,
    ResponseError,
    TimestampExpiredError,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("xianjia_example")


async def example_basic_usage():
    """基础用法示例"""
    logger.info("=== 基础用法示例 ===")

    # 1. 创建配置
    config = Config(
        app_key="your_app_key",
        app_secret="your_app_secret",
        domain="https://api.xianjia.com",  # 可选，默认值
        timeout=30,  # 可选，默认 30 秒
        max_retries=3,  # 可选，默认 3 次
    )

    # 2. 创建客户端并使用异步上下文管理器（推荐）
    async with XianjiaClient(config) as client:
        # 3. 发送 POST 请求
        try:
            result = await client.post(
                "/v1/orders",
                body={"action": "create", "order_id": "12345"},
            )
            logger.info(f"创建订单成功：{result}")
        except XianjiaException as e:
            logger.error(f"请求失败：{e}")

        # 4. 发送 GET 请求
        try:
            result = await client.get(
                "/v1/orders",
                params={"status": "pending", "limit": 10},
            )
            logger.info(f"查询订单成功：{result}")
        except XianjiaException as e:
            logger.error(f"请求失败：{e}")


async def example_error_handling():
    """错误处理示例"""
    logger.info("=== 错误处理示例 ===")

    config = Config(app_key="your_app_key", app_secret="your_app_secret")

    async with XianjiaClient(config) as client:
        try:
            # 发送请求
            result = await client.post("/v1/orders", body={"action": "create"})
            logger.info(f"成功：{result}")

        except TimestampExpiredError as e:
            # 时间戳过期（超过 5 分钟）
            logger.error(f"时间戳过期：{e}")
            logger.error(f"过期时间差：{e.details.get('diff_seconds', 'N/A')}秒")
            # 可以重新生成请求

        except SignatureError as e:
            # 签名错误
            logger.error(f"签名错误：{e}")
            logger.error(f"错误代码：{e.code}")

        except RequestError as e:
            # HTTP 请求错误
            logger.error(f"请求错误：{e}")
            logger.error(f"HTTP 状态码：{e.status_code}")
            logger.error(f"响应内容：{e.response_body}")

        except ResponseError as e:
            # 响应解析错误或业务错误
            logger.error(f"响应错误：{e}")
            logger.error(f"错误代码：{e.code}")
            logger.error(f"原始响应：{e.raw_response}")

        except XianjiaException as e:
            # 其他闲管家相关错误
            logger.error(f"其他错误：{e}")
            logger.error(f"详细信息：{e.details}")


async def example_retry_mechanism():
    """重试机制示例"""
    logger.info("=== 重试机制示例 ===")

    # 配置重试参数
    config = Config(
        app_key="your_app_key",
        app_secret="your_app_secret",
        timeout=10,  # 较短的超时时间
        max_retries=3,  # 最多重试 3 次
    )

    async with XianjiaClient(config) as client:
        # 客户端会自动处理重试
        # 使用指数退避策略：1s, 2s, 4s, ...
        try:
            result = await client.post("/v1/orders", body={"action": "create"})
            logger.info(f"请求成功（可能经过重试）：{result}")
        except RequestError as e:
            logger.error(f"重试后仍然失败：{e}")


async def example_custom_headers():
    """自定义请求头示例"""
    logger.info("=== 自定义请求头示例 ===")

    config = Config(app_key="your_app_key", app_secret="your_app_secret")

    async with XianjiaClient(config) as client:
        # 添加自定义请求头
        custom_headers = {
            "X-Custom-Header": "custom_value",
            "X-Request-ID": "req_123456",
        }

        result = await client.post(
            "/v1/orders",
            body={"action": "create"},
            headers=custom_headers,
        )
        logger.info(f"使用自定义请求头：{result}")


async def example_environment_config():
    """环境变量配置示例"""
    logger.info("=== 环境变量配置示例 ===")

    import os

    # 设置环境变量（实际使用时在 shell 中设置）
    os.environ["XIANJIA_APP_KEY"] = "env_app_key"
    os.environ["XIANJIA_APP_SECRET"] = "env_app_secret"
    os.environ["XIANJIA_DOMAIN"] = "https://api.xianjia.com"
    os.environ["XIANJIA_TIMEOUT"] = "60"
    os.environ["XIANJIA_MAX_RETRIES"] = "5"

    # 从环境变量加载配置
    config = Config.from_env()
    logger.info(f"从环境变量加载配置：{config}")

    async with XianjiaClient(config) as client:
        logger.info("客户端已就绪")


async def example_manual_client_management():
    """手动管理客户端生命周期示例"""
    logger.info("=== 手动管理客户端示例 ===")

    config = Config(app_key="your_app_key", app_secret="your_app_secret")

    # 创建客户端（不使用上下文管理器）
    client = XianjiaClient(config)

    try:
        # 发送请求
        result = await client.get("/v1/products")
        logger.info(f"查询产品：{result}")

    finally:
        # 必须手动关闭客户端
        await client.close()
        logger.info("客户端已关闭")


async def example_signature_details():
    """签名机制详解示例"""
    logger.info("=== 签名机制详解 ===")

    from xianjia_client.utils.signature import (
        get_timestamp,
        generate_body_md5,
        generate_signature,
        generate_signed_params,
        validate_timestamp,
    )

    app_key = "demo_key"
    app_secret = "demo_secret"
    body = {"action": "query", "order_id": "123"}

    # 1. 获取时间戳（毫秒）
    timestamp = get_timestamp()
    logger.info(f"时间戳：{timestamp}")

    # 2. 计算请求体 MD5（JSON 序列化无空格）
    body_md5 = generate_body_md5(body)
    logger.info(f"请求体 MD5: {body_md5}")

    # 3. 生成签名：md5("appKey,bodyMd5,timestamp,appSecret")
    signature = generate_signature(app_key, app_secret, body, timestamp)
    logger.info(f"签名：{signature}")

    # 4. 验证时间戳有效性（5 分钟内）
    try:
        validate_timestamp(timestamp)
        logger.info("时间戳有效")
    except Exception as e:
        logger.error(f"时间戳无效：{e}")

    # 5. 生成完整的签名参数
    params = generate_signed_params(app_key, app_secret, body)
    logger.info(f"签名参数：appKey={params['appKey']}, timestamp={params['timestamp']}")
    logger.info(f"签名参数：bodyMd5={params['bodyMd5']}, signature={params['signature']}")


async def main():
    """运行所有示例"""
    logger.info("闲管家 API 客户端使用示例\n")

    # 运行示例（注释掉不需要的示例）
    # await example_basic_usage()
    # await example_error_handling()
    # await example_retry_mechanism()
    # await example_custom_headers()
    # await example_environment_config()
    # await example_manual_client_management()
    await example_signature_details()

    logger.info("\n示例运行完成")


if __name__ == "__main__":
    asyncio.run(main())
