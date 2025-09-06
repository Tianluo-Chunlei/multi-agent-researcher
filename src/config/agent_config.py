"""
Agent Configuration Manager
从.env文件读取配置，为不同的Agent提供专用配置
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class AgentConfig:
    """Agent配置管理器"""
    
    def __init__(self):
        # API配置
        self.anthropic_base_url = os.getenv('ANTHROPIC_BASE_URL')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        
        # LangSmith配置
        self.langsmith_api_key = os.getenv('LANGSMITH_API_KEY')
        self.langsmith_endpoint = os.getenv('LANGSMITH_ENDPOINT')
        self.langsmith_tracing = os.getenv('LANGSMITH_TRACING', 'true').lower() == 'true'
        self.langchain_tracing_v2 = os.getenv('LANGCHAIN_TRACING_V2', 'true').lower() == 'true'
        self.langchain_project = os.getenv('LANGCHAIN_PROJECT', 'deep-research')
        
        # 模型配置
        self.lead_agent_model = os.getenv('LEAD_AGENT_MODEL', 'claude-opus-4-1-20250805')
        self.subagent_model = os.getenv('SUBAGENT_MODEL', 'claude-sonnet-4-20250514')
        self.citation_agent_model = os.getenv('CITATION_AGENT_MODEL', 'claude-sonnet-4-20250514')
        
        # 系统配置
        self.max_concurrent_subagents = int(os.getenv('MAX_CONCURRENT_SUBAGENTS', 5))
        self.max_iterations = int(os.getenv('MAX_ITERATIONS', 5))
        self.context_window_tokens = int(os.getenv('CONTEXT_WINDOW_TOKENS', 200000))
        self.database_path = os.getenv('DATABASE_PATH', './data/research.db')
        
        # 调试配置
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # 设置环境变量用于LangSmith
        self._setup_langsmith_env()
    
    def _setup_langsmith_env(self):
        """设置LangSmith环境变量"""
        if self.langsmith_tracing:
            os.environ['LANGCHAIN_TRACING_V2'] = 'true'
            os.environ['LANGCHAIN_API_KEY'] = self.langsmith_api_key
            os.environ['LANGCHAIN_PROJECT'] = self.langchain_project
            os.environ['LANGCHAIN_ENDPOINT'] = self.langsmith_endpoint
    
    def get_lead_agent_config(self) -> Dict[str, Any]:
        """获取Lead Agent配置"""
        return {
            'model': self.lead_agent_model,
            'api_key': self.anthropic_api_key,
            'base_url': self.anthropic_base_url,
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 120,
            'context_window': self.context_window_tokens,
            'max_iterations': self.max_iterations
        }
    
    def get_research_subagent_config(self) -> Dict[str, Any]:
        """获取Research Subagent配置"""
        return {
            'model': self.subagent_model,
            'api_key': self.anthropic_api_key,
            'base_url': self.anthropic_base_url,
            'temperature': 0.1,
            'max_tokens': 4000,
            'timeout': 60,
            'max_tool_calls': 15
        }
    
    def get_citations_agent_config(self) -> Dict[str, Any]:
        """获取Citations Agent配置"""
        return {
            'model': self.citation_agent_model,
            'api_key': self.anthropic_api_key,
            'base_url': self.anthropic_base_url,
            'temperature': 0.0,  # 引用需要准确性
            'max_tokens': 4000,
            'timeout': 60
        }
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统级配置"""
        return {
            'max_concurrent_subagents': self.max_concurrent_subagents,
            'database_path': self.database_path,
            'debug': self.debug,
            'log_level': self.log_level
        }

# 全局配置实例
config = AgentConfig()