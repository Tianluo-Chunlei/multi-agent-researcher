"""
Citations Tool - 作为Lead Agent的工具
复用现有的CitationAgent架构
"""

import json
from typing import Dict, Any, List
from langsmith import traceable

from src.tools.base import BaseTool
# 延迟导入避免循环依赖
# from src.agents.citation_agent import CitationAgent
from src.prompts.prompt_manager import PromptManager
from src.utils.logger import logger


class CitationsTool(BaseTool):
    """引用添加工具"""
    
    def __init__(self):
        super().__init__(
            name="add_citations",
            description="Add proper citations to a research report text. Input should be JSON with 'text' (the synthesized text) and 'sources' (list of source objects) fields. Returns the text with appropriate citations added."
        )
    
    @traceable(name="add_citations_tool")
    async def execute(self, input_data: str, **kwargs) -> str:
        """为研究报告添加引用
        
        Args:
            input_data: JSON格式的输入数据，包含text和sources字段
            
        Returns:
            添加引用后的文本
        """
        try:
            # 解析输入数据
            if isinstance(input_data, str):
                try:
                    data = json.loads(input_data)
                except json.JSONDecodeError:
                    # 如果不是JSON格式，假设整个字符串就是文本
                    return input_data
            else:
                data = input_data
            
            synthesized_text = data.get('text', '')
            sources = data.get('sources', [])
            
            if not synthesized_text:
                logger.warning("No text provided for citations")
                return ""
            
            logger.info(f"Adding citations to text with {len(sources)} sources")
            
            # 延迟导入避免循环依赖
            from src.agents.citation_agent import CitationAgent
            
            # 创建CitationAgent
            citation_agent = CitationAgent()
            
            # 设置系统prompt
            system_prompt = PromptManager.get_citations_agent_system_prompt()
            
            # 格式化源信息
            formatted_sources = self._format_sources(sources)
            
            # 构建输入
            citation_input = f"""<synthesized_text>
{synthesized_text}
</synthesized_text>

<sources>
{formatted_sources}
</sources>"""
            
            # 执行引用添加
            result = await citation_agent.execute_task(citation_input)
            cited_text = result.get('result', synthesized_text)
            
            # 提取带引用的文本
            cited_text = self._extract_cited_text(cited_text)
            
            logger.info("Citations added successfully")
            return cited_text
            
        except Exception as e:
            logger.error(f"Citations addition failed: {e}")
            # 如果失败，返回原文
            if isinstance(input_data, str):
                try:
                    data = json.loads(input_data)
                    return data.get('text', input_data)
                except json.JSONDecodeError:
                    return input_data
            return str(input_data)
    
    def _format_sources(self, sources: List[Dict[str, Any]]) -> str:
        """格式化源信息"""
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
        import re
        
        # 查找<exact_text_with_citation>标签
        pattern = r'<exact_text_with_citation>(.*?)</exact_text_with_citation>'
        match = re.search(pattern, response_content, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        else:
            # 如果没找到标签，返回主要内容
            lines = response_content.strip().split('\n')
            # 过滤掉明显是元信息的行
            content_lines = []
            for line in lines:
                if not (line.startswith('I ') or line.startswith('Based on') or 
                       line.startswith('The text') or line.startswith('Here is')):
                    content_lines.append(line)
            
            return '\n'.join(content_lines) if content_lines else response_content