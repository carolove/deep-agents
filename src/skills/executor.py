"""Skill 执行器 - 追踪和执行 skill 脚本。

提供 skill 脚本执行的包装器，包含详细的日志记录和追踪。
"""

import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logger import get_logger

logger = get_logger("skills.executor")


class SkillExecutor:
    """Skill 脚本执行器，提供执行追踪和日志记录。"""

    def __init__(self, skill_name: str, skill_path: str):
        """
        初始化 Skill 执行器。
        
        Args:
            skill_name: Skill 名称
            skill_path: SKILL.md 文件路径
        """
        self.skill_name = skill_name
        self.skill_path = Path(skill_path)
        self.skill_dir = self.skill_path.parent
        
        logger.info(f"Skill 执行器初始化: {skill_name}")
        logger.debug(f"  Skill 目录: {self.skill_dir}")

    def execute_script(
        self,
        script_name: str,
        args: Optional[List[str]] = None,
        input_data: Optional[str] = None,
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        执行 skill 目录中的脚本。
        
        Args:
            script_name: 脚本文件名
            args: 命令行参数列表
            input_data: 传递给脚本的标准输入
            timeout: 超时时间（秒）
            env: 环境变量
            
        Returns:
            执行结果字典，包含 stdout, stderr, returncode, duration
        """
        script_path = self.skill_dir / script_name
        
        if not script_path.exists():
            error_msg = f"脚本不存在: {script_path}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "stdout": "",
                "stderr": "",
                "returncode": -1,
                "duration": 0,
            }
        
        # 构建命令
        cmd = ["python", str(script_path)]
        if args:
            cmd.extend(args)
        
        logger.info(f"[{self.skill_name}] 执行脚本: {script_name}")
        logger.info(f"[{self.skill_name}] 命令: {' '.join(cmd)}")
        if args:
            logger.info(f"[{self.skill_name}] 参数: {args}")
        if input_data:
            logger.debug(f"[{self.skill_name}] 输入数据: {input_data[:100]}...")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.skill_dir),
                input=input_data,
                env=env,
            )
            
            duration = time.time() - start_time
            
            # 记录输出
            logger.info(f"[{self.skill_name}] 执行完成 (耗时 {duration:.2f}s, 返回码 {result.returncode})")
            
            if result.stdout:
                stdout_preview = result.stdout[:500]
                logger.info(f"[{self.skill_name}] 标准输出:\n{stdout_preview}")
                if len(result.stdout) > 500:
                    logger.debug(f"[{self.skill_name}] (输出已截断，共 {len(result.stdout)} 字符)")
            
            if result.stderr:
                logger.warning(f"[{self.skill_name}] 标准错误:\n{result.stderr[:500]}")
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "duration": duration,
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            error_msg = f"脚本执行超时 ({timeout}s)"
            logger.error(f"[{self.skill_name}] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "stdout": "",
                "stderr": "",
                "returncode": -1,
                "duration": duration,
            }
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"脚本执行失败: {str(e)}"
            logger.error(f"[{self.skill_name}] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "stdout": "",
                "stderr": "",
                "returncode": -1,
                "duration": duration,
            }

    def list_scripts(self) -> List[str]:
        """列出 skill 目录中的所有 Python 脚本。"""
        scripts = [f.name for f in self.skill_dir.glob("*.py")]
        logger.debug(f"[{self.skill_name}] 可用脚本: {scripts}")
        return scripts

