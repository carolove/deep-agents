"""Deep Agent 核心应用"""
import time
from typing import Any, Dict, List, Optional, Callable
from langchain_core.messages import BaseMessage
from langchain_anthropic import ChatAnthropic
from deepagents import create_deep_agent
from langgraph.graph.state import CompiledStateGraph

from .config import AppConfig
from .logger import get_logger
from .tracer import LLMTracer

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
        
        # 初始化 tracer
        self.tracer = LLMTracer(
            enabled=config.tracing.enabled,
            trace_dir=config.tracing.dir,
        )
        
        # 初始化模型
        self.model = self._create_model()
        
        # 创建 agent
        self.agent = self._create_agent()
        
        logger.info("Deep Agent 应用初始化完成")
    
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
        logger.info(f"开始处理请求: messages_count={len(messages)}")

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
            # 调用 agent
            response = self.agent.invoke(input_data, **kwargs)
            logger.info("请求处理完成")

        except Exception as e:
            error = str(e)
            logger.error(f"请求处理失败: {e}")
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
        logger.info(f"开始处理异步请求: messages_count={len(messages)}")

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
            # 调用 agent
            response = await self.agent.ainvoke(input_data, **kwargs)
            logger.info("异步请求处理完成")

        except Exception as e:
            error = str(e)
            logger.error(f"异步请求处理失败: {e}")
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

        return response

