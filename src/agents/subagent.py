"""Research Subagent implementation."""

from typing import Dict, List, Any, Optional
import asyncio
import json

from src.agents.base import BaseAgent
from src.managers.tool_manager import ToolManager
from src.utils.logger import logger
from src.utils.config import config


class ResearchSubagent(BaseAgent):
    """Subagent that performs specific research tasks."""
    
    def __init__(
        self,
        agent_id: str,
        task_description: str,
        tools: Optional[List[str]] = None
    ):
        """Initialize research subagent.
        
        Args:
            agent_id: Unique agent identifier
            task_description: Description of the research task
            tools: List of tool names to use
        """
        # Use Sonnet model for subagents
        super().__init__(model=config.subagent_model)
        
        self.agent_id = agent_id
        self.task_description = task_description
        
        # Initialize tools
        self.tool_manager = ToolManager()
        if tools:
            self.tool_names = tools
        else:
            self.tool_names = ["web_search", "web_fetch", "memory_store"]
        
        # Calculate tool budget based on task
        self.tool_budget = self._calculate_tool_budget()
        self.tool_calls_made = 0
        
        # Research results
        self.findings = []
        self.sources = []
        
        logger.info(f"Initialized subagent {agent_id} with budget: {self.tool_budget} calls")
    
    def _calculate_tool_budget(self) -> int:
        """Calculate tool call budget based on task complexity."""
        # Simple heuristic based on task description length and keywords
        task_lower = self.task_description.lower()
        
        if any(word in task_lower for word in ["comprehensive", "detailed", "all", "complete"]):
            return 15
        elif any(word in task_lower for word in ["compare", "analyze", "multiple"]):
            return 10
        elif any(word in task_lower for word in ["find", "search", "identify"]):
            return 7
        else:
            return 5
    
    async def execute_research(self) -> Dict[str, Any]:
        """Execute the research task.
        
        Returns:
            Research results
        """
        logger.info(f"Subagent {self.agent_id} starting research: {self.task_description[:100]}")
        
        try:
            # Plan research approach
            plan = await self._plan_research()
            
            # Execute OODA loop
            iteration = 0
            max_iterations = min(self.tool_budget, 15)
            
            while iteration < max_iterations and self.tool_calls_made < self.tool_budget:
                iteration += 1
                
                # Observe current state
                observation = await self._observe()
                
                # Orient - analyze what we have and need
                orientation = await self._orient(observation)
                
                # Decide - determine next action
                decision = await self._decide(orientation)
                
                if decision.get("complete", False):
                    break
                
                # Act - execute the decision
                await self._act(decision)
                
                # Check if we have enough information
                if len(self.findings) >= 5:  # Reasonable amount of findings
                    logger.info(f"Subagent {self.agent_id}: Sufficient findings collected")
                    break
            
            # Compile final results
            results = await self._compile_results()
            
            logger.info(f"Subagent {self.agent_id} completed: {len(self.findings)} findings, {self.tool_calls_made} tool calls")
            
            return results
            
        except Exception as e:
            logger.error(f"Subagent {self.agent_id} failed: {e}")
            return {
                "error": str(e),
                "findings": self.findings,
                "sources": self.sources
            }
    
    async def _plan_research(self) -> Dict[str, Any]:
        """Plan the research approach."""
        prompt = f"""Plan how to research this task efficiently.

Task: {self.task_description}
Available tools: {', '.join(self.tool_names)}
Tool budget: {self.tool_budget} calls

Create a research plan with:
1. Key information to find
2. Search strategies
3. Sources to prioritize

Be concise and focused."""

        response = await self._call_llm(prompt, temperature=0.3, max_tokens=500)
        
        return {"plan": response}
    
    async def _observe(self) -> Dict[str, Any]:
        """Observe current research state."""
        return {
            "findings_count": len(self.findings),
            "sources_count": len(self.sources),
            "tool_calls_remaining": self.tool_budget - self.tool_calls_made,
            "current_findings": self.findings[-3:] if self.findings else []
        }
    
    async def _orient(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Orient based on observations."""
        if not self.findings:
            return {"stage": "initial", "need": "broad search"}
        elif observation["findings_count"] < 3:
            return {"stage": "gathering", "need": "more sources"}
        else:
            return {"stage": "refining", "need": "specific details"}
    
    async def _decide(self, orientation: Dict[str, Any]) -> Dict[str, Any]:
        """Decide next action based on orientation."""
        if self.tool_calls_made >= self.tool_budget:
            return {"complete": True}
        
        if orientation["stage"] == "initial":
            # Start with web search
            return {
                "action": "search",
                "query": self._extract_search_query(),
                "complete": False
            }
        elif orientation["stage"] == "gathering":
            # Continue searching or fetch specific pages
            if self.sources and "web_fetch" in self.tool_names:
                return {
                    "action": "fetch",
                    "url": self.sources[0]["url"] if self.sources else None,
                    "complete": False
                }
            else:
                return {
                    "action": "search",
                    "query": self._extract_search_query(),
                    "complete": False
                }
        else:
            # Check if we have enough
            if len(self.findings) >= 3:
                return {"complete": True}
            else:
                return {
                    "action": "search",
                    "query": self._refine_search_query(),
                    "complete": False
                }
    
    async def _act(self, decision: Dict[str, Any]) -> None:
        """Act on the decision."""
        if decision.get("complete"):
            return
        
        action = decision.get("action")
        
        if action == "search":
            await self._perform_search(decision.get("query", self.task_description))
        elif action == "fetch":
            url = decision.get("url")
            if url:
                await self._fetch_page(url)
    
    async def _perform_search(self, query: str) -> None:
        """Perform web search."""
        if self.tool_calls_made >= self.tool_budget:
            return
        
        logger.debug(f"Subagent {self.agent_id} searching: {query}")
        
        try:
            result = await self.tool_manager.execute_tool(
                "web_search",
                query=query,
                max_results=5
            )
            
            self.tool_calls_made += 1
            
            if result.get("success") and result.get("data"):
                data = result["data"]
                results = data.get("results", [])
                
                for item in results:
                    finding = {
                        "title": item.get("title", ""),
                        "content": item.get("snippet", ""),
                        "url": item.get("url", ""),
                        "source": "web_search"
                    }
                    self.findings.append(finding)
                    
                    if item.get("url"):
                        self.sources.append({
                            "title": item.get("title", ""),
                            "url": item.get("url")
                        })
                
                logger.debug(f"Subagent {self.agent_id} found {len(results)} results")
                
        except Exception as e:
            logger.error(f"Search failed for subagent {self.agent_id}: {e}")
    
    async def _fetch_page(self, url: str) -> None:
        """Fetch a specific web page."""
        if self.tool_calls_made >= self.tool_budget:
            return
        
        if "web_fetch" not in self.tool_names:
            return
        
        logger.debug(f"Subagent {self.agent_id} fetching: {url}")
        
        try:
            result = await self.tool_manager.execute_tool(
                "web_fetch",
                url=url
            )
            
            self.tool_calls_made += 1
            
            if result.get("success") and result.get("data"):
                data = result["data"]
                
                finding = {
                    "title": data.get("title", ""),
                    "content": data.get("content", "")[:3000],  # Limit content
                    "url": url,
                    "source": "web_fetch"
                }
                self.findings.append(finding)
                
                logger.debug(f"Subagent {self.agent_id} fetched page successfully")
                
        except Exception as e:
            logger.error(f"Fetch failed for subagent {self.agent_id}: {e}")
    
    def _extract_search_query(self) -> str:
        """Extract search query from task description."""
        # Simple extraction - in production, use LLM for better queries
        words = self.task_description.split()[:10]
        return ' '.join(words)
    
    def _refine_search_query(self) -> str:
        """Refine search query based on current findings."""
        # Simple refinement - in production, use LLM
        base_query = self._extract_search_query()
        return f"{base_query} details specific"
    
    async def _compile_results(self) -> Dict[str, Any]:
        """Compile final research results."""
        if not self.findings:
            return {
                "findings": [],
                "sources": [],
                "summary": "No findings collected"
            }
        
        # Create summary of findings
        prompt = f"""Summarize these research findings for the task.

Task: {self.task_description}

Findings:
{json.dumps(self.findings[:10], indent=2)}

Create a concise summary of the key information found."""

        summary = await self._call_llm(prompt, temperature=0.3, max_tokens=500)
        
        return {
            "findings": self.findings,
            "sources": self.sources,
            "summary": summary,
            "tool_calls": self.tool_calls_made,
            "agent_id": self.agent_id
        }
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Execute a task (required by base class).
        
        Args:
            task: Task to execute
            
        Returns:
            Research results
        """
        self.task_description = task
        return await self.execute_research()