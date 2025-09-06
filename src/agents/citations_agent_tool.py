"""
Citations Agent Tool
基于citations_agent.md prompt实现的引用添加工具
作为Lead Agent的工具使用
"""

import json
import re
from typing import Dict, Any, List
from langsmith import trace

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import Tool

from ..config import config


class CitationsAgentTool:
    """
    专门的引用添加工具
    基于citations_agent.md实现精确的引用添加
    """
    
    def __init__(self):
        self.config = config.get_citations_agent_config()
        
        # 初始化Anthropic模型
        self.llm = ChatAnthropic(
            model=self.config['model'],
            api_key=self.config['api_key'],
            base_url=self.config['base_url'],
            temperature=self.config['temperature'],  # 0.0 for accuracy
            max_tokens=self.config['max_tokens'],
            timeout=self.config['timeout']
        )
    
    def _load_citations_prompt(self) -> str:
        """加载citations_agent.md prompt"""
        try:
            with open('/Users/chunleicai/Documents/workspace/ai/agent/deep_research/patterns/agents/prompts/citations_agent.md', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return """You are an agent for adding correct citations to a research report. 
Add citations to the input text using the format specified. 
Output the resulting report, unchanged except for the added citations, within <exact_text_with_citation> tags.
Do NOT modify the text content - keep all content 100% identical, only add citations."""
    
    @trace(name="citations_agent_add_citations")
    async def add_citations(self, synthesized_text: str, sources: List[Dict[str, Any]]) -> str:
        """
        为研究报告添加引用
        
        Args:
            synthesized_text: 需要添加引用的文本
            sources: 源列表，每个源包含url, title, content等信息
            
        Returns:
            添加引用后的文本
        """
        try:
            # 构建系统prompt
            system_prompt = self._load_citations_prompt()
            
            # 格式化源信息
            formatted_sources = self._format_sources(sources)
            
            # 构建输入消息
            input_message = f"""<synthesized_text>
{synthesized_text}
</synthesized_text>

<sources>
{formatted_sources}
</sources>

Please add appropriate citations to the synthesized text using the sources provided. Follow the guidelines in your instructions carefully."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=input_message)
            ]
            
            # 获取响应
            response = await self.llm.ainvoke(messages)
            
            # 提取引用后的文本
            cited_text = self._extract_cited_text(response.content)
            
            return cited_text
            
        except Exception as e:
            # 如果引用添加失败，返回原文
            print(f"Citations addition failed: {e}")
            return synthesized_text
    
    def _format_sources(self, sources: List[Dict[str, Any]]) -> str:
        """格式化源信息供Citations Agent使用"""
        formatted_sources = []
        
        for i, source in enumerate(sources, 1):
            source_text = f"Source {i}:\n"
            source_text += f"URL: {source.get('url', 'N/A')}\n"
            source_text += f"Title: {source.get('title', 'N/A')}\n"
            
            # 如果有内容，添加内容摘要
            content = source.get('content', '')
            if content:
                # 限制内容长度
                content_preview = content[:1000] + "..." if len(content) > 1000 else content
                source_text += f"Content: {content_preview}\n"
            
            formatted_sources.append(source_text)
        
        return "\n".join(formatted_sources)
    
    def _extract_cited_text(self, response_content: str) -> str:
        """从响应中提取带引用的文本"""
        # 查找<exact_text_with_citation>标签
        pattern = r'<exact_text_with_citation>(.*?)</exact_text_with_citation>'
        match = re.search(pattern, response_content, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        else:
            # 如果没找到标签，尝试返回主要内容
            lines = response_content.strip().split('\n')
            # 过滤掉明显是元信息的行
            content_lines = []
            for line in lines:
                if not (line.startswith('I ') or line.startswith('Based on') or 
                       line.startswith('The text') or line.startswith('Here is')):
                    content_lines.append(line)
            
            return '\n'.join(content_lines) if content_lines else response_content


def create_citations_agent_tool() -> Tool:
    """创建Citations Agent工具供Lead Agent使用"""
    
    async def add_citations_to_text(input_data: str) -> str:
        """添加引用到文本"""
        try:
            # 解析输入数据 (期望JSON格式)
            data = json.loads(input_data)
            synthesized_text = data.get('text', '')
            sources = data.get('sources', [])
            
            citations_agent = CitationsAgentTool()
            cited_text = await citations_agent.add_citations(synthesized_text, sources)
            
            return cited_text
            
        except json.JSONDecodeError:
            # 如果不是JSON格式，直接返回原文
            return input_data
        except Exception as e:
            return f"Citations addition failed: {str(e)}"
    
    return Tool(
        name="add_citations",
        description="Add proper citations to a research report text. Input should be JSON with 'text' (the synthesized text) and 'sources' (list of source objects) fields. Returns the text with appropriate citations added.",
        func=add_citations_to_text
    )