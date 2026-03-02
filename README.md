# Xianjia Client - 闲管家 API Python SDK

[![GitHub](https://img.shields.io/github/license/wooxi/xianjia-client)](https://github.com/wooxi/xianjia-client)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

闲管家 API Python SDK，提供完整的店铺管理、商品查询等功能。

## ✨ 特性

- ✅ 异步 HTTP 请求（asyncio + httpx）
- ✅ 自动签名生成（MD5 签名机制）
- ✅ Pydantic 2.x 数据模型，类型安全
- ✅ 请求失败自动重试（指数退避）
- ✅ 完整的错误处理
- ✅ 详细的中文文档和注释

## 📦 安装

```bash
cd xianjia_client
pip install -r requirements.txt
```

## 🚀 快速开始

### 1. 配置凭证

编辑 `config.py` 或设置环境变量：

```python
# config.py
APP_KEY = "你的 appKey"
APP_SECRET = "你的 appSecret"
```

或使用环境变量：
```bash
export XIANJIA_APP_KEY="your_app_key"
export XIANJIA_APP_SECRET="your_app_secret"
```

### 2. 查询店铺列表

```python
import asyncio
from xianjia_client import XianjiaClient

async def main():
    client = XianjiaClient(
        app_key="your_app_key",
        app_secret="your_app_secret"
    )
    
    # 获取已授权店铺
    shops = await client.user.get_authorized_shops()
    
    for shop in shops:
        print(f"🏪 {shop.shop_name}")
        print(f"   会员名：{shop.user_name}")
        print(f"   鱼小铺：{'是' if shop.is_pro else '否'}")
        print(f"   状态：{'有效' if shop.is_valid else '无效'}")
        print()

asyncio.run(main())
```

### 3. 查询商品列表

```python
import asyncio
from xianjia_client import XianjiaClient

async def main():
    client = XianjiaClient(
        app_key="your_app_key",
        app_secret="your_app_secret"
    )
    
    # 获取商品列表（分页）
    result = await client.product.list_products(page_no=1, page_size=10)
    
    print(f"共 {result.total} 个商品，第 {result.page_no}/{result.total_pages} 页\n")
    
    for p in result.list:
        status_map = {
            'onsale': '销售中', 'offline': '已下架',
            'recycled': '回收站', 'all': '全部'
        }
        status = status_map.get(p.publish_status, p.publish_status)
        print(f"📦 {p.title}")
        print(f"   价格：¥{p.price/100:.2f}")
        print(f"   库存：{p.stock}")
        print(f"   销量：{p.sold_count}")
        print(f"   状态：{status}")
        print()

asyncio.run(main())
```

### 4. 查询商品详情

```python
import asyncio
from xianjia_client import XianjiaClient

async def main():
    client = XianjiaClient(
        app_key="your_app_key",
        app_secret="your_app_secret"
    )
    
    # 获取商品详情
    detail = await client.product.get_product_detail(product_id=123456)
    
    print(f"商品：{detail.title}")
    print(f"价格：¥{detail.price/100:.2f}")
    print(f"库存：{detail.stock}")
    print(f"描述：{detail.desc[:50]}...")
    
    if detail.images:
        print(f"图片：{len(detail.images)} 张")

asyncio.run(main())
```

### 5. 使用示例脚本

```bash
# 运行完整测试
python example.py

# 运行店铺测试
python tests/test_shop_simple.py
```

## 📁 项目结构

```
xianjia_client/
├── config.py              # 配置管理
├── client.py              # HTTP 客户端
├── exceptions.py          # 自定义异常
├── api/
│   ├── user.py            # 店铺接口 ✅
│   └── product.py         # 商品接口 ✅
├── models/
│   ├── shop.py            # 店铺模型
│   └── product.py         # 商品模型
├── utils/
│   └── signature.py       # MD5 签名工具
├── tests/                 # 单元测试
├── example.py             # 使用示例
├── requirements.txt       # 依赖列表
└── README.md              # 本文档
```

## 📚 API 文档

### 店铺管理 (`client.user`)

| 方法 | 说明 |
|------|------|
| `get_authorized_shops()` | 查询已授权店铺列表 |

### 商品管理 (`client.product`)

| 方法 | 说明 |
|------|------|
| `get_product_detail(product_id)` | 查询商品详情 |
| `list_products(page_no, page_size, ...)` | 查询商品列表（分页） |
| `list_products_all()` | 获取全部商品（自动分页） |
| `search_products(keyword)` | 关键词搜索商品 |

### 数据模型

#### ShopInfo - 店铺信息
```python
- authorize_id: int          # 授权 ID
- user_identity: str         # 闲鱼会员唯一标识
- user_name: str             # 闲鱼会员名
- user_nick: str             # 昵称
- shop_name: str             # 店铺名称
- is_pro: bool               # 是否鱼小铺
- is_valid: bool             # 是否有效
- is_deposit_enough: bool    # 保证金是否缴足
- valid_end_time: int        # 有效期截止时间戳
```

#### ProductDetail - 商品详情
```python
- product_id: int            # 商品 ID
- title: str                 # 标题
- price: int                 # 价格（分）
- stock: int                 # 库存
- sold_count: int            # 销量
- publish_status: str        # 状态
- desc: str                  # 描述
- images: List[str]          # 图片 URL
```

## 🔧 开发

### 运行测试

```bash
# 全部测试
python -m pytest tests/ -v

# 单个模块
python tests/test_shop_simple.py
python tests/test_product.py
```

### 代码规范

- 使用类型注解
- 添加中文 docstring
- 遵循 PEP 8

## 📝 更新日志

### v0.1.0 (2026-03-02)
- ✅ 基础客户端框架
- ✅ 店铺查询接口
- ✅ 商品查询接口（详情 + 列表）
- ✅ Pydantic 数据模型
- ✅ 单元测试

### 🚧 计划中
- 商品创建（单个/批量）
- 商品上架/下架
- 商品编辑/删除
- 订单管理
- 消息回调处理

## 📄 许可证

MIT License

## 🔗 链接

- GitHub: https://github.com/wooxi/xianjia-client
- 闲管家文档：https://my.feishu.cn/wiki/XXbkwUkKMilg1UkoXuJc9mhInwc
