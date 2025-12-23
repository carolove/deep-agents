#!/bin/bash
# Deep Agents 项目初始化脚本

echo "================================"
echo "Deep Agents 项目初始化"
echo "================================"

# 1. 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 2. 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 3. 升级 pip
echo "升级 pip..."
pip install --upgrade pip

# 4. 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 5. 创建 .env 文件
if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    echo "请编辑 .env 文件,填写 API 密钥"
fi

# 6. 创建必要的目录
echo "创建目录..."
mkdir -p logs/tracing

echo ""
echo "================================"
echo "初始化完成!"
echo "================================"
echo ""
echo "下一步:"
echo "1. 编辑 .env 文件,填写 API 密钥"
echo "2. 激活虚拟环境: source venv/bin/activate"
echo "3. 运行示例: python examples/basic_usage.py"
echo ""

