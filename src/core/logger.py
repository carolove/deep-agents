"""日志管理模块"""
import sys
from pathlib import Path
from typing import Optional
from loguru import logger


_logger_initialized = False


def setup_logger(
    log_file: str = "logs/app.log",
    log_level: str = "INFO",
    rotation: str = "100 MB",
    retention: str = "30 days",
) -> None:
    """
    设置日志系统
    
    Args:
        log_file: 日志文件路径
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        rotation: 日志轮转大小
        retention: 日志保留时间
    """
    global _logger_initialized
    
    if _logger_initialized:
        return
    
    # 移除默认的 handler
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level.upper(),
        colorize=True,
    )
    
    # 添加文件输出
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level.upper(),
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
    )
    
    _logger_initialized = True
    logger.info(f"日志系统初始化完成: level={log_level}, file={log_file}")


def get_logger(name: Optional[str] = None):
    """
    获取 logger 实例
    
    Args:
        name: logger 名称
        
    Returns:
        logger 实例
    """
    if name:
        return logger.bind(name=name)
    return logger

