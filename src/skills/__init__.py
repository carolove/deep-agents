"""Skills 模块 - 实现基于 SKILL.md 的动态加载能力。

公共 API:
- SkillsMiddleware: 将 skills 集成到 agent 执行的中间件
  - enhance_system_prompt(): 增强系统提示词
  - get_tools(): 获取 skills 需要的文件系统工具
- SkillMetadata: skill 元数据的类型定义
- SkillExecutor: skill 脚本执行器
- list_skills: 列出所有可用 skills

Anthropic Skills 模式:
1. 在启动时加载 skills 元数据 (name + description)
2. 将元数据注入系统提示词让 Agent 知道有哪些 skills
3. Agent 使用 read_file 工具读取 SKILL.md 获取完整说明
4. Agent 使用 bash_execute 工具执行 skill 脚本
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
