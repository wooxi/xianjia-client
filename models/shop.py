"""
闲管家店铺数据模型模块

定义店铺相关的 Pydantic 数据模型，用于 API 请求和响应的数据验证。
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ShopInfo(BaseModel):
    """
    店铺信息数据模型
    
    用于表示闲管家系统中已授权店铺的完整信息。
    包含店铺基本信息、授权状态、服务支持等字段。
    
    Attributes:
        authorize_id: 授权 ID，唯一标识一次授权关系
        user_identity: 用户身份标识
        user_name: 用户真实姓名
        user_nick: 用户昵称
        shop_name: 店铺名称
        
        is_pro: 是否为专业版店铺
        is_deposit_enough: 保证金是否充足
        is_valid: 授权是否有效
        is_trial: 是否为试用店铺
        
        valid_end_time: 授权有效期结束时间
        service_support: 支持的服务类型列表
        item_biz_types: 商品业务类型列表
    """
    
    # 基础身份信息
    authorize_id: str = Field(
        ...,
        description="授权 ID，唯一标识一次授权关系",
        min_length=1
    )
    user_identity: str = Field(
        ...,
        description="用户身份标识",
        min_length=1
    )
    user_name: str = Field(
        ...,
        description="用户真实姓名",
        min_length=1
    )
    user_nick: str = Field(
        ...,
        description="用户昵称",
        min_length=1
    )
    shop_name: str = Field(
        ...,
        description="店铺名称",
        min_length=1
    )
    
    # 状态标识字段
    is_pro: bool = Field(
        default=False,
        description="是否为专业版店铺"
    )
    is_deposit_enough: bool = Field(
        default=False,
        description="保证金是否充足"
    )
    is_valid: bool = Field(
        default=False,
        description="授权是否有效"
    )
    is_trial: bool = Field(
        default=False,
        description="是否为试用店铺"
    )
    
    # 时间和服务信息
    valid_end_time: Optional[datetime] = Field(
        default=None,
        description="授权有效期结束时间"
    )
    service_support: List[str] = Field(
        default_factory=list,
        description="支持的服务类型列表"
    )
    item_biz_types: List[str] = Field(
        default_factory=list,
        description="商品业务类型列表"
    )
    
    class Config:
        """Pydantic 模型配置"""
        # 允许从字典属性创建模型实例
        from_attributes = True
        # JSON Schema 配置
        json_schema_extra = {
            "example": {
                "authorize_id": "auth_123456",
                "user_identity": "user_789",
                "user_name": "张三",
                "user_nick": "小张",
                "shop_name": "张三的店铺",
                "is_pro": True,
                "is_deposit_enough": True,
                "is_valid": True,
                "is_trial": False,
                "valid_end_time": "2026-12-31T23:59:59",
                "service_support": ["item_manage", "order_process"],
                "item_biz_types": ["retail", "wholesale"]
            }
        }
    
    def is_expired(self) -> bool:
        """
        检查授权是否已过期
        
        Returns:
            bool: 如果已过期返回 True，否则返回 False
        """
        if self.valid_end_time is None:
            return False
        return datetime.now() > self.valid_end_time
    
    def get_remaining_days(self) -> Optional[int]:
        """
        获取授权剩余天数
        
        Returns:
            Optional[int]: 剩余天数，如果无有效期则返回 None
        """
        if self.valid_end_time is None:
            return None
        delta = self.valid_end_time - datetime.now()
        return max(0, delta.days)
