"""
商品模块单元测试

测试商品数据模型和 API 接口的功能。
"""

import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Any, Dict

from pydantic import ValidationError

# 导入被测试模块
from xianjia_client.models.product import (
    ProductDetail,
    ProductList,
    ProductListItem,
    ProductPublishStatus
)
from xianjia_client.api.product import (
    get_product_detail,
    list_products,
    list_products_all,
    search_products
)
from xianjia_client.exceptions import XianjiaException, RequestError, ResponseError


def async_test(coro):
    """装饰器：将异步测试函数包装为同步测试"""
    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))
    return wrapper


class TestProductPublishStatus(unittest.TestCase):
    """测试商品状态枚举"""
    
    def test_status_values(self):
        """测试枚举值"""
        self.assertEqual(ProductPublishStatus.ONSALE.value, "onsale")
        self.assertEqual(ProductPublishStatus.OFFLINE.value, "offline")
        self.assertEqual(ProductPublishStatus.RECYCLED.value, "recycled")
        self.assertEqual(ProductPublishStatus.ALL.value, "all")
    
    def test_status_from_string(self):
        """测试从字符串创建枚举"""
        status = ProductPublishStatus("onsale")
        self.assertEqual(status, ProductPublishStatus.ONSALE)
        
        status = ProductPublishStatus("offline")
        self.assertEqual(status, ProductPublishStatus.OFFLINE)


class TestProductDetail(unittest.TestCase):
    """测试商品详情数据模型"""
    
    def test_create_minimal_product(self):
        """测试创建最小化商品详情"""
        product = ProductDetail(
            product_id="123456",
            title="测试商品",
            price=99.99
        )
        
        self.assertEqual(product.product_id, "123456")
        self.assertEqual(product.title, "测试商品")
        self.assertEqual(product.price, 99.99)
        self.assertEqual(product.stock, 1)  # 默认值
        self.assertEqual(product.publish_status, ProductPublishStatus.OFFLINE)  # 默认值
        self.assertEqual(product.sales, 0)  # 默认值
    
    def test_create_full_product(self):
        """测试创建完整商品详情"""
        now = datetime.now()
        product = ProductDetail(
            product_id="789012",
            title="完整测试商品",
            price=199.00,
            stock=10,
            publish_status=ProductPublishStatus.ONSALE,
            description="这是一个测试商品描述",
            category_id="cat_001",
            category_name="测试分类",
            images=["http://example.com/img1.jpg", "http://example.com/img2.jpg"],
            sales=100,
            view_count=500,
            favorite_count=50,
            shop_id="shop_001",
            shop_name="测试店铺",
            create_time=now,
            update_time=now,
            publish_time=now,
            is_new=True,
            delivery_method="快递",
            location="杭州"
        )
        
        self.assertEqual(product.product_id, "789012")
        self.assertEqual(product.title, "完整测试商品")
        self.assertEqual(product.price, 199.00)
        self.assertEqual(product.stock, 10)
        self.assertEqual(product.publish_status, ProductPublishStatus.ONSALE)
        self.assertEqual(product.description, "这是一个测试商品描述")
        self.assertEqual(len(product.images), 2)
        self.assertEqual(product.sales, 100)
        self.assertEqual(product.view_count, 500)
        self.assertEqual(product.favorite_count, 50)
        self.assertEqual(product.is_new, True)
    
    def test_invalid_price(self):
        """测试无效价格"""
        with self.assertRaises(ValidationError):
            ProductDetail(
                product_id="123",
                title="测试",
                price=-10  # 负数价格
            )
    
    def test_invalid_stock(self):
        """测试无效库存"""
        with self.assertRaises(ValidationError):
            ProductDetail(
                product_id="123",
                title="测试",
                price=10,
                stock=-5  # 负数库存
            )
    
    def test_empty_product_id(self):
        """测试空商品 ID"""
        with self.assertRaises(ValidationError):
            ProductDetail(
                product_id="",
                title="测试",
                price=10
            )
    
    def test_from_api_response_basic(self):
        """测试从 API 响应创建 - 基础情况"""
        api_data = {
            "product_id": "api_123",
            "title": "API 测试商品",
            "price": 88.88,
            "stock": 5,
            "publish_status": "onsale"
        }
        
        product = ProductDetail.from_api_response(api_data)
        
        self.assertEqual(product.product_id, "api_123")
        self.assertEqual(product.title, "API 测试商品")
        self.assertEqual(product.price, 88.88)
        self.assertEqual(product.stock, 5)
        self.assertEqual(product.publish_status, "onsale")
    
    def test_from_api_response_with_timestamp(self):
        """测试从 API 响应创建 - 包含时间戳"""
        timestamp = int(datetime.now().timestamp() * 1000)
        api_data = {
            "product_id": "ts_123",
            "title": "时间戳测试",
            "price": 50,
            "create_time": timestamp
        }
        
        product = ProductDetail.from_api_response(api_data)
        
        self.assertIsNotNone(product.create_time)
        self.assertIsInstance(product.create_time, datetime)
    
    def test_from_api_response_with_iso_datetime(self):
        """测试从 API 响应创建 - 包含 ISO 格式时间"""
        now = datetime.now()
        iso_string = now.isoformat()
        api_data = {
            "product_id": "iso_123",
            "title": "ISO 时间测试",
            "price": 60,
            "update_time": iso_string
        }
        
        product = ProductDetail.from_api_response(api_data)
        
        self.assertIsNotNone(product.update_time)
    
    def test_from_api_response_with_image_string(self):
        """测试从 API 响应创建 - 图片为逗号分隔字符串"""
        api_data = {
            "product_id": "img_123",
            "title": "图片测试",
            "price": 70,
            "images": "http://img1.jpg,http://img2.jpg,http://img3.jpg"
        }
        
        product = ProductDetail.from_api_response(api_data)
        
        self.assertEqual(len(product.images), 3)
        self.assertEqual(product.images[0], "http://img1.jpg")
    
    def test_to_dict(self):
        """测试转换为字典"""
        product = ProductDetail(
            product_id="dict_123",
            title="字典测试",
            price=45.5
        )
        
        data = product.to_dict()
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data["product_id"], "dict_123")
        self.assertEqual(data["title"], "字典测试")
        self.assertEqual(data["price"], 45.5)


class TestProductListItem(unittest.TestCase):
    """测试商品列表项数据模型"""
    
    def test_create_list_item(self):
        """测试创建列表项"""
        item = ProductListItem(
            product_id="item_123",
            title="列表项测试",
            price=29.9,
            stock=3,
            publish_status=ProductPublishStatus.ONSALE
        )
        
        self.assertEqual(item.product_id, "item_123")
        self.assertEqual(item.title, "列表项测试")
        self.assertEqual(item.price, 29.9)
        self.assertEqual(item.stock, 3)
        self.assertEqual(item.publish_status, "onsale")
    
    def test_from_api_response(self):
        """测试从 API 响应创建"""
        api_data = {
            "product_id": "list_123",
            "title": "列表 API 测试",
            "price": 39.9,
            "stock": 2,
            "publish_status": "onsale",
            "sales": 15,
            "images": ["http://main.jpg", "http://sub.jpg"],
            "category_name": "数码",
            "shop_name": "测试店"
        }
        
        item = ProductListItem.from_api_response(api_data)
        
        self.assertEqual(item.product_id, "list_123")
        self.assertEqual(item.main_image, "http://main.jpg")  # 第一张图
        self.assertEqual(item.category_name, "数码")
        self.assertEqual(item.shop_name, "测试店")
        self.assertEqual(item.sales, 15)


class TestProductList(unittest.TestCase):
    """测试商品列表响应数据模型"""
    
    def test_create_product_list(self):
        """测试创建商品列表"""
        items = [
            ProductListItem(
                product_id=f"p{i}",
                title=f"商品{i}",
                price=i * 10,
                stock=1,
                publish_status=ProductPublishStatus.ONSALE
            )
            for i in range(1, 6)
        ]
        
        product_list = ProductList(
            total=100,
            page_no=1,
            page_size=20,
            total_pages=5,
            list=items
        )
        
        self.assertEqual(product_list.total, 100)
        self.assertEqual(product_list.page_no, 1)
        self.assertEqual(product_list.page_size, 20)
        self.assertEqual(product_list.total_pages, 5)
        self.assertEqual(len(product_list.list), 5)
    
    def test_from_api_response(self):
        """测试从 API 响应创建"""
        api_data = {
            "total": 50,
            "list": [
                {
                    "product_id": f"p{i}",
                    "title": f"商品{i}",
                    "price": i * 5,
                    "stock": 1,
                    "publish_status": "onsale"
                }
                for i in range(1, 11)
            ]
        }
        
        product_list = ProductList.from_api_response(api_data, page_no=2, page_size=10)
        
        self.assertEqual(product_list.total, 50)
        self.assertEqual(product_list.page_no, 2)
        self.assertEqual(product_list.page_size, 10)
        self.assertEqual(product_list.total_pages, 5)  # 50/10=5
        self.assertEqual(len(product_list.list), 10)
    
    def test_has_next_page(self):
        """测试是否有下一页"""
        # 有下一页
        product_list = ProductList(
            total=100,
            page_no=1,
            page_size=20,
            total_pages=5,
            list=[]
        )
        self.assertTrue(product_list.has_next_page)
        
        # 最后一页
        product_list.page_no = 5
        self.assertFalse(product_list.has_next_page)
        
        # 超过总页数
        product_list.page_no = 6
        self.assertFalse(product_list.has_next_page)
    
    def test_has_prev_page(self):
        """测试是否有上一页"""
        # 第一页
        product_list = ProductList(
            total=100,
            page_no=1,
            page_size=20,
            total_pages=5,
            list=[]
        )
        self.assertFalse(product_list.has_prev_page)
        
        # 第二页
        product_list.page_no = 2
        self.assertTrue(product_list.has_prev_page)
    
    def test_total_pages_calculation(self):
        """测试总页数计算"""
        # 整除
        product_list = ProductList.from_api_response(
            {"total": 100, "list": []},
            page_no=1,
            page_size=20
        )
        self.assertEqual(product_list.total_pages, 5)
        
        # 有余数
        product_list = ProductList.from_api_response(
            {"total": 101, "list": []},
            page_no=1,
            page_size=20
        )
        self.assertEqual(product_list.total_pages, 6)  # 向上取整
        
        # 总数为 0
        product_list = ProductList.from_api_response(
            {"total": 0, "list": []},
            page_no=1,
            page_size=20
        )
        self.assertEqual(product_list.total_pages, 0)


class TestGetProductDetail(unittest.TestCase):
    """测试 get_product_detail API 函数"""
    
    @async_test
    async def test_get_product_detail_success(self):
        """测试成功获取商品详情"""
        # 模拟客户端
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value={
            "code": 0,
            "message": "success",
            "data": {
                "product_id": "test_123",
                "title": "测试商品",
                "price": 99.9,
                "stock": 10,
                "publish_status": "onsale"
            }
        })
        
        result = await get_product_detail(mock_client, "test_123")
        
        self.assertIsInstance(result, ProductDetail)
        self.assertEqual(result.product_id, "test_123")
        self.assertEqual(result.title, "测试商品")
        mock_client.get.assert_called_once_with("/item/detail", params={"item_id": "test_123"})
    
    @async_test
    async def test_get_product_detail_empty_id(self):
        """测试空商品 ID"""
        mock_client = AsyncMock()
        
        with self.assertRaises(RequestError):
            await get_product_detail(mock_client, "")
        
        with self.assertRaises(RequestError):
            await get_product_detail(mock_client, None)
    
    @async_test
    async def test_get_product_detail_api_error(self):
        """测试 API 错误响应"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value={
            "code": 404,
            "message": "商品不存在"
        })
        
        with self.assertRaises(XianjiaException):
            await get_product_detail(mock_client, "not_exist")
    
    @async_test
    async def test_get_product_detail_empty_response(self):
        """测试空响应"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=None)
        
        with self.assertRaises(ResponseError):
            await get_product_detail(mock_client, "test_123")


class TestListProducts(unittest.TestCase):
    """测试 list_products API 函数"""
    
    @async_test
    async def test_list_products_basic(self):
        """测试基础列表查询"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value={
            "code": 0,
            "message": "success",
            "data": {
                "total": 50,
                "list": [
                    {
                        "product_id": f"p{i}",
                        "title": f"商品{i}",
                        "price": i * 10,
                        "stock": 1,
                        "publish_status": "onsale"
                    }
                    for i in range(1, 21)
                ]
            }
        })
        
        result = await list_products(mock_client, page_no=1, page_size=20)
        
        self.assertIsInstance(result, ProductList)
        self.assertEqual(result.total, 50)
        self.assertEqual(len(result.list), 20)
        mock_client.get.assert_called_once()
    
    @async_test
    async def test_list_products_with_status(self):
        """测试带状态筛选"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value={
            "code": 0,
            "message": "success",
            "data": {"total": 10, "list": []}
        })
        
        await list_products(
            mock_client,
            product_status=ProductPublishStatus.ONSALE,
            page_no=1,
            page_size=20
        )
        
        # 验证调用了正确的参数
        call_args = mock_client.get.call_args
        self.assertEqual(call_args[1]["params"]["item_status"], "onsale")
    
    @async_test
    async def test_list_products_with_time_filter(self):
        """测试带时间筛选"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value={
            "code": 0,
            "message": "success",
            "data": {"total": 10, "list": []}
        })
        
        update_time = datetime(2024, 1, 1, 12, 0, 0)
        await list_products(mock_client, update_time=update_time, page_no=1, page_size=20)
        
        # 验证时间参数
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        self.assertIn("start_update_time", params)
        self.assertIsInstance(params["start_update_time"], int)
    
    @async_test
    async def test_list_products_invalid_page_no(self):
        """测试无效页码"""
        mock_client = AsyncMock()
        
        with self.assertRaises(RequestError):
            await list_products(mock_client, page_no=0, page_size=20)
        
        with self.assertRaises(RequestError):
            await list_products(mock_client, page_no=-1, page_size=20)
    
    @async_test
    async def test_list_products_invalid_page_size(self):
        """测试无效每页数量"""
        mock_client = AsyncMock()
        
        with self.assertRaises(RequestError):
            await list_products(mock_client, page_no=1, page_size=0)
    
    @async_test
    async def test_list_products_auto_adjust_page_size(self):
        """测试自动调整过大的 page_size"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value={
            "code": 0,
            "message": "success",
            "data": {"total": 10, "list": []}
        })
        
        await list_products(mock_client, page_no=1, page_size=1000)
        
        # 验证 page_size 被调整为 500
        call_args = mock_client.get.call_args
        self.assertEqual(call_args[1]["params"]["page_size"], 500)


class TestListProductsAll(unittest.TestCase):
    """测试 list_products_all API 函数"""
    
    @async_test
    async def test_list_products_all_single_page(self):
        """测试单页结果"""
        mock_client = AsyncMock()
        
        # Mock list_products
        with patch('xianjia_client.api.product.list_products') as mock_list:
            mock_list.return_value = ProductList(
                total=10,
                page_no=1,
                page_size=20,
                total_pages=1,
                list=[
                    ProductListItem(
                        product_id=f"p{i}",
                        title=f"商品{i}",
                        price=i * 10,
                        stock=1,
                        publish_status=ProductPublishStatus.ONSALE
                    )
                    for i in range(1, 11)
                ]
            )
            
            result = await list_products_all(mock_client, page_size=20)
            
            self.assertEqual(len(result), 10)
            mock_list.assert_called_once()
    
    @async_test
    async def test_list_products_all_multiple_pages(self):
        """测试多页结果"""
        mock_client = AsyncMock()
        call_count = [0]  # 使用列表来追踪调用次数
        
        # 模拟多页响应
        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            page_no = kwargs.get('page_no', 1)
            if page_no == 1:
                return ProductList(
                    total=50,
                    page_no=1,
                    page_size=20,
                    total_pages=3,
                    list=[ProductListItem(
                        product_id=f"p{i}",
                        title=f"商品{i}",
                        price=10,
                        stock=1,
                        publish_status=ProductPublishStatus.ONSALE
                    ) for i in range(1, 21)]
                )
            elif page_no == 2:
                return ProductList(
                    total=50,
                    page_no=2,
                    page_size=20,
                    total_pages=3,
                    list=[ProductListItem(
                        product_id=f"p{i}",
                        title=f"商品{i}",
                        price=10,
                        stock=1,
                        publish_status=ProductPublishStatus.ONSALE
                    ) for i in range(21, 41)]
                )
            else:
                return ProductList(
                    total=50,
                    page_no=3,
                    page_size=20,
                    total_pages=3,
                    list=[ProductListItem(
                        product_id=f"p{i}",
                        title=f"商品{i}",
                        price=10,
                        stock=1,
                        publish_status=ProductPublishStatus.ONSALE
                    ) for i in range(41, 51)]
                )
        
        with patch('xianjia_client.api.product.list_products', side_effect=side_effect):
            result = await list_products_all(mock_client, page_size=20)
            
            self.assertEqual(len(result), 50)
            self.assertEqual(call_count[0], 3)  # 应该调用 3 次
    
    @async_test
    async def test_list_products_all_with_max_pages(self):
        """测试最大页数限制"""
        mock_client = AsyncMock()
        
        # 模拟总是有下一页
        async def side_effect(*args, **kwargs):
            page_no = kwargs.get('page_no', 1)
            return ProductList(
                total=999,
                page_no=page_no,
                page_size=20,
                total_pages=50,
                list=[ProductListItem(
                    product_id=f"p{i}",
                    title=f"商品{i}",
                    price=10,
                    stock=1,
                    publish_status=ProductPublishStatus.ONSALE
                ) for i in range(1, 21)]
            )
        
        with patch('xianjia_client.api.product.list_products', side_effect=side_effect):
            result = await list_products_all(mock_client, page_size=20, max_pages=3)
            
            # 应该只获取 3 页
            self.assertEqual(len(result), 60)  # 3 页 * 20 条


class TestSearchProducts(unittest.TestCase):
    """测试 search_products API 函数"""
    
    @async_test
    async def test_search_products_success(self):
        """测试成功搜索"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value={
            "code": 0,
            "message": "success",
            "data": {
                "total": 5,
                "list": [
                    {
                        "product_id": "s1",
                        "title": "搜索商品 1",
                        "price": 50,
                        "stock": 1,
                        "publish_status": "onsale"
                    }
                ]
            }
        })
        
        result = await search_products(mock_client, keyword="测试", page_no=1, page_size=20)
        
        self.assertIsInstance(result, ProductList)
        self.assertEqual(result.total, 5)
        mock_client.get.assert_called_once()
    
    @async_test
    async def test_search_products_empty_keyword(self):
        """测试空关键词"""
        mock_client = AsyncMock()
        
        with self.assertRaises(RequestError):
            await search_products(mock_client, keyword="", page_no=1, page_size=20)
        
        with self.assertRaises(RequestError):
            await search_products(mock_client, keyword=None, page_no=1, page_size=20)


class TestProductModelEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def test_product_title_max_length(self):
        """测试标题最大长度"""
        # 500 字符应该成功
        long_title = "a" * 500
        product = ProductDetail(
            product_id="test",
            title=long_title,
            price=10
        )
        self.assertEqual(len(product.title), 500)
        
        # 501 字符应该失败
        with self.assertRaises(ValidationError):
            ProductDetail(
                product_id="test",
                title="a" * 501,
                price=10
            )
    
    def test_product_zero_price(self):
        """测试 0 元商品"""
        product = ProductDetail(
            product_id="free",
            title="免费商品",
            price=0
        )
        self.assertEqual(product.price, 0)
    
    def test_product_zero_stock(self):
        """测试 0 库存"""
        product = ProductDetail(
            product_id="out",
            title="售罄商品",
            price=10,
            stock=0
        )
        self.assertEqual(product.stock, 0)
    
    def test_empty_images_list(self):
        """测试空图片列表"""
        product = ProductDetail(
            product_id="noimg",
            title="无图商品",
            price=10,
            images=[]
        )
        self.assertEqual(product.images, [])
    
    def test_product_list_empty_list(self):
        """测试空商品列表"""
        product_list = ProductList(
            total=0,
            page_no=1,
            page_size=20,
            total_pages=0,
            list=[]
        )
        self.assertEqual(product_list.total, 0)
        self.assertEqual(len(product_list.list), 0)
        self.assertFalse(product_list.has_next_page)
        self.assertFalse(product_list.has_prev_page)


if __name__ == "__main__":
    unittest.main()
