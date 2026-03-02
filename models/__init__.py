"""
数据模型模块

提供闲管家 API 相关的数据模型定义。
"""

from .product import (
    ProductDetail,
    ProductList,
    ProductListItem,
    ProductPublishStatus
)
from .shop import ShopInfo

__all__ = [
    "ProductDetail",
    "ProductList",
    "ProductListItem",
    "ProductPublishStatus",
    "ShopInfo",
]
