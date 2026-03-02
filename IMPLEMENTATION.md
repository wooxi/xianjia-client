# 闲管家 API 客户端实现总结

## 项目结构

```
xianjia_client/
├── __init__.py              # 包初始化，导出公共类
├── config.py                # 配置管理（Config 类）
├── client.py                # HTTP 客户端（XianjiaClient 类）
├── exceptions.py            # 自定义异常类
├── utils/
│   ├── __init__.py          # 工具模块初始化
│   └── signature.py         # 签名生成工具
├── tests/
│   ├── __init__.py
│   └── test_core.py         # 核心模块测试
├── example.py               # 使用示例
├── requirements.txt         # 依赖列表
├── README.md                # 使用文档
└── IMPLEMENTATION.md        # 本文档
```

## 实现的功能

### 1. 配置管理 (config.py)

**Config 类** 提供以下功能：
- 必需参数：`app_key`, `app_secret`
- 可选参数：`domain`, `timeout`, `max_retries`
- 自动验证参数有效性
- 支持从环境变量加载：`Config.from_env()`
- 支持从字典加载：`Config.from_dict()`
- 安全导出配置（隐藏敏感信息）：`config.to_dict()`
- 构建 API URL：`config.get_api_url(endpoint)`

### 2. 签名生成工具 (utils/signature.py)

**核心函数**：
- `get_timestamp()` - 获取当前时间戳（毫秒）
- `generate_body_md5(body)` - 生成请求体 MD5（JSON 无空格序列化）
- `generate_signature(app_key, app_secret, body, timestamp)` - 生成 API 签名
- `generate_signed_params(...)` - 生成完整签名参数
- `validate_timestamp(timestamp, validity_ms)` - 验证时间戳有效性
- `verify_signature(...)` - 验证签名是否有效

**签名算法**：
```
signature = md5("appKey,bodyMd5,timestamp,appSecret")
```

**关键要求**：
- JSON 序列化使用 `separators=(',', ':')`（无空格）
- 时间戳单位为毫秒
- 时间戳有效期默认 5 分钟（300000ms）
- 所有参数用逗号连接，无空格

### 3. HTTP 客户端 (client.py)

**XianjiaClient 类** 提供以下功能：
- 异步 HTTP 请求（asyncio + httpx）
- 自动签名生成和附加
- 时间戳有效性校验
- 请求失败自动重试（指数退避策略）
- 响应解析和错误处理
- 异步上下文管理器支持
- 手动关闭支持

**请求方法**：
- `request(method, endpoint, body, params, headers)` - 通用请求
- `get(endpoint, params, headers)` - GET 请求
- `post(endpoint, body, params, headers)` - POST 请求
- `put(endpoint, body, params, headers)` - PUT 请求
- `delete(endpoint, params, headers)` - DELETE 请求

**重试机制**：
- 网络错误自动重试
- 超时自动重试
- 5xx 服务器错误自动重试
- 指数退避：1s, 2s, 4s, ...（最大 10s）
- 可配置最大重试次数

### 4. 自定义异常 (exceptions.py)

**异常层次结构**：
```
XianjiaException (基础异常)
├── SignatureError (签名错误)
│   └── TimestampExpiredError (时间戳过期)
├── RequestError (HTTP 请求错误)
└── ResponseError (响应解析错误)
```

**异常属性**：
- `message` - 错误描述
- `code` - 错误代码
- `details` - 额外详情
- `status_code` - HTTP 状态码（RequestError）
- `response_body` - 响应体（RequestError）
- `raw_response` - 原始响应（ResponseError）
- `timestamp`, `current_time` - 时间戳信息（TimestampExpiredError）

## 使用示例

### 基础用法

```python
import asyncio
from xianjia_client import Config, XianjiaClient

async def main():
    config = Config(app_key="key", app_secret="secret")
    
    async with XianjiaClient(config) as client:
        result = await client.post(
            "/v1/orders",
            body={"action": "create", "order_id": "123"}
        )
        print(result)

asyncio.run(main())
```

### 错误处理

```python
from xianjia_client.exceptions import (
    TimestampExpiredError,
    SignatureError,
    RequestError,
    ResponseError,
)

async with XianjiaClient(config) as client:
    try:
        result = await client.post("/v1/orders", body={...})
    except TimestampExpiredError as e:
        print(f"时间戳过期：{e}")
    except SignatureError as e:
        print(f"签名错误：{e}")
    except RequestError as e:
        print(f"请求错误：{e} (HTTP {e.status_code})")
    except ResponseError as e:
        print(f"响应错误：{e}")
```

### 从环境变量加载配置

```bash
export XIANJIA_APP_KEY="your_key"
export XIANJIA_APP_SECRET="your_secret"
export XIANJIA_DOMAIN="https://api.xianjia.com"
```

```python
config = Config.from_env()
```

## 测试

运行测试：
```bash
cd /root/.openclaw/workspace
python3 -c "
from xianjia_client.tests.test_core import *
import asyncio

print('Running tests...')
test_config()
test_signature()
asyncio.run(test_client())
test_integration()
print('All tests passed!')
"
```

运行示例：
```bash
cd /root/.openclaw/workspace
PYTHONPATH=/root/.openclaw/workspace python3 xianjia_client/example.py
```

## 依赖

- Python 3.8+
- httpx >= 0.25.0
- typing_extensions >= 4.0.0 (Python < 3.11)

安装依赖：
```bash
pip install -r requirements.txt
```

## 设计特点

1. **类型安全**：所有函数和方法都有完整的类型注解
2. **文档完整**：所有公共 API 都有详细的 docstring
3. **异步优先**：使用 asyncio + httpx 实现高性能异步请求
4. **错误处理**：细粒度的异常分类，便于精确处理
5. **配置灵活**：支持多种配置加载方式
6. **安全性**：敏感信息脱敏，签名验证防时序攻击
7. **可测试性**：模块化设计，便于单元测试

## 注意事项

1. **时间戳有效期**：请求时间戳必须在 5 分钟内，否则会抛出 `TimestampExpiredError`
2. **JSON 序列化**：必须使用 `separators=(',', ':')` 确保无空格
3. **签名参数顺序**：严格按照 `appKey,bodyMd5,timestamp,appSecret` 顺序
4. **异步上下文管理器**：推荐使用 `async with` 自动管理会话生命周期
5. **重试机制**：网络错误和 5xx 错误会自动重试，4xx 错误不会重试
