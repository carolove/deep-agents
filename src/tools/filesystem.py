"""文件系统工具 - 提供 Agent 访问文件系统的能力。

这些工具让 Agent 能够:
1. 读取文件内容 (包括 SKILL.md)
2. 写入文件
3. 列出目录内容
4. 使用 glob 模式搜索文件
5. 执行 bash 命令 (包括 skill 脚本)

这是实现 Anthropic Skills 渐进式披露模式的关键组件。
"""

import subprocess
import os
from pathlib import Path
from typing import List, Optional
import glob as glob_module

from langchain_core.tools import tool

from ..core.logger import get_logger

logger = get_logger("tools.filesystem")

# 允许访问的基础目录（安全限制）
# 可以通过环境变量配置
ALLOWED_BASE_DIRS: List[str] = []


def _init_allowed_dirs():
    """初始化允许访问的目录列表。"""
    global ALLOWED_BASE_DIRS
    if ALLOWED_BASE_DIRS:
        return
    
    # 默认允许当前工作目录和用户 home 目录下的 .deep-agents
    cwd = os.getcwd()
    home = str(Path.home())
    
    ALLOWED_BASE_DIRS = [
        cwd,
        os.path.join(home, ".deep-agents"),
    ]
    
    # 从环境变量添加额外允许的目录
    extra_dirs = os.environ.get("DEEP_AGENTS_ALLOWED_DIRS", "")
    if extra_dirs:
        ALLOWED_BASE_DIRS.extend(extra_dirs.split(":"))
    
    logger.info(f"文件系统工具允许访问的目录: {ALLOWED_BASE_DIRS}")


def _is_path_allowed(path: str) -> bool:
    """检查路径是否在允许的目录范围内。"""
    _init_allowed_dirs()
    
    try:
        resolved = str(Path(path).resolve())
        for allowed in ALLOWED_BASE_DIRS:
            allowed_resolved = str(Path(allowed).resolve())
            if resolved.startswith(allowed_resolved):
                return True
        return False
    except Exception:
        return False


@tool
def read_file(file_path: str) -> str:
    """读取文件内容。
    
    用于读取 SKILL.md 文件获取完整的 skill 说明，
    或读取 skill 的 references/ 目录中的参考文档。
    
    Args:
        file_path: 文件的绝对路径或相对路径
        
    Returns:
        文件内容字符串，或错误消息
    """
    logger.info(f"读取文件: {file_path}")
    
    try:
        path = Path(file_path).resolve()
        
        if not _is_path_allowed(str(path)):
            error_msg = f"路径不在允许的访问范围内: {file_path}"
            logger.warning(error_msg)
            return f"错误: {error_msg}"
        
        if not path.exists():
            return f"错误: 文件不存在: {file_path}"
        
        if not path.is_file():
            return f"错误: 不是文件: {file_path}"
        
        content = path.read_text(encoding="utf-8")
        logger.info(f"成功读取文件: {file_path} ({len(content)} 字符)")
        return content
        
    except Exception as e:
        error_msg = f"读取文件失败: {str(e)}"
        logger.error(error_msg)
        return f"错误: {error_msg}"


@tool
def write_file(file_path: str, content: str) -> str:
    """写入内容到文件。
    
    Args:
        file_path: 文件的绝对路径或相对路径
        content: 要写入的内容
        
    Returns:
        成功消息或错误消息
    """
    logger.info(f"写入文件: {file_path}")
    
    try:
        path = Path(file_path).resolve()
        
        if not _is_path_allowed(str(path)):
            error_msg = f"路径不在允许的访问范围内: {file_path}"
            logger.warning(error_msg)
            return f"错误: {error_msg}"
        
        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        path.write_text(content, encoding="utf-8")
        logger.info(f"成功写入文件: {file_path} ({len(content)} 字符)")
        return f"成功写入文件: {file_path}"
        
    except Exception as e:
        error_msg = f"写入文件失败: {str(e)}"
        logger.error(error_msg)
        return f"错误: {error_msg}"


@tool
def list_directory(dir_path: str, recursive: bool = False) -> str:
    """列出目录内容。
    
    Args:
        dir_path: 目录的绝对路径或相对路径
        recursive: 是否递归列出子目录
        
    Returns:
        目录内容列表，或错误消息
    """
    logger.info(f"列出目录: {dir_path} (recursive={recursive})")
    
    try:
        path = Path(dir_path).resolve()
        
        if not _is_path_allowed(str(path)):
            error_msg = f"路径不在允许的访问范围内: {dir_path}"
            logger.warning(error_msg)
            return f"错误: {error_msg}"
        
        if not path.exists():
            return f"错误: 目录不存在: {dir_path}"
        
        if not path.is_dir():
            return f"错误: 不是目录: {dir_path}"
        
        items = []
        if recursive:
            for item in path.rglob("*"):
                rel_path = item.relative_to(path)
                item_type = "目录" if item.is_dir() else "文件"
                items.append(f"[{item_type}] {rel_path}")
        else:
            for item in sorted(path.iterdir()):
                item_type = "目录" if item.is_dir() else "文件"
                items.append(f"[{item_type}] {item.name}")
        
        result = "\n".join(items) if items else "(空目录)"
        logger.info(f"列出 {len(items)} 个项目")
        return result

    except Exception as e:
        error_msg = f"列出目录失败: {str(e)}"
        logger.error(error_msg)
        return f"错误: {error_msg}"


@tool
def glob_files(pattern: str, base_dir: Optional[str] = None) -> str:
    """使用 glob 模式搜索文件。

    Args:
        pattern: glob 模式，如 "*.py" 或 "**/*.md"
        base_dir: 搜索的基础目录，默认为当前工作目录

    Returns:
        匹配的文件列表，或错误消息
    """
    base = base_dir or os.getcwd()
    logger.info(f"Glob 搜索: {pattern} (base={base})")

    try:
        base_path = Path(base).resolve()

        if not _is_path_allowed(str(base_path)):
            error_msg = f"路径不在允许的访问范围内: {base}"
            logger.warning(error_msg)
            return f"错误: {error_msg}"

        if not base_path.exists():
            return f"错误: 目录不存在: {base}"

        # 使用 pathlib 的 glob
        matches = list(base_path.glob(pattern))

        # 过滤只保留允许访问的路径
        safe_matches = [str(m) for m in matches if _is_path_allowed(str(m))]

        result = "\n".join(safe_matches) if safe_matches else "(无匹配)"
        logger.info(f"Glob 匹配 {len(safe_matches)} 个文件")
        return result

    except Exception as e:
        error_msg = f"Glob 搜索失败: {str(e)}"
        logger.error(error_msg)
        return f"错误: {error_msg}"


@tool
def bash_execute(
    command: str,
    working_dir: Optional[str] = None,
    timeout: int = 300,
) -> str:
    """执行 bash 命令。

    用于执行 skill 脚本，如:
    python src/skills/calculator/calculator.py "2 + 2"

    Args:
        command: 要执行的 bash 命令
        working_dir: 工作目录，默认为当前目录
        timeout: 超时时间（秒），默认 300 秒

    Returns:
        命令输出（stdout + stderr），或错误消息
    """
    cwd = working_dir or os.getcwd()
    logger.info(f"执行命令: {command}")
    logger.info(f"工作目录: {cwd}")

    try:
        cwd_path = Path(cwd).resolve()

        if not _is_path_allowed(str(cwd_path)):
            error_msg = f"工作目录不在允许的访问范围内: {cwd}"
            logger.warning(error_msg)
            return f"错误: {error_msg}"

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd_path),
        )

        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(f"[stderr]\n{result.stderr}")

        output = "\n".join(output_parts) if output_parts else "(无输出)"

        if result.returncode != 0:
            output = f"[返回码: {result.returncode}]\n{output}"

        logger.info(f"命令执行完成: 返回码={result.returncode}")
        return output

    except subprocess.TimeoutExpired:
        error_msg = f"命令执行超时 ({timeout}s)"
        logger.error(error_msg)
        return f"错误: {error_msg}"
    except Exception as e:
        error_msg = f"命令执行失败: {str(e)}"
        logger.error(error_msg)
        return f"错误: {error_msg}"


def get_filesystem_tools() -> list:
    """获取所有文件系统工具列表。

    Returns:
        LangChain 工具列表，可直接传递给 Agent
    """
    return [
        read_file,
        write_file,
        list_directory,
        glob_files,
        bash_execute,
    ]

