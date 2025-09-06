"""LangSmith tracing configuration and utilities."""

import os
from typing import Optional
from langsmith import Client
from src.utils.logger import logger
from src.utils.config import config


class TracingManager:
    """Manage LangSmith tracing configuration."""
    
    def __init__(self):
        """Initialize tracing manager."""
        self.enabled = False
        self.client: Optional[Client] = None
        self._setup_tracing()
    
    def _setup_tracing(self):
        """Setup LangSmith tracing if configured."""
        # Check if tracing should be enabled
        tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        api_key = os.getenv("LANGSMITH_API_KEY", "").strip()
        
        if tracing_enabled and api_key:
            try:
                # Set timeout for LangSmith client
                os.environ["LANGCHAIN_CLIENT_TIMEOUT"] = "10.0"
                
                # Initialize LangSmith client with timeout
                self.client = Client(api_key=api_key)
                self.enabled = True
                
                # Set environment variables for LangChain
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "deep-research")
                
                logger.info(f"LangSmith tracing enabled for project: {os.environ['LANGCHAIN_PROJECT']}")
                
            except Exception as e:
                logger.debug(f"LangSmith initialization: {e}")
                # Disable tracing if LangSmith is not available
                os.environ["LANGCHAIN_TRACING_V2"] = "false"
                self.enabled = False
        else:
            if tracing_enabled and not api_key:
                logger.info("LangSmith tracing requested but no API key provided")
            self.enabled = False
    
    def enable_tracing(self, api_key: Optional[str] = None, project: str = "deep-research"):
        """Enable LangSmith tracing.
        
        Args:
            api_key: LangSmith API key (optional if in env)
            project: Project name for tracing
        """
        if api_key:
            os.environ["LANGSMITH_API_KEY"] = api_key
        
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = project
        
        self._setup_tracing()
        
        if self.enabled:
            logger.info(f"Tracing enabled for project: {project}")
        else:
            logger.warning("Failed to enable tracing")
    
    def disable_tracing(self):
        """Disable LangSmith tracing."""
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        self.enabled = False
        self.client = None
        logger.info("Tracing disabled")
    
    def get_run_url(self, run_id: str) -> Optional[str]:
        """Get URL for a traced run.
        
        Args:
            run_id: Run ID from LangSmith
            
        Returns:
            URL to view the run, or None if not available
        """
        if self.client and self.enabled:
            try:
                # Get the run URL
                project = os.environ.get("LANGCHAIN_PROJECT", "deep-research")
                return f"https://smith.langchain.com/{project}/runs/{run_id}"
            except Exception as e:
                logger.error(f"Failed to get run URL: {e}")
        return None
    
    def log_run_info(self, run_id: str, query: str):
        """Log information about a traced run.
        
        Args:
            run_id: Run ID
            query: Query being researched
        """
        if self.enabled:
            url = self.get_run_url(run_id)
            if url:
                logger.info(f"Trace for '{query}': {url}")


# Global tracing manager instance
tracing_manager = TracingManager()


def enable_tracing(api_key: Optional[str] = None, project: str = "deep-research"):
    """Enable LangSmith tracing globally.
    
    Args:
        api_key: LangSmith API key
        project: Project name
    """
    tracing_manager.enable_tracing(api_key, project)


def disable_tracing():
    """Disable LangSmith tracing globally."""
    tracing_manager.disable_tracing()


def is_tracing_enabled() -> bool:
    """Check if tracing is enabled.
    
    Returns:
        True if tracing is enabled
    """
    return tracing_manager.enabled

if __name__ == "__main__":
    enable_tracing()
    print(is_tracing_enabled())
    disable_tracing()
    print(is_tracing_enabled())