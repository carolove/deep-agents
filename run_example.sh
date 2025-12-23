#!/bin/bash
# 运行示例脚本

# 激活虚拟环境
source venv/bin/activate

# 运行示例
if [ "$1" == "chat" ]; then
    echo "启动交互式聊天..."
    python examples/interactive_chat.py
else
    echo "运行基础示例..."
    python examples/basic_usage.py
fi

