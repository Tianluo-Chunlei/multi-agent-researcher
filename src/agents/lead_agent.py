"""Lead Research Agent implementation."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re
from xml.etree import ElementTree as ET

from src.agents.base import BaseAgent
from src.managers.tool_manager import ToolManager
from src.utils.logger import logger
from src.utils.config import config
from src.prompts.prompt_manager import PromptManager


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

Respond in XML format:
<analysis>
    <query_type>...</query_type>
    <complexity>...</complexity>
    <reasoning>...</reasoning>
</analysis>"""

        response = await self._call_llm(prompt, temperature=0.3)
        
        try:
            # Parse XML response
            analysis = self._parse_xml_analysis(response)
            
            # Validate fields
            if "query_type" not in analysis:
                analysis["query_type"] = "straightforward"
            if "complexity" not in analysis:
                analysis["complexity"] = "simple"
                
            logger.info(f"Query analysis: type={analysis['query_type']}, complexity={analysis['complexity']}")
            return analysis
            
        except Exception as e:
            logger.warning(f"Failed to parse analysis XML: {e}, using defaults")
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

Respond in XML format:
<plan>
    <subagent_count>{subagent_count}</subagent_count>
    <tasks>
        <task>
            <description>Specific research task description</description>
            <search_queries>
                <query>query1</query>
                <query>query2</query>
            </search_queries>
            <expected_output>What this task should produce</expected_output>
            <tools>
                <tool>web_search</tool>
                <tool>web_fetch</tool>
            </tools>
        </task>
    </tasks>
    <synthesis_approach>How to combine the results</synthesis_approach>
</plan>"""

        response = await self._call_llm(prompt, temperature=0.5)
        
        try:
            plan = self._parse_xml_plan(response)
            
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
            
        except Exception as e:
            logger.warning(f"Failed to parse plan XML: {e}, creating default plan")
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

Respond in XML format:
<evaluation>
    <is_complete>true/false</is_complete>
    <needs_more>true/false</needs_more>
    <completeness_score>0.0-1.0</completeness_score>
    <missing_aspects>
        <aspect>aspect1</aspect>
        <aspect>aspect2</aspect>
    </missing_aspects>
    <additional_tasks>
        <task>
            <description>Additional research needed</description>
            <search_queries>
                <query>query</query>
            </search_queries>
            <tools>
                <tool>web_search</tool>
            </tools>
        </task>
    </additional_tasks>
</evaluation>"""

        response = await self._call_llm(prompt, temperature=0.3)
        
        try:
            evaluation = self._parse_xml_evaluation(response)
            
            # Default values
            if "needs_more" not in evaluation:
                evaluation["needs_more"] = evaluation.get("completeness_score", 0.5) < 0.8
                
            logger.info(f"Completeness: {evaluation.get('completeness_score', 0)}, Needs more: {evaluation['needs_more']}")
            return evaluation
            
        except Exception as e:
            logger.warning(f"Failed to parse evaluation XML: {e}")
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

Respond in XML format:
<synthesis>
    <report>
        [Your comprehensive markdown report here]
    </report>
    <sources>
        <source>
            <title>Source Title</title>
            <url>Source URL</url>
        </source>
    </sources>
</synthesis>"""

        response = await self._call_llm(prompt, temperature=0.5, max_tokens=8000)
        
        # Extract report and sources
        report, sources = self._parse_xml_synthesis(response)
        
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
    
    def _parse_xml_analysis(self, xml_text: str) -> Dict[str, Any]:
        """Parse XML analysis response."""
        try:
            # Extract XML content
            xml_match = re.search(r'<analysis>(.*?)</analysis>', xml_text, re.DOTALL)
            if xml_match:
                xml_content = f"<analysis>{xml_match.group(1)}</analysis>"
            else:
                xml_content = xml_text
            
            root = ET.fromstring(xml_content)
            
            return {
                "query_type": root.find('query_type').text if root.find('query_type') is not None else "straightforward",
                "complexity": root.find('complexity').text if root.find('complexity') is not None else "simple",
                "reasoning": root.find('reasoning').text if root.find('reasoning') is not None else ""
            }
        except Exception as e:
            logger.warning(f"XML parsing failed: {e}")
            raise
    
    def _parse_xml_plan(self, xml_text: str) -> Dict[str, Any]:
        """Parse XML plan response."""
        try:
            # Extract XML content
            xml_match = re.search(r'<plan>(.*?)</plan>', xml_text, re.DOTALL)
            if xml_match:
                xml_content = f"<plan>{xml_match.group(1)}</plan>"
            else:
                xml_content = xml_text
            
            root = ET.fromstring(xml_content)
            
            # Parse tasks
            tasks = []
            tasks_elem = root.find('tasks')
            if tasks_elem is not None:
                for task_elem in tasks_elem.findall('task'):
                    # Parse search queries
                    queries = []
                    queries_elem = task_elem.find('search_queries')
                    if queries_elem is not None:
                        queries = [q.text for q in queries_elem.findall('query') if q.text]
                    
                    # Parse tools
                    tools = []
                    tools_elem = task_elem.find('tools')
                    if tools_elem is not None:
                        tools = [t.text for t in tools_elem.findall('tool') if t.text]
                    
                    task = {
                        "description": task_elem.find('description').text if task_elem.find('description') is not None else "",
                        "search_queries": queries,
                        "expected_output": task_elem.find('expected_output').text if task_elem.find('expected_output') is not None else "",
                        "tools": tools
                    }
                    tasks.append(task)
            
            return {
                "subagent_count": int(root.find('subagent_count').text) if root.find('subagent_count') is not None else len(tasks),
                "tasks": tasks,
                "synthesis_approach": root.find('synthesis_approach').text if root.find('synthesis_approach') is not None else "Combine all findings"
            }
        except Exception as e:
            logger.warning(f"XML plan parsing failed: {e}")
            raise
    
    def _parse_xml_evaluation(self, xml_text: str) -> Dict[str, Any]:
        """Parse XML evaluation response."""
        try:
            # Extract XML content
            xml_match = re.search(r'<evaluation>(.*?)</evaluation>', xml_text, re.DOTALL)
            if xml_match:
                xml_content = f"<evaluation>{xml_match.group(1)}</evaluation>"
            else:
                xml_content = xml_text
            
            root = ET.fromstring(xml_content)
            
            # Parse missing aspects
            missing_aspects = []
            aspects_elem = root.find('missing_aspects')
            if aspects_elem is not None:
                missing_aspects = [a.text for a in aspects_elem.findall('aspect') if a.text]
            
            # Parse additional tasks
            additional_tasks = []
            tasks_elem = root.find('additional_tasks')
            if tasks_elem is not None:
                for task_elem in tasks_elem.findall('task'):
                    # Parse search queries
                    queries = []
                    queries_elem = task_elem.find('search_queries')
                    if queries_elem is not None:
                        queries = [q.text for q in queries_elem.findall('query') if q.text]
                    
                    # Parse tools
                    tools = []
                    tools_elem = task_elem.find('tools')
                    if tools_elem is not None:
                        tools = [t.text for t in tools_elem.findall('tool') if t.text]
                    
                    task = {
                        "description": task_elem.find('description').text if task_elem.find('description') is not None else "",
                        "search_queries": queries,
                        "tools": tools
                    }
                    additional_tasks.append(task)
            
            # Parse boolean values
            is_complete_text = root.find('is_complete').text if root.find('is_complete') is not None else "false"
            needs_more_text = root.find('needs_more').text if root.find('needs_more') is not None else "true"
            completeness_score_text = root.find('completeness_score').text if root.find('completeness_score') is not None else "0.5"
            
            return {
                "is_complete": is_complete_text.lower() == "true",
                "needs_more": needs_more_text.lower() == "true",
                "completeness_score": float(completeness_score_text),
                "missing_aspects": missing_aspects,
                "additional_tasks": additional_tasks
            }
        except Exception as e:
            logger.warning(f"XML evaluation parsing failed: {e}")
            raise
    
    def _parse_xml_synthesis(self, xml_text: str) -> tuple:
        """Parse XML synthesis response."""
        try:
            # Extract XML content
            xml_match = re.search(r'<synthesis>(.*?)</synthesis>', xml_text, re.DOTALL)
            if xml_match:
                xml_content = f"<synthesis>{xml_match.group(1)}</synthesis>"
            else:
                xml_content = xml_text
            
            root = ET.fromstring(xml_content)
            
            # Extract report
            report_elem = root.find('report')
            report = report_elem.text if report_elem is not None else xml_text
            
            # Extract sources
            sources = []
            sources_elem = root.find('sources')
            if sources_elem is not None:
                for source_elem in sources_elem.findall('source'):
                    source = {
                        "title": source_elem.find('title').text if source_elem.find('title') is not None else "Unknown",
                        "url": source_elem.find('url').text if source_elem.find('url') is not None else "unknown"
                    }
                    sources.append(source)
            
            # If no sources found, create default
            if not sources:
                sources = [{"title": "Research Finding", "url": "research"}]
            
            return report.strip(), sources
            
        except Exception as e:
            logger.warning(f"XML synthesis parsing failed: {e}, using fallback")
            # Fallback to original method
            return self._extract_report_and_sources(xml_text)
    
    async def research_with_tools(self, query: str) -> Dict[str, Any]:
        """
        ReAct模式研究 - Lead Agent自主决策工具使用
        基于research_lead_agent.md的新实现
        """
        logger.info(f"Starting ReAct research for: {query}")
        
        # 获取系统prompt
        tool_names = [tool.name for tool in self.tools if tool]
        system_prompt = PromptManager.get_lead_agent_system_prompt(tools=tool_names)
        
        # 存储研究状态
        all_sources = []
        subagent_results = []
        iteration = 0
        max_iterations = 15
        
        # ReAct循环
        conversation = [
            f"Research Query: {query}\n\nPlease research this query thoroughly. You have access to tools and should use them to gather comprehensive information."
        ]
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"ReAct iteration {iteration}")
            
            # 构建完整prompt
            full_prompt = f"{system_prompt}\n\n" + "\n".join(conversation)
            
            # 获取Agent决策
            response = await self._call_llm(full_prompt, temperature=0.3)
            conversation.append(f"Assistant: {response}")
            
            # 检查是否完成研究
            if "complete_task" in response.lower() or "research completed" in response.lower():
                logger.info("Agent decided research is complete")
                break
            
            # 解析工具调用
            tool_call = self._parse_tool_call(response)
            if tool_call:
                tool_name = tool_call['name']
                tool_input = tool_call['input']
                
                logger.info(f"Using tool: {tool_name} with input: {tool_input[:100]}...")
                
                try:
                    # 执行工具
                    tool_result = await self.tool_manager.execute_tool(tool_name, **{'query': tool_input})
                    
                    # 记录结果
                    if tool_name == "run_blocking_subagent":
                        subagent_results.append(tool_result)
                        if 'sources' in tool_result:
                            all_sources.extend(tool_result['sources'])
                    
                    conversation.append(f"Tool Result ({tool_name}): {str(tool_result)[:1000]}...")
                    
                except Exception as e:
                    error_msg = f"Tool execution failed: {str(e)}"
                    logger.error(error_msg)
                    conversation.append(f"Tool Error: {error_msg}")
            
            # 检查是否应该停止
            if iteration >= max_iterations - 2:
                conversation.append("You are approaching the iteration limit. Please synthesize your findings and complete the research.")
        
        # 提取最终报告
        final_report = self._extract_final_report(conversation)
        
        # 返回结果
        result = {
            'query': query,
            'final_report': final_report,
            'sources': all_sources,
            'subagent_results': subagent_results,
            'iterations': iteration,
            'method': 'react_with_tools'
        }
        
        logger.info(f"ReAct research completed in {iteration} iterations")
        return result
    
    def _parse_tool_call(self, response: str) -> Optional[Dict[str, str]]:
        """解析工具调用"""
        import re
        
        # 查找Action: 和Action Input: 模式
        action_match = re.search(r'Action:\s*([^\n]+)', response)
        input_match = re.search(r'Action Input:\s*([^\n]+)', response)
        
        if action_match:
            tool_name = action_match.group(1).strip()
            tool_input = input_match.group(1).strip() if input_match else ""
            
            return {
                'name': tool_name,
                'input': tool_input
            }
        
        return None
    
    def _extract_final_report(self, conversation: List[str]) -> str:
        """从对话中提取最终报告"""
        # 查找最后几条消息中的报告
        for message in reversed(conversation[-3:]):
            if len(message) > 200 and ("report" in message.lower() or "summary" in message.lower()):
                return message
        
        # 如果没找到专门的报告，返回最后的响应
        return conversation[-1] if conversation else "No final report generated."
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Execute a task (required by base class).
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        # 使用新的ReAct模式研究
        return await self.research_with_tools(task)