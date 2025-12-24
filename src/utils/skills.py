"""Skills 管理模块 - 基于 SKILL.md 的动态加载能力。

目录结构示例:
skills/
├── calculator/
│   ├── SKILL.md        # 必需: 包含 YAML frontmatter 和说明
│   ├── calculator.py   # 可选: 支持脚本
│   └── config.json     # 可选: 配置文件
├── web-search/
│   └── SKILL.md
"""

from pathlib import Path
from typing import List, Optional

from ..core.logger import get_logger
from ..skills import SkillMetadata, SkillsMiddleware, list_skills as list_skill_md

logger = get_logger("skills")


class SkillManager:
    """Skills 管理器 - 基于 SKILL.md 的动态加载"""

    def __init__(
        self,
        user_skills_dir: Optional[str] = None,
        project_skills_dir: Optional[str] = None,
        assistant_id: str = "agent",
    ):
        """
        初始化 Skills 管理器

        Args:
            user_skills_dir: 用户级 SKILL.md 目录路径
            project_skills_dir: 项目级 SKILL.md 目录路径
            assistant_id: Agent 标识符
        """
        self.user_skills_dir = Path(user_skills_dir).expanduser() if user_skills_dir else None
        self.project_skills_dir = Path(project_skills_dir).expanduser() if project_skills_dir else None
        self.assistant_id = assistant_id

        # 存储加载的 skills
        self.skill_metadata: List[SkillMetadata] = []

        # Skills 中间件
        self._middleware: Optional[SkillsMiddleware] = None

        logger.info(f"Skills 管理器初始化: assistant_id={assistant_id}")

    def load_skills(self) -> List[SkillMetadata]:
        """
        加载所有 SKILL.md skills

        Returns:
            SkillMetadata 列表
        """
        self.skill_metadata = list_skill_md(
            user_skills_dir=self.user_skills_dir,
            project_skills_dir=self.project_skills_dir,
        )
        logger.info(f"成功加载 {len(self.skill_metadata)} 个 skills")
        return self.skill_metadata

    def get_middleware(self) -> SkillsMiddleware:
        """获取 Skills 中间件实例"""
        if self._middleware is None:
            self._middleware = SkillsMiddleware(
                skills_dir=self.user_skills_dir or Path.home() / f".deep-agents/{self.assistant_id}/skills",
                assistant_id=self.assistant_id,
                project_skills_dir=self.project_skills_dir,
            )
        return self._middleware

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """根据名称获取 skill 元数据"""
        for skill in self.skill_metadata:
            if skill["name"] == name:
                return skill
        return None

    def list_skills(self) -> List[str]:
        """列出所有 skill 名称"""
        return [skill["name"] for skill in self.skill_metadata]


def load_skills(
    user_skills_dir: Optional[str] = None,
    project_skills_dir: Optional[str] = None,
) -> List[SkillMetadata]:
    """
    便捷函数: 加载所有 SKILL.md skills

    Args:
        user_skills_dir: 用户级 skills 目录
        project_skills_dir: 项目级 skills 目录

    Returns:
        SkillMetadata 列表
    """
    user_path = Path(user_skills_dir).expanduser() if user_skills_dir else None
    project_path = Path(project_skills_dir).expanduser() if project_skills_dir else None

    return list_skill_md(
        user_skills_dir=user_path,
        project_skills_dir=project_path,
    )
