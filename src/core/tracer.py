"""LLM 请求/响应追踪模块"""
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
from .logger import get_logger

logger = get_logger("tracer")


class LLMTracer:
    """LLM 交互追踪器"""
    
    def __init__(
        self,
        enabled: bool = True,
        trace_dir: str = "logs/tracing",
        user_id: str = "default",
        tenant_id: str = "default",
        session_id: Optional[str] = None,
    ):
        """
        初始化追踪器
        
        Args:
            enabled: 是否启用追踪
            trace_dir: 追踪文件存放目录
            user_id: 用户 ID
            tenant_id: 租户 ID
            session_id: 会话 ID,默认使用时间戳
        """
        self.enabled = enabled
        self.trace_dir = Path(trace_dir)
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.enabled:
            self.trace_dir.mkdir(parents=True, exist_ok=True)
            self.trace_file = self._get_trace_file()
            logger.info(f"LLM Tracer 已启用: {self.trace_file}")
    
    def _get_trace_file(self) -> Path:
        """获取追踪文件路径"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.user_id}_{self.tenant_id}_{self.session_id}_{timestamp}.json"
        return self.trace_dir / filename
    
    def trace_request(
        self,
        model: str,
        messages: list,
        **kwargs
    ) -> Dict[str, Any]:
        """
        追踪 LLM 请求
        
        Args:
            model: 模型名称
            messages: 消息列表
            **kwargs: 其他请求参数
            
        Returns:
            追踪记录
        """
        trace_record = {
            "type": "request",
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "messages": messages,
            "parameters": kwargs,
        }
        
        if self.enabled:
            self._write_trace(trace_record)
        
        logger.debug(f"LLM 请求: model={model}, messages_count={len(messages)}")
        return trace_record
    
    def trace_response(
        self,
        request_trace: Dict[str, Any],
        response: Any,
        duration: float,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        追踪 LLM 响应
        
        Args:
            request_trace: 请求追踪记录
            response: 响应对象
            duration: 请求耗时(秒)
            error: 错误信息
            
        Returns:
            追踪记录
        """
        trace_record = {
            "type": "response",
            "timestamp": datetime.now().isoformat(),
            "request": request_trace,
            "duration": duration,
            "error": error,
        }
        
        # 提取响应内容
        if hasattr(response, "content"):
            trace_record["content"] = response.content
        elif hasattr(response, "text"):
            trace_record["content"] = response.text
        else:
            trace_record["content"] = str(response)
        
        # 提取 token 使用信息
        if hasattr(response, "usage_metadata"):
            trace_record["usage"] = response.usage_metadata
        
        if self.enabled:
            self._write_trace(trace_record)
        
        logger.debug(f"LLM 响应: duration={duration:.2f}s, error={error}")
        return trace_record
    
    def _write_trace(self, trace_record: Dict[str, Any]) -> None:
        """写入追踪记录到文件"""
        try:
            with open(self.trace_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(trace_record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"写入追踪记录失败: {e}")
    
    def get_trace_file_path(self) -> Optional[Path]:
        """获取当前追踪文件路径"""
        return self.trace_file if self.enabled else None

