"""基础使用示例 - 展示 Anthropic Skills 渐进式披露模式

这个示例展示:
1. 创建 SkillsMiddleware (继承 AgentMiddleware)
2. 将 middleware 传入 create_deep_agent
3. SkillsMiddleware 自动:
   - before_agent(): 加载 skills 元数据
   - wrap_model_call(): 注入 skills 到 system prompt
4. Agent 使用框架内置的 read_file/execute 工具访问 skills
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

    # 创建 skills 中间件 (真正的 AgentMiddleware)
    print("\n" + "="*50)
    print("创建 Skills 中间件 (AgentMiddleware)...")
    print("-"*50)

    skills_middleware = SkillsMiddleware(
        skills_dir=Path.home() / ".deep-agents/agent/skills",
        assistant_id="agent",
        project_skills_dir=project_root / "src/skills",
    )

    print(f"Skills 中间件已创建")
    print(f"  - 用户 skills 目录: {skills_middleware.skills_dir}")
    print(f"  - 项目 skills 目录: {skills_middleware.project_skills_dir}")

    # 基础系统提示词 (参考 deepagents-cli)
    # Skills 信息会通过 SkillsMiddleware.wrap_model_call() 自动注入
    base_system_prompt = f"""你是一个智能助手，可以帮助用户完成各种任务。

## 当前工作目录

工作目录: `{project_root}`

## 可用工具

你有以下文件系统工具 (由 deepagents 框架提供):
- `read_file`: 读取文件内容
- `write_file`: 写入文件
- `ls`: 列出目录
- `execute`: 执行 shell 命令
- `edit_file`: 编辑文件

## 使用 Skills 执行任务

当需要使用 skill 完成任务时，按以下步骤操作:

1. **阅读 skill 说明**: 使用 `read_file` 读取 SKILL.md 获取完整说明
2. **执行 skill 脚本**: 使用 `execute` 工具直接执行脚本

示例:
```
execute(command="python /path/to/skill/script.py 参数")
```

**重要规则**:
- 直接使用 `execute` 工具执行 skill 脚本
- **不要使用 `task` 工具委托给子代理** - 这会导致不必要的延迟
- 执行完成后，将结果综合成自然语言回复用户

## 风格和语气

- 简洁直接地回答问题
- 完成任务后不要过度解释
- 绝不要直接显示原始 JSON 给用户"""

    # 创建 agent 应用
    # - SkillsMiddleware 自动加载和注入 skills 到 system prompt
    app = DeepAgentApp(
        config=config,
        tools=[],  # 不使用额外工具，依赖 skills
        system_prompt=base_system_prompt,
        middleware=[skills_middleware],
        working_dir=project_root,
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

