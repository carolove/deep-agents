"""LangChain 回调处理器 - 追踪 agent 执行的各个阶段。"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
from langchain_core.agents import AgentAction, AgentFinish

from .logger import get_logger

logger = get_logger("agent.callback")


class AgentLoggingCallback(BaseCallbackHandler):
    """Agent 执行日志回调处理器。
    
    追踪并记录 agent 执行的各个阶段，包括:
    - LLM 调用开始/结束
    - 工具调用开始/结束
    - Agent 动作和完成
    - Chain 执行
    """
    
    def __init__(self, verbose: bool = True):
        """初始化回调处理器。
        
        Args:
            verbose: 是否输出详细日志
        """
        super().__init__()
        self.verbose = verbose
        self._indent = 0
    
    def _log(self, level: str, message: str):
        """带缩进的日志输出。"""
        indent_str = "  " * self._indent
        full_message = f"{indent_str}{message}"
        if level == "debug":
            logger.debug(full_message)
        elif level == "warning":
            logger.warning(full_message)
        elif level == "error":
            logger.error(full_message)
        else:
            logger.info(full_message)
    
    # ========== LLM 回调 ==========
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """LLM 调用开始。"""
        model_name = serialized.get("name", "unknown")
        self._log("info", f"🤖 LLM 调用开始: {model_name}")
        if self.verbose and prompts:
            prompt_preview = prompts[0][:200] + "..." if len(prompts[0]) > 200 else prompts[0]
            self._log("debug", f"   提示词预览: {prompt_preview}")
        self._indent += 1
    
    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """LLM 调用结束。"""
        self._indent = max(0, self._indent - 1)
        if response.generations:
            gen = response.generations[0][0] if response.generations[0] else None
            if gen:
                text_preview = gen.text[:200] + "..." if len(gen.text) > 200 else gen.text
                self._log("info", f"✅ LLM 响应: {text_preview}")
        
        # 记录 token 使用
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("usage", {})
            if usage:
                self._log("info", f"   Token 使用: {usage}")
    
    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """LLM 调用错误。"""
        self._indent = max(0, self._indent - 1)
        self._log("error", f"❌ LLM 错误: {error}")
    
    # ========== Chat Model 回调 ==========
    
    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Chat Model 调用开始。"""
        model_name = serialized.get("name", serialized.get("id", ["unknown"])[-1])
        msg_count = sum(len(m) for m in messages)
        self._log("info", f"💬 Chat Model 调用: {model_name} (消息数: {msg_count})")
        
        if self.verbose and messages and messages[0]:
            last_msg = messages[0][-1]
            content = str(last_msg.content)[:150]
            self._log("debug", f"   最新消息 [{last_msg.type}]: {content}...")
        self._indent += 1
    
    # ========== 工具回调 ==========
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """工具调用开始。"""
        tool_name = serialized.get("name", "unknown")
        self._log("info", f"🔧 工具调用: {tool_name}")
        input_preview = input_str[:200] + "..." if len(input_str) > 200 else input_str
        self._log("info", f"   输入: {input_preview}")
        self._indent += 1
    
    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """工具调用结束。"""
        self._indent = max(0, self._indent - 1)
        output_str = str(output)
        output_preview = output_str[:300] + "..." if len(output_str) > 300 else output_str
        self._log("info", f"   输出: {output_preview}")

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """工具调用错误。"""
        self._indent = max(0, self._indent - 1)
        self._log("error", f"❌ 工具错误: {error}")

    # ========== Agent 回调 ==========

    def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Agent 执行动作。"""
        self._log("info", f"🎯 Agent 动作: {action.tool}")
        input_preview = str(action.tool_input)[:200]
        self._log("info", f"   工具输入: {input_preview}")
        if action.log:
            log_preview = action.log[:200] + "..." if len(action.log) > 200 else action.log
            self._log("debug", f"   思考过程: {log_preview}")

    def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Agent 完成。"""
        self._log("info", f"🏁 Agent 完成")
        output = finish.return_values.get("output", "")
        if output:
            output_preview = str(output)[:300] + "..." if len(str(output)) > 300 else str(output)
            self._log("info", f"   最终输出: {output_preview}")

    # ========== Chain 回调 ==========

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Chain 开始。"""
        chain_name = serialized.get("name", serialized.get("id", ["unknown"])[-1])
        self._log("info", f"⛓️  Chain 开始: {chain_name}")
        self._indent += 1

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Chain 结束。"""
        self._indent = max(0, self._indent - 1)
        self._log("info", f"⛓️  Chain 结束")

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Chain 错误。"""
        self._indent = max(0, self._indent - 1)
        self._log("error", f"❌ Chain 错误: {error}")

