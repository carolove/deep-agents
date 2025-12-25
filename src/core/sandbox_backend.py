"""Sandbox Backend - 支持命令执行的文件系统后端。

扩展 FilesystemBackend 以支持 execute 方法，使 Agent 能够执行 shell 命令。
"""
import asyncio
import subprocess
from pathlib import Path
from typing import Optional

from deepagents.backends import FilesystemBackend
from deepagents.backends.protocol import SandboxBackendProtocol, ExecuteResponse


class SandboxBackend(FilesystemBackend, SandboxBackendProtocol):
    """支持命令执行的文件系统后端。
    
    继承 FilesystemBackend 的所有文件操作功能，
    并实现 SandboxBackendProtocol 的 execute 方法。
    
    Args:
        root_dir: 工作目录，所有路径相对于此目录解析
        max_output_length: 命令输出的最大长度（字节），超出将被截断
        timeout: 命令执行超时时间（秒）
    """
    
    def __init__(
        self,
        root_dir: Optional[Path] = None,
        max_output_length: int = 100_000,
        timeout: int = 60,
        **kwargs
    ):
        super().__init__(root_dir=root_dir, **kwargs)
        self.max_output_length = max_output_length
        self.timeout = timeout
    
    def execute(self, command: str) -> ExecuteResponse:
        """执行 shell 命令。
        
        Args:
            command: 要执行的 shell 命令
            
        Returns:
            ExecuteResponse 包含:
            - output: 命令的 stdout 和 stderr 合并输出
            - exit_code: 命令的退出码
            - truncated: 输出是否被截断
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            # 合并 stdout 和 stderr
            output = result.stdout
            if result.stderr:
                output += "\n[STDERR]\n" + result.stderr
            
            # 检查是否需要截断
            truncated = len(output) > self.max_output_length
            if truncated:
                output = output[:self.max_output_length] + "\n... [输出已截断]"
            
            return ExecuteResponse(
                output=output,
                exit_code=result.returncode,
                truncated=truncated,
            )
        except subprocess.TimeoutExpired:
            return ExecuteResponse(
                output=f"Error: 命令执行超时 ({self.timeout}秒)",
                exit_code=-1,
                truncated=False,
            )
        except Exception as e:
            return ExecuteResponse(
                output=f"Error: {type(e).__name__}: {str(e)}",
                exit_code=-1,
                truncated=False,
            )
    
    async def aexecute(self, command: str) -> ExecuteResponse:
        """异步执行 shell 命令。"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, command)

