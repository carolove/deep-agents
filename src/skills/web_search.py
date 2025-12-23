"""网络搜索 Skill"""
import os
from typing import Optional
from langchain_core.tools import tool

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
    if not TAVILY_AVAILABLE:
        return "错误: Tavily 未安装,请运行 'pip install tavily-python'"
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "错误: 未设置 TAVILY_API_KEY 环境变量"
    
    try:
        client = TavilyClient(api_key=api_key)
        results = client.search(query, max_results=max_results)
        
        # 格式化结果
        formatted_results = []
        for i, result in enumerate(results.get("results", []), 1):
            formatted_results.append(
                f"{i}. {result.get('title', 'N/A')}\n"
                f"   URL: {result.get('url', 'N/A')}\n"
                f"   摘要: {result.get('content', 'N/A')}\n"
            )
        
        return "\n".join(formatted_results) if formatted_results else "未找到相关结果"
    
    except Exception as e:
        return f"搜索失败: {str(e)}"

