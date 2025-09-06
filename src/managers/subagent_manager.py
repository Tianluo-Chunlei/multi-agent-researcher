"""Subagent manager for coordinating multiple research agents."""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from src.agents.subagent import ResearchSubagent
from src.utils.logger import logger
from src.utils.config import config


class SubagentManager:
    """Manager for creating and coordinating subagents."""
    
    def __init__(self, max_concurrent: Optional[int] = None):
        """Initialize subagent manager.
        
        Args:
            max_concurrent: Maximum concurrent subagents
        """
        self.max_concurrent = max_concurrent or config.max_concurrent_subagents
        self.active_agents: Dict[str, ResearchSubagent] = {}
        self.completed_agents: Dict[str, Dict] = {}
        self.agent_results: Dict[str, Any] = {}
        
    async def create_subagent(self, task: Dict[str, Any]) -> str:
        """Create a new subagent for a task.
        
        Args:
            task: Task description and parameters
            
        Returns:
            Agent ID
        """
        agent_id = str(uuid.uuid4())[:8]
        
        # Create subagent
        subagent = ResearchSubagent(
            agent_id=agent_id,
            task_description=task.get('description', ''),
            tools=task.get('tools', [])
        )
        
        self.active_agents[agent_id] = subagent
        
        logger.info(f"Created subagent {agent_id} for task: {task.get('description', '')[:100]}")
        
        return agent_id
    
    async def dispatch_agents(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Dispatch multiple subagents for tasks.
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            List of agent IDs
        """
        agent_ids = []
        
        for task in tasks:
            agent_id = await self.create_subagent(task)
            agent_ids.append(agent_id)
        
        logger.info(f"Dispatched {len(agent_ids)} subagents")
        
        return agent_ids
    
    async def execute_parallel(
        self, 
        agent_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Execute multiple subagents in parallel.
        
        Args:
            agent_ids: List of agent IDs to execute
            
        Returns:
            Results from all agents
        """
        logger.info(f"Executing {len(agent_ids)} subagents in parallel...")
        
        # Create tasks for parallel execution
        tasks = []
        for agent_id in agent_ids:
            if agent_id in self.active_agents:
                agent = self.active_agents[agent_id]
                tasks.append(self._execute_single_agent(agent_id, agent))
        
        # Execute in batches based on max_concurrent
        results = {}
        for i in range(0, len(tasks), self.max_concurrent):
            batch = tasks[i:i + self.max_concurrent]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            # Process batch results
            for j, result in enumerate(batch_results):
                agent_id = agent_ids[i + j]
                if isinstance(result, Exception):
                    logger.error(f"Subagent {agent_id} failed: {result}")
                    results[agent_id] = {
                        "success": False,
                        "error": str(result)
                    }
                else:
                    results[agent_id] = result
        
        return results
    
    async def _execute_single_agent(
        self, 
        agent_id: str, 
        agent: ResearchSubagent
    ) -> Dict[str, Any]:
        """Execute a single subagent.
        
        Args:
            agent_id: Agent ID
            agent: Subagent instance
            
        Returns:
            Agent execution result
        """
        try:
            start_time = datetime.now()
            
            # Execute research
            result = await agent.execute_research()
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Store result
            final_result = {
                "success": True,
                "agent_id": agent_id,
                "findings": result.get("findings", []),
                "sources": result.get("sources", []),
                "execution_time": execution_time,
                "tokens_used": agent.get_token_usage()
            }
            
            # Move to completed
            self.completed_agents[agent_id] = final_result
            del self.active_agents[agent_id]
            
            logger.info(f"Subagent {agent_id} completed in {execution_time:.2f}s")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Subagent {agent_id} execution failed: {e}")
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e)
            }
    
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get the status of a specific agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent status
        """
        if agent_id in self.active_agents:
            return {
                "agent_id": agent_id,
                "status": "active",
                "task": self.active_agents[agent_id].task_description
            }
        elif agent_id in self.completed_agents:
            return {
                "agent_id": agent_id,
                "status": "completed",
                "result": self.completed_agents[agent_id]
            }
        else:
            return {
                "agent_id": agent_id,
                "status": "not_found"
            }
    
    def get_all_results(self) -> Dict[str, Any]:
        """Get results from all completed agents.
        
        Returns:
            All completed agent results
        """
        return self.completed_agents.copy()
    
    def clear_completed(self):
        """Clear completed agents from memory."""
        self.completed_agents.clear()
        logger.debug("Cleared completed agents")
    
    async def shutdown(self):
        """Shutdown all active agents."""
        for agent_id in list(self.active_agents.keys()):
            logger.info(f"Shutting down agent {agent_id}")
            del self.active_agents[agent_id]
        
        logger.info("Subagent manager shutdown complete")