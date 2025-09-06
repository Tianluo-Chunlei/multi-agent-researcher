"""Multi-Agent System using LangGraph with proper subagents."""

from typing import Dict, Any, List, Optional
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
import asyncio
import os
from datetime import datetime
import re

from src.utils.config import config
from src.utils.logger import logger
from src.react_agents.prompts import get_lead_agent_prompt, get_subagent_prompt, get_citation_prompt
from src.tools.search import WebSearchTool, WebFetchTool


class ResearchSubAgent:
    """Research SubAgent that performs specific research tasks."""
    
    def __init__(self, agent_id: str = "subagent"):
        """Initialize Research SubAgent."""
        self.agent_id = agent_id
        
        # Use Sonnet model for subagent (faster and cheaper)
        self.llm = ChatAnthropic(
            model=config.subagent_model,
            temperature=0.3,
            max_tokens=4000,
            anthropic_api_key=config.anthropic_api_key,
            base_url=config.anthropic_base_url if config.anthropic_base_url else None
        )
        
        # Initialize tools
        self.tools = self._get_tools()
        
        # Create React agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self._get_prompt()
        )
        
        logger.info(f"Research SubAgent {agent_id} initialized")
    
    def _get_prompt(self) -> str:
        """Get prompt for subagent."""
        return get_subagent_prompt()
    
    def _get_tools(self):
        """Get tools for subagent."""
        tools = []
        
        # Initialize search and fetch tools from src/tools/search.py
        search_tool = WebSearchTool()
        fetch_tool = WebFetchTool()
        
        # Create wrapper tools for LangChain
        @tool
        async def web_search(query: str) -> str:
            """Search the web for information.
            
            Args:
                query: Search query
                
            Returns:
                Search results
            """
            result = await search_tool(query=query, max_results=5)
            if result.get("success", False):
                data = result.get("data", {})
                results = data.get("results", [])
                # Format results for agent
                output = []
                for r in results[:5]:
                    output.append(f"Title: {r.get('title', '')}\nURL: {r.get('url', '')}\nSnippet: {r.get('snippet', '')}\n")
                return "\n---\n".join(output) if output else "No results found"
            else:
                return f"Search failed: {result.get('error', 'Unknown error')}"
        
        @tool
        async def fetch_webpage(url: str) -> str:
            """Fetch content from a webpage.
            
            Args:
                url: URL to fetch
                
            Returns:
                Webpage content with title and snippet for citation purposes
            """
            result = await fetch_tool(url=url)
            if result.get("success", False):
                data = result.get("data", {})
                content = data.get("content", "")
                title = data.get("title", "")
                
                # Create a snippet for citation mapping (first 200 chars of content)
                snippet = content[:200] if content else ""
                
                # Store source info for citation (this will be accessible to the agent)
                source_info = {
                    "url": url,
                    "title": title,
                    "snippet": snippet
                }
                
                # Return formatted content for the agent
                return f"Title: {title}\n\nContent:\n{content[:5000]}" if content else "No content found"
            else:
                return f"Fetch failed: {result.get('error', 'Unknown error')}"
        
        tools.append(web_search)
        tools.append(fetch_webpage)
        return tools
    
    def _extract_source_info_from_response(self, response: str, sources: List[str]) -> None:
        """Extract source information from AI response content.
        
        Args:
            response: The AI response content
            sources: List to update with enhanced source information
        """
        import re
        
        # Look for "Title: X" patterns in the response
        title_pattern = r"Title:\s*([^\n]+)"
        titles = re.findall(title_pattern, response)
        
        # If we found titles and have URLs, try to match them
        if titles and sources:
            # For now, we'll enhance the sources list with title information
            # This is a simplified approach - in a more sophisticated system,
            # we'd track the relationship between fetch calls and their results
            for i, title in enumerate(titles):
                if i < len(sources):
                    # Convert string URL to dict with title if it's still a string
                    if isinstance(sources[i], str):
                        sources[i] = {
                            "url": sources[i],
                            "title": title.strip(),
                            "snippet": ""
                        }
    
    async def research(self, task: str) -> Dict[str, Any]:
        """Execute a research task.
        
        Args:
            task: The specific research task
            
        Returns:
            Research findings
        """
        logger.info(f"📚 SubAgent {self.agent_id} starting task: {task[:80]}...")
        
        try:
            # Log execution start
            logger.debug(f"SubAgent {self.agent_id} invoking LangGraph agent...")
            
            result = await self.agent.ainvoke({
                "messages": [{"role": "user", "content": task}]
            })
            
            # Extract findings
            findings = ""
            sources = []
            tool_calls_count = 0
            
            if result.get("messages"):
                logger.debug(f"SubAgent {self.agent_id} received {len(result['messages'])} messages")
                
                for msg in result["messages"]:
                    # Log tool calls and extract source information
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tool_name = tool_call.get("name", "unknown")
                            tool_calls_count += 1
                            
                            if tool_name == "web_search":
                                query = tool_call.get("args", {}).get("query", "")
                                logger.info(f"  🔍 SubAgent {self.agent_id} searching: {query}")
                            elif tool_name == "fetch_webpage":
                                url = tool_call.get("args", {}).get("url", "")
                                logger.info(f"  📄 SubAgent {self.agent_id} fetching: {url[:60]}...")
                                if url:
                                    # For now, store URL - we'll enhance this with actual fetch results
                                    sources.append(url)
                    
                    # Extract AI response and look for source information in the content
                    if msg.type == "ai" and msg.content:
                        findings = msg.content
                        logger.debug(f"SubAgent {self.agent_id} generated {len(findings)} chars response")
                        
                        # Try to extract source information from the AI response
                        # The AI response might contain "Title: X" patterns from fetch_webpage results
                        self._extract_source_info_from_response(findings, sources)
            
            logger.info(f"✅ SubAgent {self.agent_id} completed: {tool_calls_count} tool calls, {len(sources)} sources")
            
            return {
                "success": True,
                "agent_id": self.agent_id,
                "task": task,
                "findings": findings,
                "sources": sources,
                "tool_calls": tool_calls_count
            }
            
        except Exception as e:
            logger.error(f"SubAgent {self.agent_id} failed: {e}")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "task": task,
                "error": str(e)
            }


class CitationAgent:
    """Agent that adds citations to research reports."""
    
    def __init__(self):
        """Initialize Citation Agent."""
        self.llm = ChatAnthropic(
            model=config.citation_model,
            temperature=0.1,
            max_tokens=8000,
            anthropic_api_key=config.anthropic_api_key,
            base_url=config.anthropic_base_url if config.anthropic_base_url else None
        )
        
        logger.info("Citation Agent initialized")
    
    async def add_citations(
        self,
        report: str,
        sources: List[Any]
    ) -> str:
        """Add citations to a report.
        
        Args:
            report: The research report
            sources: List of source information (URLs or dicts with url/title/snippet)
            
        Returns:
            Report with citations
        """
        if not sources:
            return report
        
        # Format sources - handle both old format (strings) and new format (dicts)
        sources_text = ""
        for i, source in enumerate(sources):
            if isinstance(source, dict):
                url = source.get("url", "")
                title = source.get("title", "")
                snippet = source.get("snippet", "")
                if title:
                    sources_text += f"[{i+1}] {title} - {url}\n"
                else:
                    sources_text += f"[{i+1}] {url}\n"
            else:
                # Backward compatibility with string URLs
                sources_text += f"[{i+1}] {source}\n"
        
        # Use the citation prompt from prompts.py
        base_prompt = get_citation_prompt()
        
        # Combine with the specific task
        prompt = f"""{base_prompt}

<synthesized_text>
{report}
</synthesized_text>

<sources>
{sources_text}
</sources>

"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            cited_report = response.content
            
            # Ensure sources section exists
            if "## Sources" not in cited_report and "## References" not in cited_report:
                cited_report += f"\n\n## Sources\n{sources_text}"
            
            return cited_report
            
        except Exception as e:
            logger.error(f"Citation failed: {e}")
            return report + f"\n\n## Sources\n{sources_text}"


class MultiAgentLeadResearcher:
    """Lead Agent that coordinates multiple subagents."""
    
    def __init__(self):
        """Initialize Lead Agent."""
        # Use Opus for lead agent (better reasoning)
        self.llm = ChatAnthropic(
            model=config.lead_agent_model,
            temperature=0.5,
            max_tokens=8000,
            anthropic_api_key=config.anthropic_api_key,
            base_url=config.anthropic_base_url if config.anthropic_base_url else None
        )
        
        # Tools including subagent deployment and citation
        self.tools = self._get_tools()
        
        # Create React agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self._get_lead_prompt()
        )
        
        logger.info("Multi-Agent Lead Researcher initialized")
    
    def _get_lead_prompt(self) -> str:
        """Get prompt for lead agent."""
        # Use the prompt from prompts.py but emphasize using run_subagents tool
        base_prompt = get_lead_agent_prompt()
        # Replace the tool usage section to match our actual tools
        return base_prompt.replace(
            "**run_subagent**: Deploy research subagents with specific tasks",
            "**run_subagents**: Deploy multiple research subagents in parallel with specific tasks"
        )
    
    def _get_tools(self):
        """Get tools for lead agent."""
        tools = []
        
        # Initialize citation agent for use as a tool
        citation_agent = CitationAgent()
        
        @tool
        async def run_subagents(tasks: List[str]) -> List[Dict[str, Any]]:
            """Deploy multiple research subagents in parallel.
            
            Args:
                tasks: List of specific research tasks for subagents
                
            Returns:
                List of research findings from all subagents
            """
            logger.info(f"🚀 Deploying {len(tasks)} subagents in parallel...")
            logger.info("📋 Tasks assigned:")
            for i, task in enumerate(tasks):
                logger.info(f"  {i+1}. {task[:100]}...")
            
            # Create subagents
            subagents = [
                ResearchSubAgent(agent_id=f"subagent_{i}")
                for i in range(len(tasks))
            ]
            
            # Run all subagents in parallel
            logger.info("⚡ Executing subagents in parallel...")
            results = await asyncio.gather(*[
                agent.research(task)
                for agent, task in zip(subagents, tasks)
            ])
            
            # Log results summary
            successful = sum(1 for r in results if r.get("success"))
            total_sources = sum(len(r.get("sources", [])) for r in results)
            total_tool_calls = sum(r.get("tool_calls", 0) for r in results)
            
            logger.info(f"✅ All {len(tasks)} subagents completed:")
            logger.info(f"  - Successful: {successful}/{len(tasks)}")
            logger.info(f"  - Total sources collected: {total_sources}")
            logger.info(f"  - Total tool calls made: {total_tool_calls}")
            
            return results
        
        @tool
        async def add_citations(report: str, sources: List[Any]) -> str:
            """Add citations to a research report.
            
            Args:
                report: The research report text
                sources: List of source information (URLs or dicts with url/title/snippet)
                
            Returns:
                Report with citations added
            """
            logger.info(f"🔖 Adding citations to report with {len(sources)} sources")
            cited_report = await citation_agent.add_citations(report, sources)
            logger.info("✅ Citations added successfully")
            return cited_report
        
        tools.append(run_subagents)
        tools.append(add_citations)
        return tools
    
    async def research(self, query: str) -> Dict[str, Any]:
        """Execute a research query using multiple agents.
        
        Args:
            query: The research query
            
        Returns:
            Final research report with citations
        """
        logger.info(f"🎯 Starting multi-agent research: {query[:100]}...")
        start_time = datetime.now()
        
        try:
            # Lead agent orchestrates the entire research process
            logger.info("📊 Lead agent orchestrating research process...")
            
            result = await self.agent.ainvoke({
                "messages": [{
                    "role": "user",
                    "content": f"""Research this query comprehensively: {query}."""
                }]
            })
            
            logger.info(f"📝 Lead agent processed {len(result.get('messages', []))} messages")
            
            # Extract final report
            final_report = ""
            sources_found = []
            
            if result.get("messages"):
                # Get the last AI message which should contain the final report
                for msg in reversed(result["messages"]):
                    if msg.type == "ai" and msg.content:
                        final_report = msg.content
                        break
                
                # Extract sources from the research process
                for msg in result["messages"]:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            # Log tool usage
                            tool_name = tool_call.get("name", "")
                            if tool_name == "run_subagents":
                                logger.info("✅ Subagents deployed")
                            elif tool_name == "add_citations":
                                logger.info("✅ Citations added")
                                # Extract sources from citation tool call
                                sources = tool_call.get("args", {}).get("sources", [])
                                sources_found.extend(sources)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"🎉 Multi-agent research completed in {execution_time:.2f}s")
            logger.info(f"📊 Final report: {len(final_report)} characters")
            logger.info(f"📚 Sources cited: {len(sources_found)}")
            
            return {
                "success": True,
                "query": query,
                "report": final_report,
                "sources": sources_found,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"❌ Multi-agent research failed: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "report": ""
            }