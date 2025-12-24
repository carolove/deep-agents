#!/usr/bin/env python3
"""Web Search skill - 使用 Tavily API 进行网络搜索。

用法:
    python web_search.py "search query"
    python web_search.py "search query" --max-results 5
"""

import argparse
import os
import sys
import time


def internet_search(query: str, max_results: int = 5) -> str:
    """
    使用 Tavily 进行网络搜索
    
    Args:
        query: 搜索查询
        max_results: 最大结果数量
        
    Returns:
        搜索结果
    """
    try:
        from tavily import TavilyClient
    except ImportError:
        return "错误: Tavily 未安装,请运行 'pip install tavily-python'"
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "错误: 未设置 TAVILY_API_KEY 环境变量"
    
    try:
        start_time = time.time()
        
        client = TavilyClient(api_key=api_key)
        results = client.search(query, max_results=max_results)
        
        duration = time.time() - start_time
        result_count = len(results.get("results", []))
        
        # 格式化结果
        formatted_results = []
        for i, result in enumerate(results.get("results", []), 1):
            formatted_results.append(
                f"{i}. {result.get('title', 'N/A')}\n"
                f"   URL: {result.get('url', 'N/A')}\n"
                f"   摘要: {result.get('content', 'N/A')}\n"
            )
        
        if formatted_results:
            header = f"搜索完成 (耗时 {duration:.2f}s, 共 {result_count} 条结果):\n\n"
            return header + "\n".join(formatted_results)
        else:
            return "未找到相关结果"
            
    except Exception as e:
        return f"搜索失败: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Web Search skill")
    parser.add_argument("query", help="搜索查询")
    parser.add_argument(
        "--max-results", 
        type=int, 
        default=5, 
        help="最大结果数量 (默认: 5)"
    )
    
    args = parser.parse_args()
    print(internet_search(args.query, args.max_results))


if __name__ == "__main__":
    main()

