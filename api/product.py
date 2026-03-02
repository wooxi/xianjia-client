"""
商品 API 接口

提供闲管家商品查询相关的 API 接口封装，包括商品详情查询和商品列表查询。
支持分页、时间范围筛选和状态筛选。
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from ..client import XianjiaClient
from ..exceptions import XianjiaException, RequestError, ResponseError
from ..models.product import ProductDetail, ProductList, ProductListItem, ProductPublishStatus

logger = logging.getLogger(__name__)


async def get_product_detail(
    client: XianjiaClient,
    product_id: str
) -> ProductDetail:
    """
    查询商品详情
    
    根据商品 ID 获取商品的完整详细信息。
    
    Args:
        client: 闲管家 API 客户端实例
        product_id: 商品唯一标识符
    
    Returns:
        ProductDetail: 商品详情对象
    
    Raises:
        XianjiaException: API 请求失败或响应异常
        RequestError: 请求参数错误
        ResponseError: 响应数据格式错误
    
    Example:
        >>> import asyncio
        >>> from xianjia_client import XianjiaClient, Config
        >>> 
        >>> async def main():
        ...     config = Config(app_key="your_app_key", app_secret="your_app_secret")
        ...     async with XianjiaClient(config) as client:
        ...         product = await get_product_detail(client, "123456789")
        ...         print(f"商品标题：{product.title}")
        ...         print(f"商品价格：{product.price}")
        >>> 
        >>> asyncio.run(main())
    """
    if not product_id or not isinstance(product_id, str):
        raise RequestError("product_id 必须是非空字符串")
    
    logger.info(f"查询商品详情：product_id={product_id}")
    
    try:
        # 构建 API 请求
        # 闲管家商品详情接口路径（根据实际 API 文档调整）
        api_path = "/item/detail"
        params = {
            "item_id": product_id
        }
        
        # 发送请求
        response = await client.get(api_path, params=params)
        
        # 检查响应状态
        if not response:
            raise ResponseError("API 响应为空")
        
        # 解析响应数据
        # 假设响应格式：{"code": 0, "message": "success", "data": {...}}
        # 或：{"code": 200, "msg": "success", "data": {...}}
        code = response.get("code", response.get("error_code", 0))
        msg = response.get("message", response.get("msg", response.get("error", "Unknown error")))
        data = response.get("data", {})
        
        # 检查错误（code != 0 表示错误）
        if code and code != 0 and code != "0":
            logger.error(f"API 返回错误：code={code}, msg={msg}")
            raise XianjiaException(f"查询商品详情失败：{msg}", code=str(code))
        
        if not data:
            raise ResponseError("商品详情数据为空")
        
        # 转换为 ProductDetail 对象
        product = ProductDetail.from_api_response(data)
        
        logger.info(f"成功获取商品详情：{product.title}")
        return product
        
    except XianjiaException:
        raise
    except Exception as e:
        logger.error(f"查询商品详情异常：{e}")
        raise ResponseError(f"解析商品详情失败：{str(e)}")


async def list_products(
    client: XianjiaClient,
    update_time: Optional[datetime] = None,
    product_status: Optional[ProductPublishStatus] = None,
    page_no: int = 1,
    page_size: int = 20
) -> ProductList:
    """
    查询商品列表
    
    支持分页查询，可选时间范围筛选和状态筛选。
    
    Args:
        client: 闲管家 API 客户端实例
        update_time: 更新时间筛选（查询该时间之后的商品），可选
        product_status: 商品状态筛选，可选，默认为 None（查询所有状态）
        page_no: 页码，从 1 开始，默认 1
        page_size: 每页数量，范围 1-500，默认 20
    
    Returns:
        ProductList: 商品列表响应对象，包含分页信息和商品列表
    
    Raises:
        XianjiaException: API 请求失败或响应异常
        RequestError: 请求参数错误
        ResponseError: 响应数据格式错误
    
    Example:
        >>> import asyncio
        >>> from datetime import datetime, timedelta
        >>> from xianjia_client import XianjiaClient, Config
        >>> from xianjia_client.models.product import ProductPublishStatus
        >>> 
        >>> async def main():
        ...     config = Config(app_key="your_app_key", app_secret="your_app_secret")
        ...     async with XianjiaClient(config) as client:
        ...         # 查询所有商品
        ...         result = await list_products(client, page_no=1, page_size=20)
        ...         print(f"总商品数：{result.total}")
        ...         for item in result.list:
        ...             print(f"商品：{item.title}, 价格：{item.price}")
        ...         
        ...         # 查询出售中的商品
        ...         result = await list_products(client, product_status=ProductPublishStatus.ONSALE)
        ...         
        ...         # 查询最近更新的商品（最近 24 小时）
        ...         yesterday = datetime.now() - timedelta(days=1)
        ...         result = await list_products(client, update_time=yesterday)
        >>> 
        >>> asyncio.run(main())
    
    Note:
        - page_size 最大值为 500，超过会自动调整为 500
        - update_time 用于筛选在该时间之后更新的商品
        - product_status 为 None 时查询所有状态的商品
    """
    # 参数验证
    if page_no < 1:
        raise RequestError("page_no 必须大于等于 1")
    
    if page_size < 1:
        raise RequestError("page_size 必须大于等于 1")
    
    if page_size > 500:
        logger.warning(f"page_size={page_size} 超过最大值，已调整为 500")
        page_size = 500
    
    logger.info(
        f"查询商品列表：page_no={page_no}, page_size={page_size}, "
        f"update_time={update_time}, product_status={product_status}"
    )
    
    try:
        # 构建 API 请求参数
        api_path = "/item/list"
        params = {
            "page_no": page_no,
            "page_size": page_size
        }
        
        # 添加时间筛选参数
        if update_time:
            if not isinstance(update_time, datetime):
                raise RequestError("update_time 必须是 datetime 类型")
            # 转换为时间戳（毫秒）
            params["start_update_time"] = int(update_time.timestamp() * 1000)
            logger.debug(f"时间筛选：start_update_time={params['start_update_time']}")
        
        # 添加状态筛选参数
        if product_status:
            # 如果是 ALL 状态，不添加筛选参数
            if product_status != ProductPublishStatus.ALL:
                params["item_status"] = product_status.value
                logger.debug(f"状态筛选：item_status={params['item_status']}")
        
        # 发送请求
        response = await client.get(api_path, params=params)
        
        # 检查响应状态
        if not response:
            raise ResponseError("API 响应为空")
        
        # 解析响应数据
        code = response.get("code", response.get("error_code", 0))
        msg = response.get("message", response.get("msg", response.get("error", "Unknown error")))
        data = response.get("data", {})
        
        # 检查错误
        if code and code != 0 and code != "0":
            logger.error(f"API 返回错误：code={code}, msg={msg}")
            raise XianjiaException(f"查询商品列表失败：{msg}", code=str(code))
        
        # 确保数据格式正确
        if not isinstance(data, dict):
            raise ResponseError("响应数据格式错误：data 应为字典类型")
        
        if "total" not in data:
            logger.warning("响应中缺少 total 字段，使用默认值 0")
            data["total"] = 0
        
        if "list" not in data:
            logger.warning("响应中缺少 list 字段，使用空列表")
            data["list"] = []
        
        # 转换为 ProductList 对象
        product_list = ProductList.from_api_response(data, page_no=page_no, page_size=page_size)
        
        logger.info(
            f"成功获取商品列表：total={product_list.total}, "
            f"page={product_list.page_no}/{product_list.total_pages}, "
            f"items={len(product_list.list)}"
        )
        
        return product_list
        
    except XianjiaException:
        raise
    except Exception as e:
        logger.error(f"查询商品列表异常：{e}")
        raise ResponseError(f"解析商品列表失败：{str(e)}")


async def list_products_all(
    client: XianjiaClient,
    update_time: Optional[datetime] = None,
    product_status: Optional[ProductPublishStatus] = None,
    page_size: int = 100,
    max_pages: Optional[int] = None
) -> List[ProductListItem]:
    """
    查询所有符合条件的商品（自动分页）
    
    自动遍历所有分页，返回全部符合条件的商品列表。
    适用于需要获取全部数据的场景。
    
    Args:
        client: 闲管家 API 客户端实例
        update_time: 更新时间筛选，可选
        product_status: 商品状态筛选，可选
        page_size: 每页数量，默认 100
        max_pages: 最大页数限制，可选，None 表示不限制
    
    Returns:
        List[ProductListItem]: 所有符合条件的商品列表项
    
    Raises:
        XianjiaException: API 请求失败
        RequestError: 请求参数错误
    
    Example:
        >>> import asyncio
        >>> from xianjia_client.models.product import ProductPublishStatus
        >>> 
        >>> async def main():
        ...     config = Config(app_key="your_app_key", app_secret="your_app_secret")
        ...     async with XianjiaClient(config) as client:
        ...         # 获取所有出售中的商品
        ...         products = await list_products_all(client, product_status=ProductPublishStatus.ONSALE)
        ...         print(f"共获取 {len(products)} 个商品")
        ...         
        ...         # 获取最多 5 页商品
        ...         products = await list_products_all(client, max_pages=5)
        >>> 
        >>> asyncio.run(main())
    
    Note:
        - 此方法会自动发起多次 API 请求，注意 API 调用频率限制
        - 建议设置 max_pages 限制最大请求页数
    """
    all_items = []
    current_page = 1
    
    logger.info(f"开始获取所有商品：page_size={page_size}, max_pages={max_pages}")
    
    while True:
        # 检查页数限制
        if max_pages and current_page > max_pages:
            logger.info(f"已达到最大页数限制：{max_pages}")
            break
        
        # 查询当前页
        result = await list_products(
            client=client,
            update_time=update_time,
            product_status=product_status,
            page_no=current_page,
            page_size=page_size
        )
        
        # 添加当前页数据
        all_items.extend(result.list)
        logger.debug(f"第 {current_page} 页：获取 {len(result.list)} 个商品")
        
        # 检查是否有下一页
        if not result.has_next_page or len(result.list) == 0:
            logger.info(f"获取完成：共 {len(all_items)} 个商品")
            break
        
        current_page += 1
        
        # 避免过快请求，添加小延迟
        await asyncio.sleep(0.1)
    
    return all_items


async def search_products(
    client: XianjiaClient,
    keyword: str,
    update_time: Optional[datetime] = None,
    product_status: Optional[ProductPublishStatus] = None,
    page_no: int = 1,
    page_size: int = 20
) -> ProductList:
    """
    搜索商品
    
    根据关键词搜索商品，支持时间范围和状态筛选。
    
    Args:
        client: 闲管家 API 客户端实例
        keyword: 搜索关键词（商品标题中包含该关键词）
        update_time: 更新时间筛选，可选
        product_status: 商品状态筛选，可选
        page_no: 页码，默认 1
        page_size: 每页数量，默认 20
    
    Returns:
        ProductList: 商品列表响应对象
    
    Raises:
        XianjiaException: API 请求失败
        RequestError: 请求参数错误
    
    Example:
        >>> import asyncio
        >>> from xianjia_client.models.product import ProductPublishStatus
        >>> 
        >>> async def main():
        ...     config = Config(app_key="your_app_key", app_secret="your_app_secret")
        ...     async with XianjiaClient(config) as client:
        ...         # 搜索标题包含"手机"的出售中商品
        ...         result = await search_products(client, keyword="手机", product_status=ProductPublishStatus.ONSALE)
        ...         for item in result.list:
        ...             print(f"{item.title} - ¥{item.price}")
        >>> 
        >>> asyncio.run(main())
    """
    if not keyword or not isinstance(keyword, str):
        raise RequestError("keyword 必须是非空字符串")
    
    logger.info(f"搜索商品：keyword={keyword}, page_no={page_no}")
    
    try:
        # 构建 API 请求参数
        api_path = "/item/search"
        params = {
            "keyword": keyword,
            "page_no": page_no,
            "page_size": page_size
        }
        
        # 添加时间筛选
        if update_time:
            params["start_update_time"] = int(update_time.timestamp() * 1000)
        
        # 添加状态筛选
        if product_status and product_status != ProductPublishStatus.ALL:
            params["item_status"] = product_status.value
        
        # 发送请求
        response = await client.get(api_path, params=params)
        
        # 检查响应
        if not response:
            raise ResponseError("API 响应为空")
        
        code = response.get("code", response.get("error_code", 0))
        msg = response.get("message", response.get("msg", response.get("error", "Unknown error")))
        data = response.get("data", {})
        
        # 检查错误
        if code and code != 0 and code != "0":
            logger.error(f"API 返回错误：code={code}, msg={msg}")
            raise XianjiaException(f"搜索商品失败：{msg}", code=str(code))
        
        # 转换为 ProductList 对象
        product_list = ProductList.from_api_response(data, page_no=page_no, page_size=page_size)
        
        logger.info(f"搜索完成：找到 {product_list.total} 个商品")
        return product_list
        
    except XianjiaException:
        raise
    except Exception as e:
        logger.error(f"搜索商品异常：{e}")
        raise ResponseError(f"搜索商品失败：{str(e)}")
