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
from langgraph.config import get_stream_writer

from src.utils.config import config
from src.utils.logger import logger
from src.react_agents.prompts import get_lead_agent_prompt, get_subagent_prompt, get_citation_prompt
from src.tools.search import WebSearchTool, WebFetchTool, TavilyWebSearchTool


class ToolManager:
    """Centralized tool manager for creating and managing agent tools."""
    
    def __init__(self):
        """Initialize tool manager with base tools."""
        self._search_tool = None
        self._fetch_tool = None
    
    @property
    def search_tool(self) -> TavilyWebSearchTool:
        """Get or create search tool instance using Tavily API."""
        if self._search_tool is None:
            self._search_tool = TavilyWebSearchTool()
        return self._search_tool
    
    @property
    def fetch_tool(self) -> WebFetchTool:
        """Get or create fetch tool instance."""
        if self._fetch_tool is None:
            self._fetch_tool = WebFetchTool()
        return self._fetch_tool
    
    def create_web_search_tool(self, agent_type: str = "agent") -> callable:
        """Create a web search tool for the specified agent type."""
        @tool
        async def web_search(query: str) -> str:
            """Search the web for information.
            
            Args:
                query: Search query
                
            Returns:
                Search results with titles, URLs, and snippets
            """
            if agent_type == "lead":
                logger.info(f"🔍 Lead agent searching: {query}")
            
            result = await self.search_tool(query=query, max_results=5)
            if result.get("success", False):
                data = result.get("data", {})
                results = data.get("results", [])
                # Format results for agent
                output = []
                for r in results[:5]:
                    output.append(f"Title: {r.get('title', '')}\nURL: {r.get('url', '')}\nSnippet: {r.get('snippet', '')}\n")
                formatted_results = "\n---\n".join(output) if output else "No results found"
                
                if agent_type == "lead":
                    logger.info(f"✅ Search completed: {len(results)} results found")
                
                return formatted_results
            else:
                error_msg = f"Search failed: {result.get('error', 'Unknown error')}"
                if agent_type == "lead":
                    logger.warning(f"⚠️ {error_msg}")
                return error_msg
        
        return web_search
    
    def create_fetch_webpage_tool(self, agent_type: str = "agent") -> callable:
        """Create a fetch webpage tool for the specified agent type."""
        @tool
        async def fetch_webpage(url: str) -> str:
            """Fetch content from a webpage.
            
            Args:
                url: URL to fetch
                
            Returns:
                Webpage content with title and snippet for citation purposes
            """
            if agent_type == "lead":
                logger.info(f"📄 Lead agent fetching: {url[:60]}...")
            
            result = await self.fetch_tool(url=url)
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
                formatted_content = f"Title: {title}\n\nContent:\n{content[:5000]}" if content else "No content found"
                
                if agent_type == "lead":
                    logger.info(f"✅ Fetch completed: {len(content)} chars, title: {title[:50]}...")
                
                return formatted_content
            else:
                error_msg = f"Fetch failed: {result.get('error', 'Unknown error')}"
                if agent_type == "lead":
                    logger.warning(f"⚠️ {error_msg}")
                return error_msg
        
        return fetch_webpage


# Global tool manager instance
tool_manager = ToolManager()


class ResearchSubAgent:
    """Research SubAgent that performs specific research tasks."""
    
    def __init__(self, agent_id: str = "subagent"):
        """Initialize Research SubAgent."""
        self.agent_id = agent_id
        
        # Use Sonnet model for subagent (faster and cheaper)
        self.llm = ChatAnthropic(
            model=config.subagent_model,
            temperature=0.3,
            max_tokens=65536,
            timeout=60*5,  # Increase timeout to 120 seconds to avoid 504 errors
            max_retries=5,  # Add retries for transient errors
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
        
        # Create wrapper tools for LangChain using tool manager
        web_search = tool_manager.create_web_search_tool(agent_type="subagent")
        fetch_webpage = tool_manager.create_fetch_webpage_tool(agent_type="subagent")
        
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
        
        # Ensure response is a string
        if not isinstance(response, str):
            logger.warning(f"Response is not a string: {type(response)}")
            return
        
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
        start_time = datetime.now()
        
        try:
            # Log execution start
            logger.debug(f"SubAgent {self.agent_id} invoking LangGraph agent...")
            
            # Use streaming to get real-time updates
            findings = ""
            sources = []
            tool_calls_count = 0
            messages = []
            last_log_time = datetime.now()
            
            async for chunk in self.agent.astream(
                {"messages": [{"role": "user", "content": task}]},
                {"recursion_limit": 100}  # Increase recursion limit from default 25 to 50
            ):
                # Log progress periodically
                current_time = datetime.now()
                if (current_time - last_log_time).total_seconds() > 10:
                    elapsed = (current_time - start_time).total_seconds()
                    logger.debug(f"  ⏳ SubAgent {self.agent_id} still working... [{elapsed:.1f}s elapsed]")
                    last_log_time = current_time
                
                agent_response = chunk.get("agent", {})
                # Process each chunk
                if "messages" in agent_response:
                    messages.extend(agent_response["messages"])
                    
                    # Log the latest message and extract information
                    for msg in agent_response["messages"]:
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
                            # In streaming, we get multiple AI messages, but we want the final one
                            # For now, we'll update findings with each AI message, but we'll extract
                            # the final result after the stream completes
                            logger.debug(f"SubAgent {self.agent_id} output: {msg.content[:100]}...")
                            
                            # Don't extract source info here during streaming - wait for final result
            
            logger.debug(f"SubAgent {self.agent_id} received {len(messages)} messages")
            
            # Extract the final findings from the last AI message
            if messages:
                for msg in reversed(messages):
                    if msg.type == "ai" and msg.content:
                        # Handle both string and list content
                        if isinstance(msg.content, list):
                            # If content is a list, join it into a string
                            findings = " ".join(str(item) for item in msg.content if item)
                        else:
                            findings = msg.content
                        logger.debug(f"SubAgent {self.agent_id} final findings: {str(findings)[:100]}...")
                        break
            
            # Now extract source information from the final complete response
            if findings:
                self._extract_source_info_from_response(findings, sources)
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ SubAgent {self.agent_id} completed in {elapsed_time:.1f}s: {tool_calls_count} tool calls, {len(sources)} sources")
            
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
            max_tokens=65536,
            timeout=60*10,  # Increase timeout to 120 seconds to avoid 504 errors
            max_retries=5,  # Add retries for transient errors
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
            max_tokens=200000,
            timeout=3600,  # Increase timeout to 120 seconds to avoid 504 errors
            max_retries=5,  # Add retries for transient errors
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
        
        # Initialize search tool for simple queries using tool manager
        web_search = tool_manager.create_web_search_tool(agent_type="lead")
        
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
            
            subagent_start = datetime.now()
            
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
            
            subagent_elapsed = (datetime.now() - subagent_start).total_seconds()
            
            # Log results summary
            successful = sum(1 for r in results if r.get("success"))
            total_sources = sum(len(r.get("sources", [])) for r in results)
            total_tool_calls = sum(r.get("tool_calls", 0) for r in results)
            
            logger.info(f"✅ All {len(tasks)} subagents completed in {subagent_elapsed:.1f}s:")
            logger.info(f"  - Successful: {successful}/{len(tasks)}")
            logger.info(f"  - Total sources collected: {total_sources}")
            logger.info(f"  - Total tool calls made: {total_tool_calls}")
            logger.info(f"  - Average time per subagent: {subagent_elapsed/len(tasks):.1f}s")
            
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
        
        tools.append(web_search)
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
            
            # Use streaming to get real-time updates
            final_report = ""
            sources_found = []
            accumulated_message = None  # Accumulate AIMessageChunks properly
            chunk_count = 0
            last_log_time = datetime.now()

            messages = []
            last_message = None
            last_turn_id = -1
            
            # Use messages mode for real-time token streaming
            async for stream_node, chunk in self.agent.astream(
                {"messages": [{
                    "role": "user",
                    "content": f"""Research this query comprehensively: {query}."""
                }]},
                config={"recursion_limit": 100},
                stream_mode=["values", "updates", "messages"]  # Stream tokens as they are produced
            ):
                
                if stream_node == "messages":
                    chunk_count += 1
                    current_time = datetime.now()
                    
                    # Log progress every 5 seconds
                    if (current_time - last_log_time).total_seconds() > 5:
                        elapsed = (current_time - start_time).total_seconds()
                        logger.info(f"⏳ Lead agent processing... [{elapsed:.1f}s elapsed, {chunk_count} chunks received]")
                        last_log_time = current_time

                if stream_node == "updates":
                    agent_response = chunk.get("agent", {})
                    # Process each chunk
                    if "messages" in agent_response:

                        messages.extend(agent_response["messages"])
                        
                        # Log the latest message and extract information
                        for msg in agent_response["messages"]:
                            # Log tool calls and extract source information
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    tool_name = tool_call.get("name", "unknown")
                                
                                    if tool_name == "web_search":
                                        logger.info(f"  🔍 LeadAgent searching")
                                    elif tool_name == "run_subagents":
                                        logger.info(f" Subagents deployment started")
                                        logger.info("⏱️ NOTE: Subagent execution may take 1-3 minutes...")
                                    elif tool_name == "add_citations":
                                        logger.info(f"  🔖 Citations being added")

                            # Extract AI response and look for source information in the content
                            if msg.type == "ai" and msg.content:
                                logger.info(f"LeadAgent output: {msg.content[:100]}...")
                    pass
                elif stream_node == "values":
                    pass
                elif stream_node == "messages":
                    pass

                continue
                # Process each chunk - stream_mode="messages" sends tuples with (AIMessageChunk, metadata)
                if chunk:
                    # Extract the actual message chunk from the tuple
                    if isinstance(chunk, tuple):
                        msg_chunk = chunk[0]  # First element is the AIMessageChunk
                        metadata = chunk[1] if len(chunk) > 1 else {}
                        if metadata["langgraph_step"] > last_turn_id:
                            last_turn_id = metadata["langgraph_step"]
                            last_message = accumulated_message
                            if last_message:
                                messages.append(last_message)
                            accumulated_message = None
                        pass

                    else:
                        msg_chunk = chunk
                        metadata = {}
                    
                    # Accumulate the message chunks using the + operator
                    if accumulated_message is None:
                        accumulated_message = msg_chunk
                    else:
                        try:
                            accumulated_message = accumulated_message + msg_chunk
                        except Exception as e:
                            logger.debug(f"Could not accumulate chunk: {e}")
                            continue
                    
                    # Process streaming content for real-time display
                    try:
                        if hasattr(msg_chunk, 'content') and msg_chunk.content:
                            # Log token streaming
                            if chunk_count % 10 == 0:  # Log every 10th chunk to avoid spam
                                logger.debug(f"🤖 Streaming tokens... ({chunk_count} chunks)")
                            # TODO: Here you could yield content for real-time UI updates
                    except Exception as e:
                        # Skip content access errors during streaming
                        logger.debug(f"Skipping chunk content access: {e}")
                        pass
                    
                    # Check for tool calls in the accumulated message
                    try:
                        if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
                            for tool_call in last_message.tool_calls:
                                tool_name = tool_call.get("name", "")
                                tool_elapsed = (datetime.now() - start_time).total_seconds()
                                
                                if tool_name == "web_search":
                                    query = tool_call.get("args", {}).get("query", "")
                                    logger.info(f"🔍 Direct web search: {query[:50]}... [at {tool_elapsed:.1f}s]")
                                elif tool_name == "run_subagents":
                                    tasks = tool_call.get("args", {}).get("tasks", [])
                                    logger.info(f"🚀 Subagents deployment started: {len(tasks)} tasks [at {tool_elapsed:.1f}s]")
                                    logger.info("⏱️ NOTE: Subagent execution may take 1-3 minutes...")
                                elif tool_name == "add_citations":
                                    logger.info(f"🔖 Citations being added [at {tool_elapsed:.1f}s]")
                                    # Extract sources from citation tool call
                                    sources = tool_call.get("args", {}).get("sources", [])
                                    sources_found.extend(sources)
                                    logger.info(f"   Added {len(sources)} sources")
                    except Exception as e:
                        # Skip tool call access errors during streaming
                        logger.debug(f"Skipping tool calls access: {e}")
                        pass
            
            logger.info(f"📝 Lead agent completed processing")
            
            # Extract final report from accumulated message
            last_message = messages[-1]
            if last_message and hasattr(last_message, 'content'):
                final_report = last_message.content

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