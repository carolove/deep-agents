"""网络搜索 Skill"""
import os
import time
from typing import Optional
from langchain_core.tools import tool
from loguru import logger

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False


@tool
def internet_search(query: str, max_results: int = 5) -> str:
    """
    使用 Tavily 进行网络搜索

    Args:
        query: 搜索查询
        max_results: 最大结果数量

    Returns:
        搜索结果
    """
    logger.info(f"🔍 开始网络搜索: query='{query}', max_results={max_results}")

    if not TAVILY_AVAILABLE:
        error_msg = "错误: Tavily 未安装,请运行 'pip install tavily-python'"
        logger.error(f"❌ {error_msg}")
        return error_msg

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        error_msg = "错误: 未设置 TAVILY_API_KEY 环境变量"
        logger.error(f"❌ {error_msg}")
        return error_msg

    # 隐藏 API key 的部分字符用于日志
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
    logger.debug(f"使用 API Key: {masked_key}")

    try:
        # 记录开始时间
        start_time = time.time()

        logger.info(f"📡 调用 Tavily API...")
        client = TavilyClient(api_key=api_key)
        results = client.search(query, max_results=max_results)

        # 计算耗时
        duration = time.time() - start_time

        # 记录响应信息
        result_count = len(results.get("results", []))
        logger.info(f"✅ Tavily API 调用成功: 耗时={duration:.2f}s, 结果数={result_count}")

        # 记录详细的结果信息
        if result_count > 0:
            logger.debug(f"搜索结果详情:")
            for i, result in enumerate(results.get("results", []), 1):
                title = result.get('title', 'N/A')
                url = result.get('url', 'N/A')
                logger.debug(f"  [{i}] {title}")
                logger.debug(f"      URL: {url}")
        else:
            logger.warning(f"⚠️  未找到相关结果")

        # 格式化结果
        formatted_results = []
        for i, result in enumerate(results.get("results", []), 1):
            formatted_results.append(
                f"{i}. {result.get('title', 'N/A')}\n"
                f"   URL: {result.get('url', 'N/A')}\n"
                f"   摘要: {result.get('content', 'N/A')}\n"
            )

        final_result = "\n".join(formatted_results) if formatted_results else "未找到相关结果"
        logger.info(f"🎯 网络搜索完成: 返回 {len(formatted_results)} 条结果")
        return final_result

    except Exception as e:
        error_msg = f"搜索失败: {str(e)}"
        logger.error(f"❌ Tavily API 调用失败: {e}")
        logger.exception("详细错误信息:")
        return error_msg

