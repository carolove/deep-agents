"""Middleware 用于加载和将 agent skills 暴露给系统提示词。

这个中间件实现 Anthropic 的 "Agent Skills" 模式，采用渐进式披露:
1. 在每次 agent 执行前从 SKILL.md 文件解析 YAML frontmatter (before_agent)
2. 在每次 model 调用时将 skills 信息注入系统提示词 (wrap_model_call)
3. Agent 使用框架内置的 read_file 工具读取完整的 SKILL.md 内容
4. Agent 使用框架内置的 execute 工具执行 skill 中的脚本

Skills 目录结构 (每个 agent + 项目):
用户级: ~/.deep-agents/{AGENT_NAME}/skills/
项目级: {PROJECT_ROOT}/.deep-agents/skills/

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

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import List, NotRequired, TypedDict, cast

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
)
from langgraph.runtime import Runtime

from .load import SkillMetadata, list_skills
from ..core.logger import get_logger

logger = get_logger("skills.middleware")


# Skills 系统文档
SKILLS_SYSTEM_PROMPT = """

## Skills 系统

你可以访问一个 skills 库，提供专业能力和领域知识。

{skills_locations}

**可用 Skills:**

{skills_list}

**如何使用 Skills (渐进式披露):**

Skills 遵循**渐进式披露**模式 - 你知道它们存在（上面显示的名称 + 描述），但只有在需要时才阅读完整说明:

1. **识别何时适用 skill**: 检查用户的任务是否匹配任何 skill 的描述
2. **阅读 skill 的完整说明**: 上面的 skill 列表显示了用于 read_file 的确切路径
3. **按照 skill 的说明操作**: SKILL.md 包含分步工作流、最佳实践和示例
4. **访问支持文件**: Skills 可能包含 Python 脚本、配置或参考文档 - 使用绝对路径

**何时使用 Skills:**
- 当用户的请求匹配 skill 的领域时（例如，"研究 X" → web-research skill）
- 当你需要专业知识或结构化工作流时
- 当 skill 为复杂任务提供经过验证的模式时

**Skills 是自文档化的:**
- 每个 SKILL.md 告诉你 skill 做什么以及如何使用它
- 上面的 skill 列表显示每个 skill 的 SKILL.md 文件的完整路径

记住: Skills 是让你更强大和一致的工具。如有疑问，检查是否存在适用于该任务的 skill！
"""


class SkillsState(AgentState):
    """Skills 中间件的状态类型。"""

    skills_metadata: NotRequired[List[SkillMetadata]]
    """已加载的 skill 元数据列表 (name, description, path)。"""


class SkillsStateUpdate(TypedDict):
    """Skills 中间件的状态更新类型。"""

    skills_metadata: List[SkillMetadata]
    """已加载的 skill 元数据列表。"""


class SkillsMiddleware(AgentMiddleware):
    """用于加载和暴露 agent skills 的中间件。

    继承 langchain AgentMiddleware，实现:
    - before_agent(): 在每次 agent 执行前加载 skills 元数据
    - wrap_model_call(): 在每次 model 调用时注入 skills 到 system prompt

    实现 Anthropic 的 agent skills 模式:
    - 在会话开始时从 YAML frontmatter 加载 skills 元数据
    - 将 skills 列表注入系统提示词以便发现
    - Agent 在 skill 相关时读取完整的 SKILL.md 内容（渐进式披露）

    支持用户级和项目级 skills:
    - 用户 skills: ~/.deep-agents/{AGENT_NAME}/skills/
    - 项目 skills: {PROJECT_ROOT}/.deep-agents/skills/
    - 同名的项目 skills 会覆盖用户 skills

    使用框架内置工具:
    - deepagents 的 FilesystemMiddleware 提供 read_file, execute 等工具
    - Agent 使用 read_file 读取 SKILL.md
    - Agent 使用 execute 执行 skill 脚本
    """

    state_schema = SkillsState

    def __init__(
        self,
        *,
        skills_dir: str | Path,
        assistant_id: str = "agent",
        project_skills_dir: str | Path | None = None,
    ) -> None:
        """初始化 skills 中间件。

        Args:
            skills_dir: 用户级 skills 目录的路径。
            assistant_id: Agent 标识符。
            project_skills_dir: 项目级 skills 目录的可选路径。
        """
        self.skills_dir = Path(skills_dir).expanduser().resolve()
        self.assistant_id = assistant_id
        self.project_skills_dir = (
            Path(project_skills_dir).expanduser().resolve() if project_skills_dir else None
        )
        # 使用绝对路径，避免 ~ 符号导致的路径遍历检测问题
        self.user_skills_display = str(self.skills_dir)
        self.system_prompt_template = SKILLS_SYSTEM_PROMPT

        logger.info(f"Skills 中间件初始化: assistant_id={assistant_id}")
        logger.info(f"  用户 skills 目录: {self.skills_dir}")
        if self.project_skills_dir:
            logger.info(f"  项目 skills 目录: {self.project_skills_dir}")

    def _format_skills_locations(self) -> str:
        """格式化 skills 位置用于系统提示词显示。"""
        locations = [f"**用户 Skills**: `{self.user_skills_display}`"]
        if self.project_skills_dir:
            locations.append(
                f"**项目 Skills**: `{self.project_skills_dir}` (覆盖用户 skills)"
            )
        return "\n".join(locations)

    def _format_skills_list(self, skills: List[SkillMetadata]) -> str:
        """格式化 skills 元数据用于系统提示词显示。"""
        if not skills:
            locations = [f"{self.user_skills_display}/"]
            if self.project_skills_dir:
                locations.append(f"{self.project_skills_dir}/")
            return f"(暂无可用 skills。你可以在 {' 或 '.join(locations)} 创建 skills)"

        user_skills = [s for s in skills if s["source"] == "user"]
        project_skills = [s for s in skills if s["source"] == "project"]

        lines = []

        if user_skills:
            lines.append("**用户 Skills:**")
            for skill in user_skills:
                lines.append(f"- **{skill['name']}**: {skill['description']}")
                lines.append(f"  → 使用 read_file 阅读 `{skill['path']}` 获取完整说明")
            lines.append("")

        if project_skills:
            lines.append("**项目 Skills:**")
            for skill in project_skills:
                lines.append(f"- **{skill['name']}**: {skill['description']}")
                lines.append(f"  → 使用 read_file 阅读 `{skill['path']}` 获取完整说明")

        return "\n".join(lines)

    # ========== AgentMiddleware 接口实现 ==========

    def before_agent(self, state: SkillsState, runtime: Runtime) -> SkillsStateUpdate | None:  # noqa: ARG002
        """在 agent 执行前加载 skills 元数据。

        每次 agent 交互时都会调用，以捕获 skills 目录的任何变化。

        Args:
            state: 当前 agent 状态。
            runtime: 运行时上下文。

        Returns:
            更新后的状态，包含 skills_metadata。
        """
        logger.info("before_agent: 加载 skills...")
        skills = list_skills(
            user_skills_dir=self.skills_dir,
            project_skills_dir=self.project_skills_dir,
        )
        logger.info(f"before_agent: 加载了 {len(skills)} 个 skills")
        return SkillsStateUpdate(skills_metadata=skills)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """将 skills 文档注入系统提示词。

        每次 model 调用时都会运行，确保 skills 信息始终可用。

        Args:
            request: 正在处理的 model 请求。
            handler: 处理修改后请求的 handler 函数。

        Returns:
            handler 返回的 model 响应。
        """
        # 从 state 获取 skills 元数据
        skills_metadata = request.state.get("skills_metadata", [])

        # 格式化 skills 位置和列表
        skills_locations = self._format_skills_locations()
        skills_list = self._format_skills_list(skills_metadata)

        # 格式化 skills 文档
        skills_section = self.system_prompt_template.format(
            skills_locations=skills_locations,
            skills_list=skills_list,
        )

        # 注入到 system prompt
        if request.system_prompt:
            system_prompt = request.system_prompt + "\n\n" + skills_section
        else:
            system_prompt = skills_section

        logger.debug(f"wrap_model_call: 注入 skills 到 system prompt ({len(skills_section)} 字符)")
        return handler(request.override(system_prompt=system_prompt))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """(异步) 将 skills 文档注入系统提示词。

        Args:
            request: 正在处理的 model 请求。
            handler: 处理修改后请求的异步 handler 函数。

        Returns:
            handler 返回的 model 响应。
        """
        # 从 state 获取 skills 元数据
        state = cast(SkillsState, request.state)
        skills_metadata = state.get("skills_metadata", [])

        # 格式化 skills 位置和列表
        skills_locations = self._format_skills_locations()
        skills_list = self._format_skills_list(skills_metadata)

        # 格式化 skills 文档
        skills_section = self.system_prompt_template.format(
            skills_locations=skills_locations,
            skills_list=skills_list,
        )

        # 注入到 system prompt
        if request.system_prompt:
            system_prompt = request.system_prompt + "\n\n" + skills_section
        else:
            system_prompt = skills_section

        logger.debug(f"awrap_model_call: 注入 skills 到 system prompt ({len(skills_section)} 字符)")
        return await handler(request.override(system_prompt=system_prompt))