"""计算器 Skill"""
from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
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


@tool
def get_current_time() -> str:
    """
    获取当前时间
    
    Returns:
        当前时间字符串
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

