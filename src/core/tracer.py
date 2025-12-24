"""LLM 请求/响应追踪模块"""
import atexit
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from .logger import get_logger

logger = get_logger("tracer")

# 全局追踪器注册表，用于在程序退出时保存所有追踪器的数据
_tracer_registry: List["LLMTracer"] = []


def _save_all_tracers():
    """在程序退出时保存所有追踪器的数据"""
    for tracer in _tracer_registry:
        tracer.save()


# 注册退出处理函数
atexit.register(_save_all_tracers)


class LLMTracer:
    """LLM 交互追踪器 - 输出 JSON 数组格式"""

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

        # 内存中的追踪记录列表
        self._traces: List[Dict[str, Any]] = []
        self._saved = False

        if self.enabled:
            self.trace_dir.mkdir(parents=True, exist_ok=True)
            self.trace_file = self._get_trace_file()
            # 如果文件已存在，加载现有数据
            self._load_existing_traces()
            # 注册到全局注册表
            _tracer_registry.append(self)
            logger.info(f"LLM Tracer 已启用: {self.trace_file}")
    
    def _get_trace_file(self) -> Path:
        """获取追踪文件路径，相同会话使用同一个文件"""
        filename = f"{self.user_id}_{self.tenant_id}_{self.session_id}.json"
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
        
        
        # 提取响应内容，确保可以 JSON 格式化
        if response is None:
            trace_record["response"] = None
        elif hasattr(response, "content"):
            trace_record["response"] = self._to_json_serializable(response.content)
        elif hasattr(response, "text"):
            trace_record["response"] = self._to_json_serializable(response.text)
        elif isinstance(response, dict):
            trace_record["response"] = self._to_json_serializable(response)
        else:
            trace_record["response"] = str(response)
        
        # 提取 token 使用信息
        if hasattr(response, "usage_metadata"):
            trace_record["usage"] = response.usage_metadata
        
        if self.enabled:
            self._write_trace(trace_record)
        
        logger.debug(f"LLM 响应: duration={duration:.2f}s, error={error}")
        return trace_record
    
    def _to_json_serializable(self, obj: Any) -> Any:
        """
        将对象转换为可 JSON 序列化的格式

        Args:
            obj: 任意对象

        Returns:
            可 JSON 序列化的对象
        """
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, dict):
            return {k: self._to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._to_json_serializable(item) for item in obj]
        elif hasattr(obj, "dict"):
            # Pydantic model 或类似对象
            return self._to_json_serializable(obj.dict())
        elif hasattr(obj, "__dict__"):
            return self._to_json_serializable(obj.__dict__)
        else:
            return str(obj)
        
    def _write_trace(self, trace_record: Dict[str, Any]) -> None:
        """添加追踪记录到内存列表"""
        self._traces.append(trace_record)
        self._saved = False

    def _load_existing_traces(self) -> None:
        """加载现有的追踪文件数据"""
        if self.trace_file.exists():
            try:
                with open(self.trace_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        if isinstance(data, list):
                            self._traces = data
                        else:
                            # 兼容旧格式：单个对象或 JSONL
                            self._traces = [data]
                        logger.debug(f"加载了 {len(self._traces)} 条现有追踪记录")
            except json.JSONDecodeError:
                # 尝试按 JSONL 格式解析（兼容旧格式）
                try:
                    with open(self.trace_file, "r", encoding="utf-8") as f:
                        self._traces = []
                        for line in f:
                            line = line.strip()
                            if line:
                                self._traces.append(json.loads(line))
                        logger.debug(f"从 JSONL 格式加载了 {len(self._traces)} 条追踪记录")
                except Exception as e:
                    logger.warning(f"无法解析现有追踪文件，将创建新文件: {e}")
                    self._traces = []
            except Exception as e:
                logger.warning(f"加载追踪文件失败: {e}")
                self._traces = []

    def save(self) -> None:
        """将追踪记录保存为 JSON 数组格式"""
        if not self.enabled or self._saved:
            return

        try:
            with open(self.trace_file, "w", encoding="utf-8") as f:
                json.dump(self._traces, f, ensure_ascii=False, indent=2, default=str)
            self._saved = True
            logger.debug(f"保存了 {len(self._traces)} 条追踪记录到 {self.trace_file}")
        except Exception as e:
            logger.error(f"保存追踪记录失败: {e}")

    def get_trace_file_path(self) -> Optional[Path]:
        """获取当前追踪文件路径"""
        return self.trace_file if self.enabled else None

    def get_traces(self) -> List[Dict[str, Any]]:
        """获取所有追踪记录"""
        return self._traces.copy()

    def __del__(self):
        """析构时保存数据"""
        self.save()

