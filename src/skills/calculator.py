"""计算器 Skill"""
from langchain_core.tools import tool
from loguru import logger


@tool
def calculator(expression: str) -> str:
    """
    计算数学表达式

    Args:
        expression: 数学表达式,例如 "2 + 2" 或 "10 * 5"

    Returns:
        计算结果
    """
    logger.info(f"🧮 开始计算: expression='{expression}'")

    try:
        # 使用 eval 计算表达式(仅用于演示,生产环境应使用更安全的方法)
        result = eval(expression, {"__builtins__": {}}, {})
        result_str = f"{expression} = {result}"
        logger.info(f"✅ 计算成功: {result_str}")
        return result_str
    except Exception as e:
        error_msg = f"计算错误: {str(e)}"
        logger.error(f"❌ 计算失败: expression='{expression}', error={e}")
        return error_msg


@tool
def get_current_time() -> str:
    """
    获取当前时间

    Returns:
        当前时间字符串
    """
    logger.info(f"🕐 获取当前时间")
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"✅ 当前时间: {current_time}")
    return current_time

