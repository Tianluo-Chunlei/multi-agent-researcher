"""Lead Research Agent implementation."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from src.agents.base import BaseAgent
from src.managers.tool_manager import ToolManager
from src.utils.logger import logger
from src.utils.config import config


class LeadResearchAgent(BaseAgent):
    """Lead agent that coordinates the research process."""
    
    def __init__(self):
        """Initialize lead research agent."""
        # Use Opus model for lead agent
        super().__init__(model=config.lead_agent_model)
        
        # Initialize tool manager
        self.tool_manager = ToolManager()
        self.tools = self.tool_manager.get_tools_for_agent("lead")
        
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze a research query to determine type and complexity.
        
        Args:
            query: The research query
            
        Returns:
            Analysis results including query type and complexity
        """
        logger.info("Analyzing query...")
        
        prompt = f"""Analyze this research query and determine its type and complexity.

Query: {query}

Classify the query type as one of:
- "depth-first": Requires multiple perspectives on the same issue
- "breadth-first": Can be broken into distinct, independent sub-questions  
- "straightforward": Focused, well-defined, can be answered by single investigation

Classify the complexity as one of:
- "simple": 1 subagent, basic fact-finding
- "standard": 2-3 subagents, multiple perspectives
- "medium": 3-5 subagents, multi-faceted
- "high": 5-20 subagents, very broad with many components

Respond in JSON format:
{{
    "query_type": "...",
    "complexity": "...",
    "reasoning": "..."
}}"""

        response = await self._call_llm(prompt, temperature=0.3)
        
        try:
            # Parse JSON response
            analysis = json.loads(response)
            
            # Validate fields
            if "query_type" not in analysis:
                analysis["query_type"] = "straightforward"
            if "complexity" not in analysis:
                analysis["complexity"] = "simple"
                
            logger.info(f"Query analysis: type={analysis['query_type']}, complexity={analysis['complexity']}")
            return analysis
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse analysis JSON, using defaults")
            return {
                "query_type": "straightforward",
                "complexity": "simple",
                "reasoning": "Failed to parse analysis"
            }
    
    async def create_research_plan(
        self, 
        query: str,
        query_type: str,
        complexity: str
    ) -> Dict[str, Any]:
        """Create a detailed research plan.
        
        Args:
            query: The research query
            query_type: Type of query
            complexity: Query complexity
            
        Returns:
            Research plan with tasks
        """
        logger.info(f"Creating research plan for {complexity} {query_type} query...")
        
        # Determine subagent count based on complexity
        subagent_counts = {
            "simple": 1,
            "standard": 3,
            "medium": 5,
            "high": 10
        }
        subagent_count = subagent_counts.get(complexity, 3)
        
        prompt = f"""Create a detailed research plan for this query.

Query: {query}
Query Type: {query_type}
Complexity: {complexity}
Suggested Subagents: {subagent_count}

Based on the query type and complexity, create {subagent_count} specific research tasks.
Each task should have:
- A clear, specific objective
- Suggested search queries or sources
- Expected output format

For {query_type} queries:
{self._get_query_type_guidance(query_type)}

Respond in JSON format:
{{
    "subagent_count": {subagent_count},
    "tasks": [
        {{
            "description": "Specific research task description",
            "search_queries": ["query1", "query2"],
            "expected_output": "What this task should produce",
            "tools": ["web_search", "web_fetch"]
        }}
    ],
    "synthesis_approach": "How to combine the results"
}}"""

        response = await self._call_llm(prompt, temperature=0.5)
        
        try:
            plan = json.loads(response)
            
            # Ensure required fields
            if "tasks" not in plan or not plan["tasks"]:
                plan["tasks"] = [{
                    "description": f"Research: {query}",
                    "search_queries": [query],
                    "expected_output": "Comprehensive information",
                    "tools": ["web_search", "web_fetch"]
                }]
            
            plan["subagent_count"] = len(plan["tasks"])
            
            logger.info(f"Created plan with {plan['subagent_count']} tasks")
            return plan
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse plan JSON, creating default plan")
            return {
                "subagent_count": 1,
                "tasks": [{
                    "description": f"Research: {query}",
                    "search_queries": [query],
                    "expected_output": "Comprehensive information",
                    "tools": ["web_search", "web_fetch"]
                }],
                "synthesis_approach": "Combine all findings"
            }
    
    def _get_query_type_guidance(self, query_type: str) -> str:
        """Get guidance for specific query type."""
        guidance = {
            "depth-first": """
- Create tasks that explore different perspectives/methodologies
- Each task should approach the core question from a unique angle
- Focus on depth rather than breadth""",
            
            "breadth-first": """
- Break into distinct, independent sub-topics
- Each task should cover a separate aspect
- Ensure clear boundaries between tasks to avoid overlap""",
            
            "straightforward": """
- Create focused task(s) for direct information gathering
- Include verification/fact-checking if needed
- Keep scope narrow and well-defined"""
        }
        return guidance.get(query_type, "")
    
    async def evaluate_completeness(
        self, 
        query: str,
        results: List[Dict],
        iteration: int
    ) -> Dict[str, Any]:
        """Evaluate if research results are complete.
        
        Args:
            query: Original query
            results: Current results
            iteration: Current iteration number
            
        Returns:
            Evaluation including whether more research is needed
        """
        logger.info(f"Evaluating completeness (iteration {iteration})...")
        
        # Summarize results for evaluation
        results_summary = self._summarize_results(results)
        
        prompt = f"""Evaluate if the research results are sufficient to answer the query.

Original Query: {query}
Current Iteration: {iteration}
Results Found: {len(results)} items

Results Summary:
{results_summary}

Evaluate:
1. Does the information fully answer the query?
2. Are there important gaps or missing perspectives?
3. Is the information credible and well-sourced?

Respond in JSON format:
{{
    "is_complete": true/false,
    "needs_more": true/false,
    "completeness_score": 0.0-1.0,
    "missing_aspects": ["aspect1", "aspect2"],
    "additional_tasks": [
        {{
            "description": "Additional research needed",
            "search_queries": ["query"],
            "tools": ["web_search"]
        }}
    ]
}}"""

        response = await self._call_llm(prompt, temperature=0.3)
        
        try:
            evaluation = json.loads(response)
            
            # Default values
            if "needs_more" not in evaluation:
                evaluation["needs_more"] = evaluation.get("completeness_score", 0.5) < 0.8
                
            logger.info(f"Completeness: {evaluation.get('completeness_score', 0)}, Needs more: {evaluation['needs_more']}")
            return evaluation
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse evaluation JSON")
            return {
                "is_complete": iteration >= 2,
                "needs_more": iteration < 2,
                "completeness_score": 0.5,
                "missing_aspects": [],
                "additional_tasks": []
            }
    
    def _summarize_results(self, results: List[Dict]) -> str:
        """Summarize results for evaluation."""
        if not results:
            return "No results found yet."
        
        summary = []
        for i, result in enumerate(results[:10], 1):  # Limit to first 10
            if isinstance(result, dict):
                title = result.get("title", "Untitled")
                content = result.get("content", result.get("snippet", ""))[:200]
                summary.append(f"{i}. {title}: {content}...")
            else:
                summary.append(f"{i}. {str(result)[:200]}...")
        
        return "\n".join(summary)
    
    async def synthesize_results(
        self,
        query: str,
        results: List[Dict],
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize research results into a coherent report.
        
        Args:
            query: Original query
            results: All research results
            plan: Research plan
            
        Returns:
            Synthesized report and sources
        """
        logger.info(f"Synthesizing {len(results)} results...")
        
        # Prepare results for synthesis
        formatted_results = self._format_results_for_synthesis(results)
        
        prompt = f"""Synthesize the research results into a comprehensive report.

Original Query: {query}
Research Plan: {plan.get('synthesis_approach', 'Combine all findings')}

Research Results:
{formatted_results}

Create a well-structured report that:
1. Directly answers the query
2. Integrates information from all sources
3. Highlights key findings and insights
4. Maintains factual accuracy
5. Provides a balanced perspective

Format the report in markdown with clear sections.
Do not include citations in the text - they will be added later.

After the report, list the sources used in JSON format."""

        response = await self._call_llm(prompt, temperature=0.5, max_tokens=8000)
        
        # Extract report and sources
        report, sources = self._extract_report_and_sources(response)
        
        logger.info(f"Synthesized report: {len(report)} chars, {len(sources)} sources")
        
        return {
            "report": report,
            "sources": sources
        }
    
    def _format_results_for_synthesis(self, results: List[Dict]) -> str:
        """Format results for synthesis."""
        formatted = []
        
        for i, result in enumerate(results, 1):
            if isinstance(result, dict):
                source = result.get("url", result.get("source", f"Source {i}"))
                title = result.get("title", "")
                content = result.get("content", result.get("snippet", ""))
                
                formatted.append(f"""
Source {i}: {source}
Title: {title}
Content: {content}
---""")
            else:
                formatted.append(f"Source {i}: {str(result)}\n---")
        
        return "\n".join(formatted[:50])  # Limit to 50 sources
    
    def _extract_report_and_sources(self, response: str) -> tuple:
        """Extract report and sources from response."""
        # Try to find JSON sources at the end
        lines = response.split('\n')
        
        report_lines = []
        sources = []
        in_json = False
        json_buffer = []
        
        for line in lines:
            if line.strip().startswith('[') or line.strip().startswith('{'):
                in_json = True
            
            if in_json:
                json_buffer.append(line)
            else:
                report_lines.append(line)
        
        report = '\n'.join(report_lines).strip()
        
        # Try to parse sources
        if json_buffer:
            try:
                sources_text = '\n'.join(json_buffer)
                sources = json.loads(sources_text)
                if not isinstance(sources, list):
                    sources = [sources]
            except:
                sources = []
        
        # If no sources found, create from results
        if not sources:
            sources = [{"title": "Research Finding", "url": "research"}]
        
        return report, sources
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Execute a task (required by base class).
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        # Lead agent primarily coordinates, not executes
        return {
            "status": "Lead agent coordinates research",
            "task": task
        }