"""Middleware 用于加载和将 agent skills 暴露给系统提示词。

这个中间件实现 Anthropic 的 "Agent Skills" 模式，采用渐进式披露:
1. 在会话开始时从 SKILL.md 文件解析 YAML frontmatter
2. 将 skills 元数据 (name + description) 注入系统提示词
3. 当 skill 与任务相关时，Agent 读取完整的 SKILL.md 内容

Skills 目录结构 (每个 agent + 项目):
用户级: ~/.deep-agents/{AGENT_NAME}/skills/
项目级: {PROJECT_ROOT}/.deep-agents/skills/
"""

from pathlib import Path
from typing import List, Optional

from .load import SkillMetadata, list_skills


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


class SkillsMiddleware:
    """用于加载和暴露 agent skills 的中间件。
    
    实现 Anthropic 的 agent skills 模式:
    - 在会话开始时从 YAML frontmatter 加载 skills 元数据
    - 将 skills 列表注入系统提示词以便发现
    - Agent 在 skill 相关时读取完整的 SKILL.md 内容（渐进式披露）

    支持用户级和项目级 skills:
    - 用户 skills: ~/.deep-agents/{AGENT_NAME}/skills/
    - 项目 skills: {PROJECT_ROOT}/.deep-agents/skills/
    - 同名的项目 skills 会覆盖用户 skills
    """

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
        self.skills_dir = Path(skills_dir).expanduser()
        self.assistant_id = assistant_id
        self.project_skills_dir = (
            Path(project_skills_dir).expanduser() if project_skills_dir else None
        )
        self.user_skills_display = f"~/.deep-agents/{assistant_id}/skills"
        self.system_prompt_template = SKILLS_SYSTEM_PROMPT
        self._skills_metadata: List[SkillMetadata] = []
    
    def load_skills(self) -> List[SkillMetadata]:
        """加载所有 skills 元数据。"""
        self._skills_metadata = list_skills(
            user_skills_dir=self.skills_dir,
            project_skills_dir=self.project_skills_dir,
        )
        return self._skills_metadata
    
    def get_skills_metadata(self) -> List[SkillMetadata]:
        """获取已加载的 skills 元数据。"""
        return self._skills_metadata

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
                lines.append(f"  → 阅读 `{skill['path']}` 获取完整说明")
            lines.append("")

        if project_skills:
            lines.append("**项目 Skills:**")
            for skill in project_skills:
                lines.append(f"- **{skill['name']}**: {skill['description']}")
                lines.append(f"  → 阅读 `{skill['path']}` 获取完整说明")

        return "\n".join(lines)

    def get_skills_prompt(self) -> str:
        """获取要注入系统提示词的 skills 文档。"""
        if not self._skills_metadata:
            self.load_skills()
        
        skills_locations = self._format_skills_locations()
        skills_list = self._format_skills_list(self._skills_metadata)
        
        return self.system_prompt_template.format(
            skills_locations=skills_locations,
            skills_list=skills_list,
        )
    
    def enhance_system_prompt(self, system_prompt: Optional[str] = None) -> str:
        """增强系统提示词，添加 skills 文档。"""
        skills_section = self.get_skills_prompt()
        
        if system_prompt:
            return system_prompt + "\n\n" + skills_section
        return skills_section

