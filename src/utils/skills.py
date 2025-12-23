"""Skills 管理模块"""
import importlib
import inspect
from pathlib import Path
from typing import List, Callable, Optional
from langchain_core.tools import tool

from ..core.logger import get_logger

logger = get_logger("skills")


class SkillManager:
    """Skills 管理器"""
    
    def __init__(self, skills_dir: str = "src/skills"):
        """
        初始化 Skills 管理器
        
        Args:
            skills_dir: skills 目录路径
        """
        self.skills_dir = Path(skills_dir)
        self.skills: List[Callable] = []
        logger.info(f"Skills 管理器初始化: dir={skills_dir}")
    
    def load_skills(self) -> List[Callable]:
        """
        加载所有 skills
        
        Returns:
            skills 列表
        """
        if not self.skills_dir.exists():
            logger.warning(f"Skills 目录不存在: {self.skills_dir}")
            return []
        
        # 查找所有 Python 文件
        skill_files = list(self.skills_dir.glob("*.py"))
        skill_files = [f for f in skill_files if f.name != "__init__.py"]
        
        logger.info(f"发现 {len(skill_files)} 个 skill 文件")
        
        for skill_file in skill_files:
            try:
                self._load_skill_file(skill_file)
            except Exception as e:
                logger.error(f"加载 skill 文件失败 {skill_file}: {e}")
        
        logger.info(f"成功加载 {len(self.skills)} 个 skills")
        return self.skills
    
    def _load_skill_file(self, skill_file: Path) -> None:
        """
        加载单个 skill 文件
        
        Args:
            skill_file: skill 文件路径
        """
        # 构建模块名
        module_name = f"src.skills.{skill_file.stem}"
        
        try:
            # 动态导入模块
            module = importlib.import_module(module_name)
            
            # 查找所有函数
            for name, obj in inspect.getmembers(module):
                # 检查是否是工具函数
                if callable(obj) and hasattr(obj, "__wrapped__"):
                    # 这是一个被 @tool 装饰的函数
                    self.skills.append(obj)
                    logger.debug(f"加载 skill: {name} from {skill_file.name}")
                elif callable(obj) and not name.startswith("_"):
                    # 普通函数,尝试包装为 tool
                    if inspect.isfunction(obj) and obj.__module__ == module.__name__:
                        # 只包装定义在当前模块的函数
                        try:
                            wrapped_tool = tool(obj)
                            self.skills.append(wrapped_tool)
                            logger.debug(f"包装并加载 skill: {name} from {skill_file.name}")
                        except Exception as e:
                            logger.warning(f"无法包装函数 {name}: {e}")
        
        except Exception as e:
            logger.error(f"导入模块失败 {module_name}: {e}")
            raise
    
    def get_skill(self, name: str) -> Optional[Callable]:
        """
        根据名称获取 skill
        
        Args:
            name: skill 名称
            
        Returns:
            skill 函数或 None
        """
        for skill in self.skills:
            if hasattr(skill, "name") and skill.name == name:
                return skill
            elif hasattr(skill, "__name__") and skill.__name__ == name:
                return skill
        return None
    
    def list_skills(self) -> List[str]:
        """
        列出所有 skill 名称
        
        Returns:
            skill 名称列表
        """
        names = []
        for skill in self.skills:
            if hasattr(skill, "name"):
                names.append(skill.name)
            elif hasattr(skill, "__name__"):
                names.append(skill.__name__)
        return names


def load_skills(skills_dir: str = "src/skills") -> List[Callable]:
    """
    便捷函数:加载所有 skills
    
    Args:
        skills_dir: skills 目录路径
        
    Returns:
        skills 列表
    """
    manager = SkillManager(skills_dir)
    return manager.load_skills()

