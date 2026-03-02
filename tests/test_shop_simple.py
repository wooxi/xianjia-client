#!/usr/bin/env python3
"""
闲管家店铺管理模块简单测试

不依赖完整 API 架构，仅测试核心模型和函数。
"""

import sys
import os
import importlib.util
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from models.shop import ShopInfo

# 直接加载 user.py 模块，避免 __init__.py 的导入问题
user_module_path = os.path.join(project_root, 'api', 'user.py')
spec = importlib.util.spec_from_file_location("user_api", user_module_path)
user_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(user_api)

_parse_datetime = user_api._parse_datetime
_shop_from_dict = user_api._shop_from_dict
APIError = user_api.APIError
TokenExpiredError = user_api.TokenExpiredError
PermissionDeniedError = user_api.PermissionDeniedError
ResourceNotFoundError = user_api.ResourceNotFoundError
APIErrorCode = user_api.APIErrorCode


def test_shop_info_creation():
    """测试 ShopInfo 创建"""
    print("测试 1: ShopInfo 创建...")
    
    shop = ShopInfo(
        authorize_id="auth_123",
        user_identity="user_456",
        user_name="张三",
        user_nick="小张",
        shop_name="张三的店铺",
        is_pro=True,
        is_deposit_enough=True,
        is_valid=True,
        is_trial=False,
        service_support=["item_manage", "order_process"],
        item_biz_types=["retail", "wholesale"]
    )
    
    assert shop.authorize_id == "auth_123"
    assert shop.user_name == "张三"
    assert shop.is_pro == True
    assert shop.is_valid == True
    assert len(shop.service_support) == 2
    print("  ✓ ShopInfo 创建成功")


def test_shop_info_defaults():
    """测试 ShopInfo 默认值"""
    print("测试 2: ShopInfo 默认值...")
    
    shop = ShopInfo(
        authorize_id="auth_123",
        user_identity="user_456",
        user_name="张三",
        user_nick="小张",
        shop_name="张三的店铺"
    )
    
    assert shop.is_pro == False
    assert shop.is_deposit_enough == False
    assert shop.is_valid == False
    assert shop.is_trial == False
    assert shop.valid_end_time is None
    assert shop.service_support == []
    assert shop.item_biz_types == []
    print("  ✓ 默认值正确")


def test_shop_expiration():
    """测试店铺过期检查"""
    print("测试 3: 店铺过期检查...")
    
    # 未来日期 - 未过期
    future_date = datetime.now() + timedelta(days=30)
    shop_future = ShopInfo(
        authorize_id="auth_123",
        user_identity="user_456",
        user_name="张三",
        user_nick="小张",
        shop_name="张三的店铺",
        valid_end_time=future_date
    )
    assert shop_future.is_expired() == False
    assert shop_future.get_remaining_days() is not None
    assert shop_future.get_remaining_days() >= 29
    
    # 过去日期 - 已过期
    past_date = datetime.now() - timedelta(days=30)
    shop_past = ShopInfo(
        authorize_id="auth_123",
        user_identity="user_456",
        user_name="张三",
        user_nick="小张",
        shop_name="张三的店铺",
        valid_end_time=past_date
    )
    assert shop_past.is_expired() == True
    
    # 无有效期 - 永不过期
    shop_no_end = ShopInfo(
        authorize_id="auth_123",
        user_identity="user_456",
        user_name="张三",
        user_nick="小张",
        shop_name="张三的店铺",
        valid_end_time=None
    )
    assert shop_no_end.is_expired() == False
    assert shop_no_end.get_remaining_days() is None
    
    print("  ✓ 过期检查正确")


def test_parse_datetime():
    """测试日期时间解析"""
    print("测试 4: 日期时间解析...")
    
    # 标准格式
    dt1 = _parse_datetime("2026-12-31 23:59:59")
    assert dt1.year == 2026
    assert dt1.month == 12
    assert dt1.day == 31
    
    # ISO 格式
    dt2 = _parse_datetime("2026-12-31T23:59:59")
    assert dt2 is not None
    
    # 仅日期
    dt3 = _parse_datetime("2026-12-31")
    assert dt3.year == 2026
    assert dt3.hour == 0
    
    # None 和空字符串
    assert _parse_datetime(None) is None
    assert _parse_datetime("") is None
    
    # 无效格式
    assert _parse_datetime("invalid") is None
    
    print("  ✓ 日期解析正确")


def test_shop_from_dict():
    """测试字典转 ShopInfo"""
    print("测试 5: 字典转 ShopInfo...")
    
    shop_data = {
        "authorize_id": "auth_123",
        "user_identity": "user_456",
        "user_name": "张三",
        "user_nick": "小张",
        "shop_name": "张三的店铺",
        "is_pro": True,
        "is_deposit_enough": True,
        "is_valid": True,
        "is_trial": False,
        "valid_end_time": "2026-12-31T23:59:59",
        "service_support": ["item_manage"],
        "item_biz_types": ["retail"]
    }
    
    shop = _shop_from_dict(shop_data)
    
    assert isinstance(shop, ShopInfo)
    assert shop.shop_name == "张三的店铺"
    assert shop.is_pro == True
    assert len(shop.service_support) == 1
    assert shop.valid_end_time is not None
    
    print("  ✓ 字典转换正确")


def test_api_exceptions():
    """测试 API 异常类"""
    print("测试 6: API 异常类...")
    
    # APIError
    error = APIError(code=1001, message="Test error", details="Details")
    assert error.code == 1001
    assert error.message == "Test error"
    assert "1001" in str(error)
    
    # TokenExpiredError
    token_error = TokenExpiredError()
    assert token_error.code == APIErrorCode.TOKEN_EXPIRED
    
    # PermissionDeniedError
    perm_error = PermissionDeniedError("No permission")
    assert perm_error.code == APIErrorCode.PERMISSION_DENIED
    assert perm_error.message == "No permission"
    
    # ResourceNotFoundError
    not_found_error = ResourceNotFoundError("Shop not found")
    assert not_found_error.code == APIErrorCode.RESOURCE_NOT_FOUND
    
    print("  ✓ 异常类正确")


def test_model_dump():
    """测试模型导出"""
    print("测试 7: 模型导出...")
    
    shop = ShopInfo(
        authorize_id="auth_123",
        user_identity="user_456",
        user_name="张三",
        user_nick="小张",
        shop_name="张三的店铺",
        is_pro=True
    )
    
    data = shop.model_dump()
    
    assert data["authorize_id"] == "auth_123"
    assert data["is_pro"] == True
    assert "service_support" in data
    assert "item_biz_types" in data
    
    print("  ✓ 模型导出正确")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("闲管家店铺管理模块测试")
    print("=" * 60)
    print()
    
    tests = [
        test_shop_info_creation,
        test_shop_info_defaults,
        test_shop_expiration,
        test_parse_datetime,
        test_shop_from_dict,
        test_api_exceptions,
        test_model_dump,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ 失败：{e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ 错误：{e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
