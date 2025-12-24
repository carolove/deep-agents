"""Skill loader 用于解析和加载 SKILL.md 文件中的 agent skills。

实现 Anthropic 的 agent skills 模式，使用 YAML frontmatter 解析。
每个 skill 是一个包含 SKILL.md 文件的目录:
- YAML frontmatter (name, description 必需)
- Markdown 格式的 agent 指令
- 可选的支持文件 (scripts, configs 等)

SKILL.md 结构示例:
```markdown
---
name: web-research
description: Structured approach to conducting thorough web research
---

# Web Research Skill

## When to Use
- User asks you to research a topic
...
```
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, NotRequired, TypedDict

import yaml

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# SKILL.md 文件最大大小 (10MB)
MAX_SKILL_FILE_SIZE = 10 * 1024 * 1024

# Agent Skills 规范约束 (https://agentskills.io/specification)
MAX_SKILL_NAME_LENGTH = 64
MAX_SKILL_DESCRIPTION_LENGTH = 1024


class SkillMetadata(TypedDict):
    """Skill 的元数据，按照 Agent Skills 规范定义。"""

    name: str
    """Skill 名称 (最多64字符, 小写字母数字和连字符)。"""

    description: str
    """Skill 的功能描述 (最多1024字符)。"""

    path: str
    """SKILL.md 文件的路径。"""

    source: str
    """Skill 来源 ('user' 或 'project')。"""

    # Agent Skills 规范中的可选字段
    license: NotRequired[str | None]
    """许可证名称或引用。"""

    compatibility: NotRequired[str | None]
    """环境需求 (最多500字符)。"""

    metadata: NotRequired[dict[str, str] | None]
    """额外元数据的键值映射。"""

    allowed_tools: NotRequired[str | None]
    """预先批准的工具列表（空格分隔）。"""


def _is_safe_path(path: Path, base_dir: Path) -> bool:
    """检查路径是否安全地位于 base_dir 内部。
    
    防止通过符号链接或路径操作进行的目录遍历攻击。
    """
    try:
        resolved_path = path.resolve()
        resolved_base = base_dir.resolve()
        resolved_path.relative_to(resolved_base)
        return True
    except ValueError:
        return False
    except (OSError, RuntimeError):
        return False


def _validate_skill_name(name: str, directory_name: str) -> tuple[bool, str]:
    """验证 skill 名称是否符合 Agent Skills 规范。
    
    要求:
    - 最多64个字符
    - 只能包含小写字母数字和连字符 (a-z, 0-9, -)
    - 不能以连字符开头或结尾
    - 不能有连续的连字符
    - 必须与父目录名称匹配
    """
    if not name:
        return False, "name is required"
    if len(name) > MAX_SKILL_NAME_LENGTH:
        return False, "name exceeds 64 characters"
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
        return False, "name must be lowercase alphanumeric with single hyphens only"
    if name != directory_name:
        return False, f"name '{name}' must match directory name '{directory_name}'"
    return True, ""


def _parse_skill_metadata(skill_md_path: Path, source: str) -> SkillMetadata | None:
    """从 SKILL.md 文件解析 YAML frontmatter。"""
    try:
        file_size = skill_md_path.stat().st_size
        if file_size > MAX_SKILL_FILE_SIZE:
            logger.warning("跳过 %s: 文件过大 (%d bytes)", skill_md_path, file_size)
            return None

        content = skill_md_path.read_text(encoding="utf-8")

        # 匹配 --- 分隔符之间的 YAML frontmatter
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if not match:
            logger.warning("跳过 %s: 没有找到有效的 YAML frontmatter", skill_md_path)
            return None

        frontmatter_str = match.group(1)

        try:
            frontmatter_data = yaml.safe_load(frontmatter_str)
        except yaml.YAMLError as e:
            logger.warning("无效的 YAML %s: %s", skill_md_path, e)
            return None

        if not isinstance(frontmatter_data, dict):
            logger.warning("跳过 %s: frontmatter 不是映射类型", skill_md_path)
            return None

        name = frontmatter_data.get("name")
        description = frontmatter_data.get("description")

        if not name or not description:
            logger.warning("跳过 %s: 缺少必需的 'name' 或 'description'", skill_md_path)
            return None

        directory_name = skill_md_path.parent.name
        is_valid, error = _validate_skill_name(str(name), directory_name)
        if not is_valid:
            logger.warning(
                "Skill '%s' 在 %s 不符合 Agent Skills 规范: %s",
                name, skill_md_path, error,
            )

        description_str = str(description)
        if len(description_str) > MAX_SKILL_DESCRIPTION_LENGTH:
            logger.warning("描述超过 %d 字符，将被截断 %s", MAX_SKILL_DESCRIPTION_LENGTH, skill_md_path)
            description_str = description_str[:MAX_SKILL_DESCRIPTION_LENGTH]

        return SkillMetadata(
            name=str(name),
            description=description_str,
            path=str(skill_md_path),
            source=source,
            license=frontmatter_data.get("license"),
            compatibility=frontmatter_data.get("compatibility"),
            metadata=frontmatter_data.get("metadata"),
            allowed_tools=frontmatter_data.get("allowed-tools"),
        )

    except (OSError, UnicodeDecodeError) as e:
        logger.warning("读取错误 %s: %s", skill_md_path, e)
        return None


def _list_skills(skills_dir: Path, source: str) -> list[SkillMetadata]:
    """从单个 skills 目录列出所有 skills（内部辅助函数）。

    扫描 skills 目录中包含 SKILL.md 文件的子目录，
    解析 YAML frontmatter，并返回 skill 元数据。
    """
    skills_dir = skills_dir.expanduser()
    if not skills_dir.exists():
        return []

    try:
        resolved_base = skills_dir.resolve()
    except (OSError, RuntimeError):
        return []

    skills: list[SkillMetadata] = []

    for skill_dir in skills_dir.iterdir():
        if not _is_safe_path(skill_dir, resolved_base):
            continue

        if not skill_dir.is_dir():
            continue

        skill_md_path = skill_dir / "SKILL.md"
        if not skill_md_path.exists():
            continue

        if not _is_safe_path(skill_md_path, resolved_base):
            continue

        metadata = _parse_skill_metadata(skill_md_path, source=source)
        if metadata:
            skills.append(metadata)

    return skills


def list_skills(
    *, user_skills_dir: Path | None = None, project_skills_dir: Path | None = None
) -> list[SkillMetadata]:
    """从用户和/或项目目录列出 skills。

    当两个目录都提供时，同名的项目 skill 会覆盖用户 skill。

    Args:
        user_skills_dir: 用户级 skills 目录的路径。
        project_skills_dir: 项目级 skills 目录的路径。

    Returns:
        合并后的 skill 元数据列表，项目 skills 优先于用户 skills。
    """
    all_skills: dict[str, SkillMetadata] = {}

    # 先加载用户 skills (基础)
    if user_skills_dir:
        user_skills = _list_skills(user_skills_dir, source="user")
        for skill in user_skills:
            all_skills[skill["name"]] = skill

    # 再加载项目 skills (覆盖/增强)
    if project_skills_dir:
        project_skills = _list_skills(project_skills_dir, source="project")
        for skill in project_skills:
            all_skills[skill["name"]] = skill

    return list(all_skills.values())

