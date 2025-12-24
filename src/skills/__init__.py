"""Skills 模块 - 实现基于 SKILL.md 的动态加载能力。

公共 API:
- SkillsMiddleware: AgentMiddleware 子类，将 skills 集成到 agent 执行
  - 自动实现 before_agent() 加载 skills
  - 自动实现 wrap_model_call() 注入 system prompt
- SkillMetadata: skill 元数据的类型定义
- list_skills: 列出所有可用 skills

Anthropic Skills 渐进式披露模式:
1. SkillsMiddleware.before_agent() 在每次交互前加载 skills 元数据
2. SkillsMiddleware.wrap_model_call() 将 skills 注入 system prompt
3. Agent 使用框架内置的 read_file 工具读取 SKILL.md 获取完整说明
4. Agent 使用框架内置的 execute 工具执行 skill 脚本

使用方式:
    from src.skills import SkillsMiddleware

    middleware = SkillsMiddleware(
        skills_dir=Path.home() / ".deep-agents/agent/skills",
        assistant_id="agent",
        project_skills_dir=project_root / ".deep-agents/skills",
    )

    agent = create_deep_agent(
        model=model,
        middleware=[middleware],  # 传入 middleware 参数
        ...
    )
"""

from .load import (
    SkillMetadata,
    list_skills,
    MAX_SKILL_NAME_LENGTH,
    MAX_SKILL_DESCRIPTION_LENGTH,
)
from .middleware import SkillsMiddleware

__all__ = [
    "SkillMetadata",
    "SkillsMiddleware",
    "list_skills",
    "MAX_SKILL_NAME_LENGTH",
    "MAX_SKILL_DESCRIPTION_LENGTH",
]
