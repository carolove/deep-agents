#!/usr/bin/env python3
"""Calculator skill - 计算数学表达式和获取当前时间。

用法:
    python calculator.py "2 + 2"
    python calculator.py "10 * 5 + 3"
    python calculator.py --time
"""

import argparse
import sys
from datetime import datetime


def calculate(expression: str) -> str:
    """
    计算数学表达式
    
    Args:
        expression: 数学表达式,例如 "2 + 2" 或 "10 * 5"
        
    Returns:
        计算结果
    """
    try:
        # 使用 eval 计算表达式(仅用于演示,生产环境应使用更安全的方法)
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


def get_current_time() -> str:
    """
    获取当前时间
    
    Returns:
        当前时间字符串
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description="Calculator skill")
    parser.add_argument("expression", nargs="?", help="数学表达式")
    parser.add_argument("--time", action="store_true", help="获取当前时间")
    
    args = parser.parse_args()
    
    if args.time:
        print(get_current_time())
    elif args.expression:
        print(calculate(args.expression))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

