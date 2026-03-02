"""
商品数据模型

提供闲管家商品相关的 Pydantic 数据模型，用于 API 请求和响应的数据验证与序列化。
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ProductPublishStatus(str, Enum):
    """商品发布状态枚举"""
    ONSALE = "onsale"  # 出售中
    OFFLINE = "offline"  # 已下架
    RECYCLED = "recycled"  # 回收站
    ALL = "all"  # 全部状态


class ProductDetail(BaseModel):
    """
    商品详情数据模型
    
    表示单个商品的完整信息，用于 API 响应和内部数据处理。
    
    Attributes:
        product_id: 商品唯一标识符
        title: 商品标题
        price: 商品价格（单位：元）
        stock: 商品库存数量
        publish_status: 商品发布状态
        description: 商品描述
        category_id: 分类 ID
        category_name: 分类名称
        images: 商品图片 URL 列表
        sales: 销量
        view_count: 浏览量
        favorite_count: 收藏量
        shop_id: 所属店铺 ID
        shop_name: 店铺名称
        create_time: 创建时间
        update_time: 更新时间
        publish_time: 上架时间
        delist_time: 下架时间
        is_new: 是否为新品
        delivery_method: 配送方式
        location: 商品所在地
    """
    product_id: str = Field(..., description="商品唯一标识符", min_length=1)
    title: str = Field(..., description="商品标题", min_length=1, max_length=500)
    price: float = Field(..., description="商品价格（单位：元）", ge=0)
    stock: int = Field(default=1, description="商品库存数量", ge=0)
    publish_status: ProductPublishStatus = Field(
        default=ProductPublishStatus.OFFLINE,
        description="商品发布状态"
    )
    description: Optional[str] = Field(default=None, description="商品描述")
    category_id: Optional[str] = Field(default=None, description="分类 ID")
    category_name: Optional[str] = Field(default=None, description="分类名称")
    images: List[str] = Field(default_factory=list, description="商品图片 URL 列表")
    sales: int = Field(default=0, description="销量", ge=0)
    view_count: int = Field(default=0, description="浏览量", ge=0)
    favorite_count: int = Field(default=0, description="收藏量", ge=0)
    shop_id: Optional[str] = Field(default=None, description="所属店铺 ID")
    shop_name: Optional[str] = Field(default=None, description="店铺名称")
    create_time: Optional[datetime] = Field(default=None, description="创建时间")
    update_time: Optional[datetime] = Field(default=None, description="更新时间")
    publish_time: Optional[datetime] = Field(default=None, description="上架时间")
    delist_time: Optional[datetime] = Field(default=None, description="下架时间")
    is_new: bool = Field(default=False, description="是否为新品")
    delivery_method: Optional[str] = Field(default=None, description="配送方式")
    location: Optional[str] = Field(default=None, description="商品所在地")
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = True  # 枚举值自动转换为字符串
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @classmethod
    def from_api_response(cls, data: dict) -> "ProductDetail":
        """
        从 API 响应数据创建商品详情实例
        
        Args:
            data: API 返回的商品数据字典
        
        Returns:
            ProductDetail: 商品详情实例
        """
        # 处理时间字段转换
        def parse_time(time_value):
            if time_value is None:
                return None
            if isinstance(time_value, datetime):
                return time_value
            if isinstance(time_value, (int, float)):
                # 毫秒时间戳
                return datetime.fromtimestamp(time_value / 1000)
            if isinstance(time_value, str):
                try:
                    return datetime.fromisoformat(time_value.replace('Z', '+00:00'))
                except ValueError:
                    return None
            return None
        
        # 处理图片列表
        images = data.get("images", [])
        if isinstance(images, str):
            # 如果图片是逗号分隔的字符串，转换为列表
            images = [img.strip() for img in images.split(",") if img.strip()]
        
        return cls(
            product_id=data.get("product_id", ""),
            title=data.get("title", ""),
            price=float(data.get("price", 0)),
            stock=int(data.get("stock", 1)),
            publish_status=data.get("publish_status", "offline"),
            description=data.get("description"),
            category_id=data.get("category_id"),
            category_name=data.get("category_name"),
            images=images,
            sales=int(data.get("sales", 0)),
            view_count=int(data.get("view_count", 0)),
            favorite_count=int(data.get("favorite_count", 0)),
            shop_id=data.get("shop_id"),
            shop_name=data.get("shop_name"),
            create_time=parse_time(data.get("create_time")),
            update_time=parse_time(data.get("update_time")),
            publish_time=parse_time(data.get("publish_time")),
            delist_time=parse_time(data.get("delist_time")),
            is_new=bool(data.get("is_new", False)),
            delivery_method=data.get("delivery_method"),
            location=data.get("location")
        )
    
    def to_dict(self) -> dict:
        """
        将商品详情转换为字典
        
        Returns:
            dict: 商品数据字典
        """
        return self.model_dump(mode="json")


class ProductListItem(BaseModel):
    """
    商品列表项数据模型
    
    用于商品列表响应中的单个商品项，包含精简的商品信息。
    
    Attributes:
        product_id: 商品唯一标识符
        title: 商品标题
        price: 商品价格
        stock: 商品库存
        publish_status: 商品发布状态
        sales: 销量
        main_image: 商品主图 URL
        category_name: 分类名称
        shop_name: 店铺名称
        update_time: 更新时间
    """
    product_id: str = Field(..., description="商品唯一标识符", min_length=1)
    title: str = Field(..., description="商品标题", min_length=1, max_length=500)
    price: float = Field(..., description="商品价格", ge=0)
    stock: int = Field(default=0, description="商品库存", ge=0)
    publish_status: ProductPublishStatus = Field(
        ...,
        description="商品发布状态"
    )
    sales: int = Field(default=0, description="销量", ge=0)
    main_image: Optional[str] = Field(default=None, description="商品主图 URL")
    category_name: Optional[str] = Field(default=None, description="分类名称")
    shop_name: Optional[str] = Field(default=None, description="店铺名称")
    update_time: Optional[datetime] = Field(default=None, description="更新时间")
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @classmethod
    def from_api_response(cls, data: dict) -> "ProductListItem":
        """
        从 API 响应数据创建列表项实例
        
        Args:
            data: API 返回的商品列表项数据字典
        
        Returns:
            ProductListItem: 商品列表项实例
        """
        def parse_time(time_value):
            if time_value is None:
                return None
            if isinstance(time_value, datetime):
                return time_value
            if isinstance(time_value, (int, float)):
                return datetime.fromtimestamp(time_value / 1000)
            if isinstance(time_value, str):
                try:
                    return datetime.fromisoformat(time_value.replace('Z', '+00:00'))
                except ValueError:
                    return None
            return None
        
        # 获取主图（第一张图片）
        images = data.get("images", [])
        main_image = images[0] if isinstance(images, list) and images else None
        if isinstance(images, str) and images:
            main_image = images.split(",")[0].strip()
        
        return cls(
            product_id=data.get("product_id", ""),
            title=data.get("title", ""),
            price=float(data.get("price", 0)),
            stock=int(data.get("stock", 0)),
            publish_status=data.get("publish_status", "offline"),
            sales=int(data.get("sales", 0)),
            main_image=main_image,
            category_name=data.get("category_name"),
            shop_name=data.get("shop_name"),
            update_time=parse_time(data.get("update_time"))
        )
    
    def to_dict(self) -> dict:
        """
        将列表项转换为字典
        
        Returns:
            dict: 列表项数据字典
        """
        return self.model_dump(mode="json")


class ProductList(BaseModel):
    """
    商品列表响应数据模型
    
    用于分页查询商品列表的 API 响应。
    
    Attributes:
        total: 商品总数
        page_no: 当前页码
        page_size: 每页数量
        total_pages: 总页数
        list: 商品列表项
    """
    total: int = Field(..., description="商品总数", ge=0)
    page_no: int = Field(..., description="当前页码", ge=1)
    page_size: int = Field(..., description="每页数量", ge=1, le=500)
    total_pages: int = Field(..., description="总页数", ge=0)
    list: List[ProductListItem] = Field(default_factory=list, description="商品列表项")
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = True
    
    @classmethod
    def from_api_response(cls, data: dict, page_no: int = 1, page_size: int = 20) -> "ProductList":
        """
        从 API 响应数据创建商品列表实例
        
        Args:
            data: API 返回的商品列表数据字典，应包含 total 和 list 字段
            page_no: 当前页码
            page_size: 每页数量
        
        Returns:
            ProductList: 商品列表实例
        """
        total = data.get("total", 0)
        items_data = data.get("list", [])
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        # 转换列表项
        items = [ProductListItem.from_api_response(item) for item in items_data]
        
        return cls(
            total=total,
            page_no=page_no,
            page_size=page_size,
            total_pages=total_pages,
            list=items
        )
    
    def to_dict(self) -> dict:
        """
        将商品列表转换为字典
        
        Returns:
            dict: 商品列表数据字典
        """
        return self.model_dump(mode="json")
    
    @property
    def has_next_page(self) -> bool:
        """
        判断是否有下一页
        
        Returns:
            bool: 是否有下一页
        """
        return self.page_no < self.total_pages
    
    @property
    def has_prev_page(self) -> bool:
        """
        判断是否有上一页
        
        Returns:
            bool: 是否有上一页
        """
        return self.page_no > 1
