"""交互式聊天示例"""
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
你拥有多种工具和能力,包括文件操作、任务规划、网络搜索、计算等。
请根据用户的需求,合理使用这些工具来完成任务。"""
    
    app = DeepAgentApp(
        config=config,
        tools=skills,
        system_prompt=system_prompt,
    )
    
    # 交互式对话
    print("\n" + "="*50)
    print("Deep Agent 交互式聊天")
    print("输入 'quit' 或 'exit' 退出")
    print("="*50 + "\n")
    
    conversation_history = []
    
    while True:
        try:
            # 获取用户输入
            user_input = input("你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "退出"]:
                print("\n再见!")
                break
            
            # 添加用户消息到历史
            conversation_history.append({"role": "user", "content": user_input})
            
            # 调用 agent
            print("\nAgent 正在思考...\n")
            response = app.invoke({"messages": conversation_history})
            
            # 提取 agent 回复
            agent_message = response["messages"][-1]
            print(f"Agent: {agent_message.content}\n")
            
            # 添加 agent 回复到历史
            conversation_history.append({
                "role": "assistant",
                "content": agent_message.content
            })
            
        except KeyboardInterrupt:
            print("\n\n再见!")
            break
        except Exception as e:
            print(f"\n错误: {e}\n")
    
    print(f"\n追踪文件: {app.tracer.get_trace_file_path()}")


if __name__ == "__main__":
    main()

