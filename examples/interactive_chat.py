"""交互式聊天示例 - 支持 Tab 键切换 Thinking 模式"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from src.core import load_config, setup_logger
from src.core.agent import DeepAgentApp
from src.utils import load_skills


class ThinkingModeManager:
    """Thinking 模式管理器

    支持两种模式:
    1. 普通模式 (deepseek-chat) - 快速响应
    2. 思考模式 (deepseek-reasoner) - 深度思考,输出思维链
    """

    def __init__(self, config):
        self.config = config
        self.thinking_enabled = False
        # DeepSeek 模型名称
        self.normal_model = "deepseek-chat"
        self.thinking_model = "deepseek-reasoner"
        # thinking 参数配置 (用于 Anthropic API 兼容模式)
        self.thinking_budget_tokens = 4096

    def toggle(self):
        """切换 thinking 模式"""
        self.thinking_enabled = not self.thinking_enabled
        return self.thinking_enabled

    def get_current_model(self) -> str:
        """获取当前模型"""
        return self.thinking_model if self.thinking_enabled else self.normal_model

    def get_status_text(self) -> str:
        """获取状态文本"""
        if self.thinking_enabled:
            return "🧠 Thinking: ON"
        else:
            return "💬 Thinking: OFF"

    def get_status_color(self) -> str:
        """获取状态颜色"""
        return "ansigreen" if self.thinking_enabled else "ansigray"


def create_prompt_session(thinking_manager: ThinkingModeManager):
    """创建带有快捷键绑定的 prompt session"""

    # 创建键绑定
    bindings = KeyBindings()

    @bindings.add('c-t')  # Ctrl+T
    def toggle_thinking(event):
        """Ctrl+T 切换 thinking 模式"""
        thinking_manager.toggle()
        status = thinking_manager.get_status_text()
        # 打印状态变化提示
        print(f"\n>>> 模式已切换: {status}")
        # 刷新提示符
        event.app.invalidate()

    @bindings.add('f2')  # F2 也可以切换
    def toggle_thinking_f2(event):
        """F2 切换 thinking 模式"""
        thinking_manager.toggle()
        status = thinking_manager.get_status_text()
        print(f"\n>>> 模式已切换: {status}")
        event.app.invalidate()

    # 创建样式
    style = Style.from_dict({
        'status': 'bg:#333333 #ffffff',
        'status-on': 'bg:#006600 #ffffff bold',
        'status-off': 'bg:#666666 #ffffff',
    })

    # 创建 session
    session = PromptSession(
        key_bindings=bindings,
        style=style,
    )

    return session


def get_terminal_width() -> int:
    """获取终端宽度"""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def print_with_status(text: str, thinking_manager: ThinkingModeManager, end="\n"):
    """打印带有右侧状态的文本"""
    status = thinking_manager.get_status_text()
    terminal_width = get_terminal_width()

    # 计算需要的空格数
    # 注意: 中文字符和 emoji 占用2个显示宽度
    text_display_width = sum(2 if ord(c) > 127 else 1 for c in text)
    status_display_width = sum(2 if ord(c) > 127 else 1 for c in status)

    padding = terminal_width - text_display_width - status_display_width - 2

    if padding > 0:
        # 状态颜色
        if thinking_manager.thinking_enabled:
            status_colored = f"\033[92m{status}\033[0m"  # 绿色
        else:
            status_colored = f"\033[90m{status}\033[0m"  # 灰色
        print(f"{text}{' ' * padding}{status_colored}", end=end)
    else:
        print(text, end=end)


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

    # 创建 thinking 模式管理器
    thinking_manager = ThinkingModeManager(config)

    # 创建 agent 应用 (初始使用普通模式)
    system_prompt = """你是一个智能助手,可以帮助用户完成各种任务。
你拥有多种工具和能力,包括文件操作、任务规划、网络搜索、计算等。
请根据用户的需求,合理使用这些工具来完成任务。"""

    # 创建两个 agent 应用: 普通模式和 thinking 模式
    app_normal = DeepAgentApp(
        config=config,
        tools=skills,
        system_prompt=system_prompt,
    )

    # 创建 thinking 模式的配置
    config_thinking = load_config()
    config_thinking.anthropic.model = "deepseek-reasoner"

    app_thinking = DeepAgentApp(
        config=config_thinking,
        tools=skills,
        system_prompt=system_prompt,
    )

    # 创建 prompt session
    session = create_prompt_session(thinking_manager)

    # 打印欢迎信息
    print("\n" + "="*60)
    print("Deep Agent 交互式聊天")
    print("-"*60)
    print("  [Ctrl+T] 或 [F2]  切换 Thinking 模式 (deepseek-reasoner)")
    print("  [quit] 退出程序")
    print("="*60)

    conversation_history = []

    while True:
        try:
            # 构建提示符 (显示当前模式)
            status = thinking_manager.get_status_text()
            if thinking_manager.thinking_enabled:
                prompt_text = HTML(f'<style fg="ansigreen">[{status}]</style> 你: ')
            else:
                prompt_text = HTML(f'<style fg="ansigray">[{status}]</style> 你: ')

            # 获取用户输入
            user_input = session.prompt(prompt_text).strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "退出"]:
                print("\n再见!")
                break

            # 添加用户消息到历史
            conversation_history.append({"role": "user", "content": user_input})

            # 根据当前模式选择 agent
            current_app = app_thinking if thinking_manager.thinking_enabled else app_normal
            model_name = thinking_manager.get_current_model()

            # 显示处理状态
            if thinking_manager.thinking_enabled:
                print(f"\n🧠 Agent 正在深度思考 (使用 {model_name})...\n")
            else:
                print(f"\n💬 Agent 正在处理 (使用 {model_name})...\n")

            # 调用 agent
            response = current_app.invoke({"messages": conversation_history})

            # 提取 agent 回复
            agent_message = response["messages"][-1]

            # 检查是否有思考内容 (content_blocks 或 reasoning_content)
            thinking_text = None
            final_text = None

            # 方式1: 检查 content_blocks (Anthropic API 格式)
            content_blocks = getattr(agent_message, 'content_blocks', None)
            if content_blocks:
                for block in content_blocks:
                    if isinstance(block, dict):
                        if block.get('type') == 'thinking':
                            thinking_text = block.get('thinking', '')
                        elif block.get('type') == 'text':
                            final_text = block.get('text', '')

            # 方式2: 检查 reasoning_content (DeepSeek OpenAI API 格式)
            if not thinking_text:
                thinking_text = getattr(agent_message, 'reasoning_content', None)

            # 获取最终回复内容
            if not final_text:
                final_text = agent_message.content

            # 显示思考过程 (如果有)
            if thinking_text and thinking_manager.thinking_enabled:
                print("="*60)
                print("🧠 思考过程:")
                print("-"*60)
                # 限制显示长度
                if len(thinking_text) > 2000:
                    print(thinking_text[:2000] + "\n... (思考内容已截断)")
                else:
                    print(thinking_text)
                print("="*60)
                print()

            print(f"Agent: {final_text}\n")

            # 添加 agent 回复到历史 (不包含 reasoning_content)
            conversation_history.append({
                "role": "assistant",
                "content": final_text if isinstance(final_text, str) else str(final_text)
            })

        except KeyboardInterrupt:
            print("\n\n再见!")
            break
        except Exception as e:
            print(f"\n错误: {e}\n")
            import traceback
            traceback.print_exc()

    print(f"\n追踪文件: {app_normal.tracer.get_trace_file_path()}")


if __name__ == "__main__":
    main()

