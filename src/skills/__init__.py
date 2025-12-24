"""Skills 模块 - 实现基于 SKILL.md 的动态加载能力。

公共 API:
- SkillsMiddleware: 将 skills 集成到 agent 执行的中间件
- SkillMetadata: skill 元数据的类型定义
- SkillExecutor: skill 脚本执行器
- list_skills: 列出所有可用 skills

所有其他组件是内部实现细节。
"""

from .load import (
    SkillMetadata,
    list_skills,
    MAX_SKILL_NAME_LENGTH,
    MAX_SKILL_DESCRIPTION_LENGTH,
)
from .middleware import SkillsMiddleware
from .executor import SkillExecutor

__all__ = [
    "SkillMetadata",
    "SkillsMiddleware",
    "SkillExecutor",
    "list_skills",
    "MAX_SKILL_NAME_LENGTH",
    "MAX_SKILL_DESCRIPTION_LENGTH",
]
