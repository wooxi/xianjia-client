# 闲管家 API 客户端

闲管家 API Python 异步客户端，提供完整的 API 交互能力。

## 特性

- ✅ 异步 HTTP 请求（asyncio + httpx）
- ✅ 自动签名生成（MD5 签名机制）
- ✅ 时间戳 5 分钟有效性校验
- ✅ 请求失败自动重试（指数退避）
- ✅ 完整的类型注解和文档字符串
- ✅ 自定义异常处理

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 基础用法

```python
import asyncio
from xianjia_client import XianjiaClient, Config

async def main():
    # 创建配置
    config = Config(
        app_key="your_app_key",
        app_secret="your_app_secret"
    )
    
    # 创建客户端并使用异步上下文管理器
    async with XianjiaClient(config) as client:
        # 发送 POST 请求
        result = await client.post(
            "/v1/orders",
            body={"action": "create", "order_id": "123"}
        )
        print(result)
        
        # 发送 GET 请求
        result = await client.get(
            "/v1/orders",
            params={"status": "pending"}
        )
        print(result)

asyncio.run(main())
```

### 从环境变量加载配置

```python
import asyncio
import os
from xianjia_client import XianjiaClient, Config

# 设置环境变量
os.environ["XIANJIA_APP_KEY"] = "your_app_key"
os.environ["XIANJIA_APP_SECRET"] = "your_app_secret"

async def main():
    # 从环境变量加载配置
    config = Config.from_env()
    
    async with XianjiaClient(config) as client:
        result = await client.get("/v1/products")
        print(result)

asyncio.run(main())
```

### 错误处理

```python
import asyncio
from xianjia_client import XianjiaClient, Config
from xianjia_client.exceptions import (
    XianjiaException,
    SignatureError,
    RequestError,
    ResponseError,
    TimestampExpiredError,
)

async def main():
    config = Config(app_key="key", app_secret="secret")
    
    async with XianjiaClient(config) as client:
        try:
            result = await client.post("/v1/orders", body={"action": "create"})
            print(result)
        except TimestampExpiredError as e:
            print(f"时间戳过期：{e}")
            # 重新生成请求
        except SignatureError as e:
            print(f"签名错误：{e}")
        except RequestError as e:
            print(f"请求错误：{e} (HTTP {e.status_code})")
        except ResponseError as e:
            print(f"响应错误：{e}")
            print(f"原始响应：{e.raw_response}")
        except XianjiaException as e:
            print(f"其他错误：{e}")

asyncio.run(main())
```

## 项目结构

```
xianjia_client/
├── __init__.py          # 包初始化，导出公共类
├── config.py            # 配置管理
├── client.py            # HTTP 客户端
├── exceptions.py        # 自定义异常
├── utils/
│   ├── __init__.py      # 工具模块初始化
│   └── signature.py     # 签名生成工具
├── requirements.txt     # 依赖列表
└── README.md            # 本文档
```

## API 参考

### Config

配置类，管理 API 访问参数。

```python
config = Config(
    app_key="your_app_key",      # 必需
    app_secret="your_app_secret", # 必需
    domain="https://api.xianjia.com",  # 可选，默认
    timeout=30,                   # 可选，默认 30 秒
    max_retries=3,                # 可选，默认 3 次
)
```

### XianjiaClient

异步 HTTP 客户端。

```python
# 创建客户端
client = XianjiaClient(config)

# 使用异步上下文管理器（推荐）
async with XianjiaClient(config) as client:
    # 自动管理会话生命周期
    pass

# 手动管理
await client.close()
```

#### 请求方法

- `request(method, endpoint, body, params, headers)` - 通用请求方法
- `get(endpoint, params, headers)` - GET 请求
- `post(endpoint, body, params, headers)` - POST 请求
- `put(endpoint, body, params, headers)` - PUT 请求
- `delete(endpoint, params, headers)` - DELETE 请求

### 签名机制

签名算法严格按照闲管家文档：

```
signature = md5("appKey,bodyMd5,timestamp,appSecret")
```

- `appKey`: 应用唯一标识
- `bodyMd5`: 请求体 JSON 序列化后的 MD5（无空格）
- `timestamp`: 当前时间戳（毫秒）
- `appSecret`: 应用密钥

**注意：**
- JSON 序列化使用 `separators=(',', ':')`（无空格）
- 时间戳有效期为 5 分钟（300000 毫秒）
- 所有参数使用逗号连接，无空格

## 异常类

- `XianjiaException` - 基础异常类
- `SignatureError` - 签名相关错误
- `RequestError` - HTTP 请求错误
- `ResponseError` - 响应解析错误
- `TimestampExpiredError` - 时间戳过期错误（SignatureError 子类）

## 日志

客户端使用 Python 标准 logging 模块，可以通过以下方式配置日志：

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("xianjia_client")
logger.setLevel(logging.DEBUG)
```

## 许可证

MIT License
