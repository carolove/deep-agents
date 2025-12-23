# Deep Agents 应用项目

基于 [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) 框架开发的智能代理应用。

## 项目特性

✅ **完整的配置管理** - 支持 YAML 配置文件和环境变量覆盖  
✅ **日志系统** - 基于 loguru 的结构化日志,支持文件和控制台输出  
✅ **LLM 追踪** - 自动记录所有 LLM 请求和响应,便于调试和分析  
✅ **Skills 支持** - 灵活的技能插件系统,支持动态加载自定义工具  
✅ **DeepAgents 框架** - 集成规划、文件系统、子代理等高级能力  

## 项目结构

```
deep-agents/
├── conf/                   # 配置文件目录
│   └── app.yaml           # 应用配置
├── src/                   # 源代码目录
│   ├── core/              # 核心模块
│   │   ├── config.py      # 配置管理
│   │   ├── logger.py      # 日志管理
│   │   ├── tracer.py      # LLM 追踪
│   │   └── agent.py       # Deep Agent 应用
│   ├── skills/            # Skills 目录
│   │   ├── web_search.py  # 网络搜索 skill
│   │   └── calculator.py  # 计算器 skill
│   └── utils/             # 工具模块
│       └── skills.py      # Skills 管理器
├── examples/              # 示例代码
│   ├── basic_usage.py     # 基础使用示例
│   └── interactive_chat.py # 交互式聊天示例
├── logs/                  # 日志目录
│   ├── app.log           # 应用日志
│   └── tracing/          # LLM 追踪日志
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量示例
└── README.md             # 项目说明
```

## 快速开始

### 方式一: 使用初始化脚本 (推荐)

```bash
# 1. 运行初始化脚本
./setup.sh

# 2. 编辑 .env 文件,填写 API 密钥
vim .env

# 3. 运行示例
./run_example.sh          # 基础示例
./run_example.sh chat     # 交互式聊天
```

### 方式二: 手动安装

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件,填写 API 密钥

# 4. 运行示例
python examples/basic_usage.py
python examples/interactive_chat.py
```

### 环境变量配置

编辑 `.env` 文件:

```bash
# Anthropic API 配置 (必需)
ANTHROPIC_API_KEY=your_api_key_here

# 使用 DeepSeek 兼容 API (可选)
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic

# Tavily 搜索 API 配置 (可选)
TAVILY_API_KEY=your_tavily_api_key_here
```

## 配置说明

配置文件位于 `conf/app.yaml`,支持以下配置项:

```yaml
# 服务器配置
server:
  host: "0.0.0.0"
  port: 8080

# 日志配置
log:
  level: "info"          # debug, info, warn, error
  file: "logs/app.log"

# Tracing 配置
tracing:
  enabled: true
  dir: "logs/tracing"

# Anthropic API 配置
anthropic:
  base_url: "https://api.deepseek.com/anthropic"
  api_key: "your_api_key"
  model: "deepseek-chat"
  max_tokens: 4096
  timeout: 60
  max_retries: 3

# Tavily 搜索配置
tavily:
  api_key: "your_tavily_key"
```

## Skills 开发

在 `src/skills/` 目录下创建新的 Python 文件,使用 `@tool` 装饰器定义工具:

```python
from langchain_core.tools import tool

@tool
def my_custom_tool(param: str) -> str:
    """工具描述"""
    # 实现你的逻辑
    return f"结果: {param}"
```

Skills 会在应用启动时自动加载。

## 日志和追踪

### 应用日志

日志文件位于 `logs/app.log`,包含应用运行的详细信息。

### LLM 追踪

所有 LLM 请求和响应会记录到 `logs/tracing/` 目录,文件格式:

```
{user_id}_{tenant_id}_{session_id}_{timestamp}.json
```

每行是一个 JSON 对象,包含:
- 请求信息(模型、消息、参数)
- 响应内容
- Token 使用情况
- 耗时统计

## DeepAgents 框架能力

本项目基于 DeepAgents 框架,自动提供以下内置工具:

- **任务规划** - `write_todos`, `read_todos`
- **文件操作** - `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`
- **子代理** - `task` (委托任务给专门的子代理)
- **命令执行** - `execute` (需要沙箱后端支持)

详见 [DeepAgents 文档](https://docs.langchain.com/oss/python/deepagents/overview)

## 许可证

MIT License

