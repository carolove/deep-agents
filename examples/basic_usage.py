"""基础使用示例"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.core import load_config, setup_logger
from src.core.agent import DeepAgentApp
from src.utils import load_skills


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
    
    # 加载 skills
    skills = load_skills()
    print(f"\n已加载 {len(skills)} 个 skills")
    
    # 创建 agent 应用
    system_prompt = """你是一个智能助手,可以帮助用户完成各种任务。
你拥有多种工具和能力,包括文件操作、任务规划、网络搜索等。
请根据用户的需求,合理使用这些工具来完成任务。"""
    
    app = DeepAgentApp(
        config=config,
        tools=skills,
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

