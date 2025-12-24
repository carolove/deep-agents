"""基础使用示例 - 展示 Anthropic Skills 渐进式披露模式

这个示例展示:
1. 加载 skills 元数据 (name + description)
2. 将元数据注入系统提示词
3. 提供文件系统工具让 Agent 能够:
   - 使用 read_file 读取 SKILL.md 获取完整说明
   - 使用 bash_execute 执行 skill 脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.core import load_config, setup_logger
from src.core.agent import DeepAgentApp
from src.skills import SkillsMiddleware


def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()

    # 加载配置
    config = load_config()

    # 设置日志
    setup_logger(
        log_file=config.log.file,
        log_level=config.log.level,
    )

    # 加载 skills (使用 Anthropic Skills 渐进式披露模式)
    print("\n" + "="*50)
    print("加载 Skills (Anthropic Skills 模式)...")
    print("-"*50)

    # 创建 skills 中间件
    skills_middleware = SkillsMiddleware(
        skills_dir=Path.home() / ".deep-agents/agent/skills",
        assistant_id="agent",
        project_skills_dir=project_root / "src/skills",
    )

    # 加载并显示 skills
    skills_metadata = skills_middleware.load_skills()
    print(f"\n已加载 {len(skills_metadata)} 个 skills:")
    for skill in skills_metadata:
        print(f"  - {skill['name']}: {skill['description'][:50]}...")

    # 获取 skills 需要的工具 (文件系统工具)
    skills_tools = skills_middleware.get_tools()
    print(f"\nSkills 工具: {[t.name for t in skills_tools]}")

    # 基础系统提示词
    base_system_prompt = """你是一个智能助手,可以帮助用户完成各种任务。

你拥有文件系统工具,可以:
- 使用 read_file 读取文件内容
- 使用 bash_execute 执行命令和脚本
- 使用 list_directory 查看目录内容

请根据用户的需求,合理使用这些工具和 skills 来完成任务。"""

    # 使用中间件增强系统提示词 (注入 skills 信息)
    system_prompt = skills_middleware.enhance_system_prompt(base_system_prompt)

    # 创建 agent 应用，传入 skills 工具
    app = DeepAgentApp(
        config=config,
        tools=skills_tools,  # 使用 skills 提供的文件系统工具
        system_prompt=system_prompt,
    )
    
    # 测试对话
    print("\n" + "="*50)
    print("Deep Agent 应用已启动")
    print("="*50 + "\n")
    
    # 示例 1: 简单问答
    print("示例 1: 简单问答")
    print("-" * 50)
    response = app.invoke({
        "messages": [
            {"role": "user", "content": "你好,请介绍一下你自己"}
        ]
    })
    print(f"回答: {response['messages'][-1].content}\n")
    
    # 示例 2: 使用工具
    print("示例 2: 使用计算器工具")
    print("-" * 50)
    response = app.invoke({
        "messages": [
            {"role": "user", "content": "请帮我计算 123 * 456"}
        ]
    })
    print(f"回答: {response['messages'][-1].content}\n")
    
    # 示例 3: 获取当前时间
    print("示例 3: 获取当前时间")
    print("-" * 50)
    response = app.invoke({
        "messages": [
            {"role": "user", "content": "现在几点了?"}
        ]
    })
    print(f"回答: {response['messages'][-1].content}\n")
    
    print("="*50)
    print("示例运行完成!")
    print(f"追踪文件: {app.tracer.get_trace_file_path()}")
    print("="*50)


if __name__ == "__main__":
    main()

