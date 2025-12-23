"""配置管理模块"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dataclasses import dataclass, field


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8080


@dataclass
class LogConfig:
    """日志配置"""
    level: str = "info"
    file: str = "logs/app.log"


@dataclass
class TracingConfig:
    """Tracing 配置"""
    enabled: bool = True
    dir: str = "logs/tracing"


@dataclass
class AnthropicConfig:
    """Anthropic API 配置"""
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    auth_token: Optional[str] = None
    model: str = "deepseek-chat"
    max_tokens: int = 4096
    timeout: int = 60
    max_retries: int = 3


@dataclass
class TavilyConfig:
    """Tavily 搜索 API 配置"""
    api_key: Optional[str] = None


@dataclass
class AppConfig:
    """应用配置"""
    server: ServerConfig = field(default_factory=ServerConfig)
    log: LogConfig = field(default_factory=LogConfig)
    tracing: TracingConfig = field(default_factory=TracingConfig)
    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    tavily: TavilyConfig = field(default_factory=TavilyConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """从字典创建配置对象"""
        return cls(
            server=ServerConfig(**data.get("server", {})),
            log=LogConfig(**data.get("log", {})),
            tracing=TracingConfig(**data.get("tracing", {})),
            anthropic=AnthropicConfig(**data.get("anthropic", {})),
            tavily=TavilyConfig(**data.get("tavily", {})),
        )

    def apply_env_overrides(self) -> None:
        """应用环境变量覆盖"""
        # Anthropic API 配置
        if api_key := os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic.api_key = api_key
        if base_url := os.getenv("ANTHROPIC_BASE_URL"):
            self.anthropic.base_url = base_url
        if auth_token := os.getenv("ANTHROPIC_AUTH_TOKEN"):
            self.anthropic.auth_token = auth_token
        
        # Tavily API 配置
        if tavily_key := os.getenv("TAVILY_API_KEY"):
            self.tavily.api_key = tavily_key


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径,默认为 conf/app.yaml
        
    Returns:
        AppConfig: 应用配置对象
    """
    if config_path is None:
        config_path = os.getenv("APP_CONFIG_PATH", "conf/app.yaml")
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        print(f"警告: 配置文件 {config_path} 不存在,使用默认配置")
        config = AppConfig()
    else:
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            config = AppConfig.from_dict(data)
    
    # 应用环境变量覆盖
    config.apply_env_overrides()
    
    # 确保日志和 tracing 目录存在
    Path(config.log.file).parent.mkdir(parents=True, exist_ok=True)
    if config.tracing.enabled:
        Path(config.tracing.dir).mkdir(parents=True, exist_ok=True)
    
    return config

