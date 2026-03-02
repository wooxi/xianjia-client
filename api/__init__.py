"""
API 接口模块

提供闲管家 API 接口封装。
"""

from .product import (
    get_product_detail,
    list_products,
    list_products_all,
    search_products
)
from .user import (
    get_authorized_shops,
    get_shop_detail,
    APIError,
    TokenExpiredError,
    PermissionDeniedError,
    ResourceNotFoundError
)

__all__ = [
    "get_product_detail",
    "list_products",
    "list_products_all",
    "search_products",
    "get_authorized_shops",
    "get_shop_detail",
    "APIError",
    "TokenExpiredError",
    "PermissionDeniedError",
    "ResourceNotFoundError",
]
