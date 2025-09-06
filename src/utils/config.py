"""Configuration management for Deep Research system."""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config(BaseSettings):
    """System configuration."""
    
    # API Keys
    anthropic_base_url: Optional[str] = Field(None, env="ANTHROPIC_BASE_URL")
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    langsmith_api_key: Optional[str] = Field(None, env="LANGSMITH_API_KEY")
    
    # LangSmith Configuration
    langchain_tracing_v2: bool = Field(True, env="LANGCHAIN_TRACING_V2")
    langchain_project: str = Field("deep-research", env="LANGCHAIN_PROJECT")
    langchain_endpoint: str = Field(
        "https://api.smith.langchain.com", 
        env="LANGCHAIN_ENDPOINT"
    )
    langsmith_endpoint: Optional[str] = Field(None, env="LANGSMITH_ENDPOINT")
    langsmith_tracing: Optional[str] = Field(None, env="LANGSMITH_TRACING")
    
    # Model Configuration
    lead_agent_model: str = Field(
        "claude-opus-4-1-20250805",
        env="LEAD_AGENT_MODEL"
    )
    subagent_model: str = Field(
        "claude-sonnet-4-20250514",
        env="SUBAGENT_MODEL"
    )
    citation_agent_model: str = Field(
        "claude-sonnet-4-20250514",
        env="CITATION_AGENT_MODEL"
    )
    citation_model: str = Field(
        "claude-sonnet-4-20250514",
        env="CITATION_MODEL"
    )
    
    # System Configuration
    max_concurrent_subagents: int = Field(5, env="MAX_CONCURRENT_SUBAGENTS")
    max_iterations: int = Field(5, env="MAX_ITERATIONS")
    context_window_tokens: int = Field(200000, env="CONTEXT_WINDOW_TOKENS")
    database_path: Path = Field(
        Path("./data/research.db"),
        env="DATABASE_PATH"
    )
    
    # Debug
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_config() -> Config:
    """Get configuration instance."""
    return Config()

# Initialize configuration
config = get_config()