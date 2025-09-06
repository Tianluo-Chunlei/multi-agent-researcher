"""Base agent class for Deep Research system."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from langsmith import traceable
from src.utils.logger import logger
from src.utils.config import config
from src.utils.rate_limiter import APIRetry, anthropic_rate_limited


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(
        self, 
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        memory_store: Optional[Dict] = None
    ):
        """Initialize base agent.
        
        Args:
            model: Model to use for this agent
            tools: List of tools available to this agent
            memory_store: Memory storage for the agent
        """
        # Initialize Anthropic client with optional base URL
        client_kwargs = {"api_key": config.anthropic_api_key}
        if config.anthropic_base_url:
            client_kwargs["base_url"] = config.anthropic_base_url
        
        self.client = Anthropic(**client_kwargs)
        self.model = model or config.subagent_model
        self.tools = tools or []
        self.memory = memory_store or {}
        self.token_count = 0
        self.conversation_history = []
        
        logger.info(f"Initialized {self.__class__.__name__} with model {self.model}")
    
    @traceable(name="agent_think")
    async def think(self, context: str, extended: bool = False) -> str:
        """Extended thinking mode for complex reasoning.
        
        Args:
            context: The context to think about
            extended: Whether to use extended thinking mode
            
        Returns:
            The agent's thoughts
        """
        if extended:
            prompt = f"""<thinking>
{context}

Please think through this step by step, considering all aspects carefully and thoroughly.
Take your time to reason through the problem.
</thinking>"""
        else:
            prompt = f"""<thinking>
{context}

Please think through this carefully.
</thinking>"""
        
        response = await self._call_llm(prompt, temperature=0.2)
        return response
    
    @traceable(name="agent_act")
    async def act(self, task: str) -> Dict[str, Any]:
        """Execute a task.
        
        Args:
            task: The task to execute
            
        Returns:
            Result of the task execution
        """
        result = await self.execute_task(task)
        return result
    
    @abstractmethod
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Execute a specific task. Must be implemented by subclasses.
        
        Args:
            task: The task to execute
            
        Returns:
            Result of the task execution
        """
        pass
    
    @traceable(name="llm_call")
    @APIRetry.with_retry(max_attempts=3, wait_multiplier=2)
    @anthropic_rate_limited(tokens=1)
    async def _call_llm(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system: Optional[str] = None
    ) -> str:
        """Make a call to the LLM.
        
        Args:
            prompt: The prompt to send
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            system: System prompt
            
        Returns:
            The LLM response
        """
        messages = [{"role": "user", "content": prompt}]
        
        # Add conversation history if available
        if self.conversation_history:
            messages = self.conversation_history + messages
        
        try:
            response = self.client.messages.create(
                model=self.model,
                messages=messages,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Track token usage
            self.token_count += response.usage.input_tokens + response.usage.output_tokens
            
            # Store in conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": response.content[0].text})
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def get_token_usage(self) -> int:
        """Get total token usage for this agent.
        
        Returns:
            Total tokens used
        """
        return self.token_count
    
    def reset_conversation(self):
        """Reset conversation history."""
        self.conversation_history = []
        logger.debug(f"Reset conversation history for {self.__class__.__name__}")
    
    def save_to_memory(self, key: str, value: Any):
        """Save information to memory.
        
        Args:
            key: Memory key
            value: Value to store
        """
        self.memory[key] = value
        logger.debug(f"Saved to memory: {key}")
    
    def get_from_memory(self, key: str) -> Any:
        """Retrieve information from memory.
        
        Args:
            key: Memory key
            
        Returns:
            Stored value or None
        """
        return self.memory.get(key)