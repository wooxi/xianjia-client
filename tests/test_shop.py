"""
闲管家店铺管理模块单元测试

包含对 ShopInfo 数据模型和用户/店铺 API 接口的完整测试。
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.shop import ShopInfo
from api.user import (
    get_authorized_shops,
    get_shop_detail,
    APIError,
    TokenExpiredError,
    PermissionDeniedError,
    ResourceNotFoundError,
    _parse_datetime,
    _shop_from_dict,
    APIErrorCode
)


class TestShopInfo(unittest.TestCase):
    """ShopInfo 数据模型测试"""
    
    def test_create_shop_with_required_fields(self):
        """测试使用必填字段创建店铺对象"""
        shop = ShopInfo(
            authorize_id="auth_123",
            user_identity="user_456",
            user_name="张三",
            user_nick="小张",
            shop_name="张三的店铺"
        )
        
        self.assertEqual(shop.authorize_id, "auth_123")
        self.assertEqual(shop.user_identity, "user_456")
        self.assertEqual(shop.user_name, "张三")
        self.assertEqual(shop.user_nick, "小张")
        self.assertEqual(shop.shop_name, "张三的店铺")
        # 默认值测试
        self.assertFalse(shop.is_pro)
        self.assertFalse(shop.is_deposit_enough)
        self.assertFalse(shop.is_valid)
        self.assertFalse(shop.is_trial)
        self.assertIsNone(shop.valid_end_time)
        self.assertEqual(shop.service_support, [])
        self.assertEqual(shop.item_biz_types, [])
    
    def test_create_shop_with_all_fields(self):
        """测试使用所有字段创建店铺对象"""
        valid_end = datetime(2026, 12, 31, 23, 59, 59)
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
            valid_end_time=valid_end,
            service_support=["item_manage", "order_process"],
            item_biz_types=["retail", "wholesale"]
        )
        
        self.assertTrue(shop.is_pro)
        self.assertTrue(shop.is_deposit_enough)
        self.assertTrue(shop.is_valid)
        self.assertFalse(shop.is_trial)
        self.assertEqual(shop.valid_end_time, valid_end)
        self.assertEqual(shop.service_support, ["item_manage", "order_process"])
        self.assertEqual(shop.item_biz_types, ["retail", "wholesale"])
    
    def test_create_shop_from_dict(self):
        """测试从字典创建店铺对象"""
        shop_data = {
            "authorize_id": "auth_789",
            "user_identity": "user_012",
            "user_name": "李四",
            "user_nick": "小李",
            "shop_name": "李四的店铺",
            "is_pro": True,
            "is_deposit_enough": False,
            "is_valid": True,
            "is_trial": True,
            "valid_end_time": "2026-06-30T23:59:59",
            "service_support": ["customer_service"],
            "item_biz_types": ["retail"]
        }
        
        shop = ShopInfo(**shop_data)
        
        self.assertEqual(shop.authorize_id, "auth_789")
        self.assertEqual(shop.user_name, "李四")
        self.assertTrue(shop.is_pro)
        self.assertTrue(shop.is_trial)
    
    def test_is_expired_with_future_date(self):
        """测试未过期的店铺"""
        future_date = datetime.now() + timedelta(days=30)
        shop = ShopInfo(
            authorize_id="auth_123",
            user_identity="user_456",
            user_name="张三",
            user_nick="小张",
            shop_name="张三的店铺",
            valid_end_time=future_date
        )
        
        self.assertFalse(shop.is_expired())
    
    def test_is_expired_with_past_date(self):
        """测试已过期的店铺"""
        past_date = datetime.now() - timedelta(days=30)
        shop = ShopInfo(
            authorize_id="auth_123",
            user_identity="user_456",
            user_name="张三",
            user_nick="小张",
            shop_name="张三的店铺",
            valid_end_time=past_date
        )
        
        self.assertTrue(shop.is_expired())
    
    def test_is_expired_without_end_time(self):
        """测试无有效期的店铺"""
        shop = ShopInfo(
            authorize_id="auth_123",
            user_identity="user_456",
            user_name="张三",
            user_nick="小张",
            shop_name="张三的店铺",
            valid_end_time=None
        )
        
        self.assertFalse(shop.is_expired())
    
    def test_get_remaining_days(self):
        """测试获取剩余天数"""
        future_date = datetime.now() + timedelta(days=30)
        shop = ShopInfo(
            authorize_id="auth_123",
            user_identity="user_456",
            user_name="张三",
            user_nick="小张",
            shop_name="张三的店铺",
            valid_end_time=future_date
        )
        
        remaining = shop.get_remaining_days()
        self.assertIsNotNone(remaining)
        self.assertGreaterEqual(remaining, 29)  # 考虑执行时间差异
        self.assertLessEqual(remaining, 31)
    
    def test_get_remaining_days_without_end_time(self):
        """测试无有效期时返回 None"""
        shop = ShopInfo(
            authorize_id="auth_123",
            user_identity="user_456",
            user_name="张三",
            user_nick="小张",
            shop_name="张三的店铺",
            valid_end_time=None
        )
        
        self.assertIsNone(shop.get_remaining_days())
    
    def test_validation_error_empty_authorize_id(self):
        """测试空 authorize_id 抛出验证错误"""
        with self.assertRaises(Exception):  # pydantic.ValidationError
            ShopInfo(
                authorize_id="",
                user_identity="user_456",
                user_name="张三",
                user_nick="小张",
                shop_name="张三的店铺"
            )
    
    def test_model_dump(self):
        """测试模型导出为字典"""
        shop = ShopInfo(
            authorize_id="auth_123",
            user_identity="user_456",
            user_name="张三",
            user_nick="小张",
            shop_name="张三的店铺",
            is_pro=True
        )
        
        data = shop.model_dump()
        
        self.assertEqual(data["authorize_id"], "auth_123")
        self.assertEqual(data["is_pro"], True)
        self.assertIn("service_support", data)
        self.assertIn("item_biz_types", data)


class TestParseDatetime(unittest.TestCase):
    """日期时间解析函数测试"""
    
    def test_parse_standard_format(self):
        """测试标准格式解析"""
        result = _parse_datetime("2026-12-31 23:59:59")
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 31)
        self.assertEqual(result.hour, 23)
        self.assertEqual(result.minute, 59)
        self.assertEqual(result.second, 59)
    
    def test_parse_iso_format(self):
        """测试 ISO 格式解析"""
        result = _parse_datetime("2026-12-31T23:59:59")
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 12)
    
    def test_parse_iso_with_z(self):
        """测试带 Z 的 ISO 格式"""
        result = _parse_datetime("2026-12-31T23:59:59Z")
        self.assertIsNotNone(result)
    
    def test_parse_date_only(self):
        """测试仅日期格式"""
        result = _parse_datetime("2026-12-31")
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 31)
        self.assertEqual(result.hour, 0)
        self.assertEqual(result.minute, 0)
    
    def test_parse_none(self):
        """测试 None 输入"""
        result = _parse_datetime(None)
        self.assertIsNone(result)
    
    def test_parse_empty_string(self):
        """测试空字符串"""
        result = _parse_datetime("")
        self.assertIsNone(result)
    
    def test_parse_invalid_format(self):
        """测试无效格式返回 None"""
        result = _parse_datetime("invalid-date")
        self.assertIsNone(result)


class TestShopFromDict(unittest.TestCase):
    """字典转 ShopInfo 对象测试"""
    
    def test_convert_complete_dict(self):
        """测试完整字典转换"""
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
        
        self.assertIsInstance(shop, ShopInfo)
        self.assertEqual(shop.authorize_id, "auth_123")
        self.assertTrue(shop.is_pro)
        self.assertEqual(len(shop.service_support), 1)
    
    def test_convert_minimal_dict(self):
        """测试最小字典转换"""
        shop_data = {
            "authorize_id": "auth_123",
            "user_identity": "user_456",
            "user_name": "张三",
            "user_nick": "小张",
            "shop_name": "张三的店铺"
        }
        
        shop = _shop_from_dict(shop_data)
        
        self.assertIsInstance(shop, ShopInfo)
        self.assertFalse(shop.is_pro)
        self.assertEqual(shop.service_support, [])
    
    def test_convert_with_invalid_date(self):
        """测试带无效日期的字典"""
        shop_data = {
            "authorize_id": "auth_123",
            "user_identity": "user_456",
            "user_name": "张三",
            "user_nick": "小张",
            "shop_name": "张三的店铺",
            "valid_end_time": "invalid-date"
        }
        
        shop = _shop_from_dict(shop_data)
        
        self.assertIsInstance(shop, ShopInfo)
        self.assertIsNone(shop.valid_end_time)


class TestGetAuthorizedShops(unittest.TestCase):
    """get_authorized_shops API 接口测试"""
    
    @patch('api.user.httpx.Client')
    def test_get_shops_success(self, mock_client_class):
        """测试成功获取店铺列表"""
        # 准备模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "message": "success",
            "data": {
                "shops": [
                    {
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
                ]
            }
        }
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        # 调用 API
        shops = get_authorized_shops(
            api_base_url="https://api.xianjia.com",
            access_token="test_token"
        )
        
        # 验证结果
        self.assertEqual(len(shops), 1)
        self.assertIsInstance(shops[0], ShopInfo)
        self.assertEqual(shops[0].shop_name, "张三的店铺")
        self.assertTrue(shops[0].is_pro)
    
    @patch('api.user.httpx.Client')
    def test_get_shops_empty_list(self, mock_client_class):
        """测试空店铺列表"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "message": "success",
            "data": {"shops": []}
        }
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        shops = get_authorized_shops(
            api_base_url="https://api.xianjia.com",
            access_token="test_token"
        )
        
        self.assertEqual(len(shops), 0)
        self.assertIsInstance(shops, list)
    
    @patch('api.user.httpx.Client')
    def test_get_shops_token_expired(self, mock_client_class):
        """测试 Token 过期异常"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "code": 1002,
            "message": "Token 已过期"
        }
        
        from httpx import HTTPStatusError
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        
        http_error = HTTPStatusError(
            "Unauthorized",
            request=Mock(),
            response=mock_response
        )
        mock_client.get = Mock(side_effect=http_error)
        mock_client_class.return_value = mock_client
        
        with self.assertRaises(TokenExpiredError):
            get_authorized_shops(
                api_base_url="https://api.xianjia.com",
                access_token="expired_token"
            )
    
    @patch('api.user.httpx.Client')
    def test_get_shops_permission_denied(self, mock_client_class):
        """测试权限不足异常"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "code": 1003,
            "message": "权限不足"
        }
        
        from httpx import HTTPStatusError
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        
        http_error = HTTPStatusError(
            "Forbidden",
            request=Mock(),
            response=mock_response
        )
        mock_client.get = Mock(side_effect=http_error)
        mock_client_class.return_value = mock_client
        
        with self.assertRaises(PermissionDeniedError):
            get_authorized_shops(
                api_base_url="https://api.xianjia.com",
                access_token="test_token"
            )
    
    @patch('api.user.httpx.Client')
    def test_get_shops_not_found(self, mock_client_class):
        """测试资源不存在异常"""
        mock_response = Mock()
        mock_response.status_code = 404
        
        from httpx import HTTPStatusError
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        
        http_error = HTTPStatusError(
            "Not Found",
            request=Mock(),
            response=mock_response
        )
        mock_client.get = Mock(side_effect=http_error)
        mock_client_class.return_value = mock_client
        
        with self.assertRaises(ResourceNotFoundError):
            get_authorized_shops(
                api_base_url="https://api.xianjia.com",
                access_token="test_token"
            )
    
    @patch('api.user.httpx.Client')
    def test_get_shops_network_error(self, mock_client_class):
        """测试网络错误"""
        from httpx import RequestError
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get = Mock(side_effect=RequestError("Network error", request=Mock()))
        mock_client_class.return_value = mock_client
        
        with self.assertRaises(APIError):
            get_authorized_shops(
                api_base_url="https://api.xianjia.com",
                access_token="test_token"
            )
    
    @patch('api.user.httpx.Client')
    def test_get_shops_invalid_json(self, mock_client_class):
        """测试无效 JSON 响应"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        with self.assertRaises(APIError):
            get_authorized_shops(
                api_base_url="https://api.xianjia.com",
                access_token="test_token"
            )
    
    @patch('api.user.httpx.Client')
    def test_get_shops_alternative_response_format(self, mock_client_class):
        """测试替代响应格式（data 直接是列表）"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": [
                {
                    "authorize_id": "auth_123",
                    "user_identity": "user_456",
                    "user_name": "张三",
                    "user_nick": "小张",
                    "shop_name": "张三的店铺"
                }
            ]
        }
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        shops = get_authorized_shops(
            api_base_url="https://api.xianjia.com",
            access_token="test_token"
        )
        
        self.assertEqual(len(shops), 1)
        self.assertEqual(shops[0].shop_name, "张三的店铺")


class TestGetShopDetail(unittest.TestCase):
    """get_shop_detail API 接口测试"""
    
    @patch('api.user.httpx.Client')
    def test_get_shop_detail_success(self, mock_client_class):
        """测试成功获取店铺详情"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "message": "success",
            "data": {
                "authorize_id": "auth_123",
                "user_identity": "user_456",
                "user_name": "张三",
                "user_nick": "小张",
                "shop_name": "张三的店铺",
                "is_pro": True
            }
        }
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        shop = get_shop_detail(
            api_base_url="https://api.xianjia.com",
            access_token="test_token",
            authorize_id="auth_123"
        )
        
        self.assertIsInstance(shop, ShopInfo)
        self.assertEqual(shop.shop_name, "张三的店铺")
        self.assertTrue(shop.is_pro)


class TestAPIExceptions(unittest.TestCase):
    """API 异常类测试"""
    
    def test_api_error_creation(self):
        """测试 APIError 创建"""
        error = APIError(code=1001, message="Test error", details="Additional info")
        
        self.assertEqual(error.code, 1001)
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.details, "Additional info")
        self.assertIn("1001", str(error))
        self.assertIn("Test error", str(error))
    
    def test_token_expired_error(self):
        """测试 TokenExpiredError"""
        error = TokenExpiredError()
        self.assertEqual(error.code, APIErrorCode.TOKEN_EXPIRED)
        self.assertIn("过期", error.message)
    
    def test_permission_denied_error(self):
        """测试 PermissionDeniedError"""
        error = PermissionDeniedError("Custom message")
        self.assertEqual(error.code, APIErrorCode.PERMISSION_DENIED)
        self.assertEqual(error.message, "Custom message")
    
    def test_resource_not_found_error(self):
        """测试 ResourceNotFoundError"""
        error = ResourceNotFoundError("Shop not found")
        self.assertEqual(error.code, APIErrorCode.RESOURCE_NOT_FOUND)
        self.assertEqual(error.message, "Shop not found")


if __name__ == '__main__':
    unittest.main()
