"""Deep Agent 核心应用"""
import time
from typing import Any, Dict, List, Optional, Callable
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage
from langchain_anthropic import ChatAnthropic
from deepagents import create_deep_agent
from langgraph.graph.state import CompiledStateGraph

from .config import AppConfig
from .logger import get_logger
from .tracer import LLMTracer
from .callbacks import AgentLoggingCallback

logger = get_logger("agent")


class DeepAgentApp:
    """Deep Agent 应用封装"""
    
    def __init__(
        self,
        config: AppConfig,
        tools: Optional[List[Callable]] = None,
        system_prompt: Optional[str] = None,
        middleware: Optional[List[Any]] = None,
        subagents: Optional[List[Any]] = None,
    ):
        """
        初始化 Deep Agent 应用
        
        Args:
            config: 应用配置
            tools: 自定义工具列表
            system_prompt: 系统提示词
            middleware: 中间件列表
            subagents: 子代理列表
        """
        self.config = config
        self.tools = tools or []
        self.system_prompt = system_prompt
        self.middleware = middleware or []
        self.subagents = subagents or []

        # 初始化日志回调
        self.callbacks = [AgentLoggingCallback(verbose=True)]

        # 初始化 tracer
        self.tracer = LLMTracer(
            enabled=config.tracing.enabled,
            trace_dir=config.tracing.dir,
        )

        logger.info("="*60)
        logger.info("初始化 Deep Agent 应用")
        logger.info("="*60)

        # 初始化模型
        self.model = self._create_model()

        # 创建 agent
        self.agent = self._create_agent()

        logger.info("="*60)
        logger.info("Deep Agent 应用初始化完成")
        logger.info("="*60)
    
    def _create_model(self) -> ChatAnthropic:
        """创建 LLM 模型"""
        model_kwargs = {
            "model": self.config.anthropic.model,
            "max_tokens": self.config.anthropic.max_tokens,
            "timeout": self.config.anthropic.timeout,
            "max_retries": self.config.anthropic.max_retries,
        }
        
        if self.config.anthropic.api_key:
            model_kwargs["api_key"] = self.config.anthropic.api_key
        
        if self.config.anthropic.base_url:
            model_kwargs["base_url"] = self.config.anthropic.base_url
        
        logger.info(f"创建模型: {self.config.anthropic.model}")
        return ChatAnthropic(**model_kwargs)
    
    def _create_agent(self) -> CompiledStateGraph:
        """创建 Deep Agent"""
        agent_kwargs = {
            "model": self.model,
            "tools": self.tools,
        }
        
        if self.system_prompt:
            agent_kwargs["system_prompt"] = self.system_prompt
        
        if self.middleware:
            agent_kwargs["middleware"] = self.middleware
        
        if self.subagents:
            agent_kwargs["subagents"] = self.subagents
        
        logger.info(f"创建 Deep Agent: tools={len(self.tools)}, middleware={len(self.middleware)}")
        return create_deep_agent(**agent_kwargs)
    
    def _log_messages(self, messages: List[Any], prefix: str = ""):
        """记录消息详情。"""
        for i, msg in enumerate(messages):
            if isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:100]
                logger.info(f"{prefix}[{i}] {role}: {content}...")
            elif isinstance(msg, BaseMessage):
                content = str(msg.content)[:100]
                logger.info(f"{prefix}[{i}] {msg.type}: {content}...")

    def _log_response(self, response: Dict[str, Any]):
        """记录响应详情。"""
        if not response:
            return

        messages = response.get("messages", [])
        if messages:
            logger.info(f"响应包含 {len(messages)} 条消息:")
            for i, msg in enumerate(messages[-5:]):  # 只显示最后5条
                if isinstance(msg, AIMessage):
                    content = str(msg.content)[:200]
                    logger.info(f"  [{i}] AI: {content}...")
                    if msg.tool_calls:
                        logger.info(f"      工具调用: {[tc['name'] for tc in msg.tool_calls]}")
                elif isinstance(msg, ToolMessage):
                    content = str(msg.content)[:150]
                    logger.info(f"  [{i}] Tool({msg.name}): {content}...")
                elif isinstance(msg, HumanMessage):
                    content = str(msg.content)[:100]
                    logger.info(f"  [{i}] Human: {content}...")

    def invoke(
        self,
        input_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        同步调用 agent

        Args:
            input_data: 输入数据,格式为 {"messages": [...]}
            **kwargs: 其他参数

        Returns:
            agent 响应
        """
        messages = input_data.get("messages", [])

        logger.info("")
        logger.info("="*60)
        logger.info(f"🚀 开始处理请求")
        logger.info("="*60)
        logger.info(f"模型: {self.config.anthropic.model}")
        logger.info(f"消息数量: {len(messages)}")

        # 记录输入消息
        self._log_messages(messages, "  输入 ")

        # 追踪请求
        request_trace = self.tracer.trace_request(
            model=self.config.anthropic.model,
            messages=messages,
            **kwargs
        )

        start_time = time.time()
        error = None
        response = None

        try:
            logger.info("-"*60)
            logger.info("⏳ 正在调用 Agent...")
            logger.info("-"*60)

            # 调用 agent，传入回调
            invoke_kwargs = {**kwargs}
            if "callbacks" not in invoke_kwargs:
                invoke_kwargs["callbacks"] = self.callbacks
            else:
                invoke_kwargs["callbacks"] = list(invoke_kwargs["callbacks"]) + self.callbacks

            response = self.agent.invoke(input_data, **invoke_kwargs)

            duration = time.time() - start_time

            logger.info("-"*60)
            logger.info(f"✅ 请求处理完成 (耗时: {duration:.2f}s)")
            logger.info("-"*60)

            # 记录响应
            self._log_response(response)

        except Exception as e:
            error = str(e)
            duration = time.time() - start_time
            logger.error(f"❌ 请求处理失败 (耗时: {duration:.2f}s): {e}")
            raise

        finally:
            # 追踪响应
            duration = time.time() - start_time
            self.tracer.trace_response(
                request_trace=request_trace,
                response=response,
                duration=duration,
                error=error,
            )
            logger.info("="*60)

        return response
    
    async def ainvoke(
        self,
        input_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        异步调用 agent

        Args:
            input_data: 输入数据,格式为 {"messages": [...]}
            **kwargs: 其他参数

        Returns:
            agent 响应
        """
        messages = input_data.get("messages", [])

        logger.info("")
        logger.info("="*60)
        logger.info(f"🚀 开始处理异步请求")
        logger.info("="*60)
        logger.info(f"模型: {self.config.anthropic.model}")
        logger.info(f"消息数量: {len(messages)}")

        # 记录输入消息
        self._log_messages(messages, "  输入 ")

        # 追踪请求
        request_trace = self.tracer.trace_request(
            model=self.config.anthropic.model,
            messages=messages,
            **kwargs
        )

        start_time = time.time()
        error = None
        response = None

        try:
            logger.info("-"*60)
            logger.info("⏳ 正在调用 Agent (异步)...")
            logger.info("-"*60)

            # 调用 agent，传入回调
            invoke_kwargs = {**kwargs}
            if "callbacks" not in invoke_kwargs:
                invoke_kwargs["callbacks"] = self.callbacks
            else:
                invoke_kwargs["callbacks"] = list(invoke_kwargs["callbacks"]) + self.callbacks

            response = await self.agent.ainvoke(input_data, **invoke_kwargs)

            duration = time.time() - start_time

            logger.info("-"*60)
            logger.info(f"✅ 异步请求处理完成 (耗时: {duration:.2f}s)")
            logger.info("-"*60)

            # 记录响应
            self._log_response(response)

        except Exception as e:
            error = str(e)
            duration = time.time() - start_time
            logger.error(f"❌ 异步请求处理失败 (耗时: {duration:.2f}s): {e}")
            raise

        finally:
            # 追踪响应
            duration = time.time() - start_time
            self.tracer.trace_response(
                request_trace=request_trace,
                response=response,
                duration=duration,
                error=error,
            )
            logger.info("="*60)

        return response

