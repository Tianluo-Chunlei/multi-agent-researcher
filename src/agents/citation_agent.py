"""Citation Agent implementation."""

import re
from typing import Dict, List, Any, Tuple
import json

from src.agents.base import BaseAgent
from src.utils.logger import logger
from src.utils.config import config


class CitationAgent(BaseAgent):
    """Agent that adds citations to research reports."""
    
    def __init__(self):
        """Initialize citation agent."""
        # Use Sonnet model for citations
        super().__init__(model=config.citation_agent_model)
        
    async def add_citations(
        self,
        text: str,
        sources: List[Dict[str, str]]
    ) -> str:
        """Add citations to a research report.
        
        Args:
            text: The synthesized text to add citations to
            sources: List of sources with title and url
            
        Returns:
            Text with citations added
        """
        logger.info(f"Adding citations to text ({len(text)} chars, {len(sources)} sources)")
        
        if not sources:
            logger.warning("No sources provided for citations")
            return text
        
        # Prepare sources for citation
        formatted_sources = self._format_sources(sources)
        
        prompt = f"""Add citations to this research report.

<synthesized_text>
{text}
</synthesized_text>

<sources>
{formatted_sources}
</sources>

Rules:
- Add citations in the format [1], [2], etc.
- Place citations at the end of sentences or claims that use information from that source
- Only cite where the source directly supports the claim
- Avoid over-citation - not every sentence needs a citation
- Focus on key facts, data, and specific claims
- Do NOT modify the text content, only add citation markers

Return ONLY the text with citations added. Do not include any preamble or explanation."""

        response = await self._call_llm(prompt, temperature=0.2, max_tokens=len(text) + 500)
        
        # Clean up response
        cited_text = self._clean_cited_text(response)
        
        # Append reference list
        cited_text = self._append_references(cited_text, sources)
        
        logger.info("Citations added successfully")
        
        return cited_text
    
    def _format_sources(self, sources: List[Dict[str, str]]) -> str:
        """Format sources for the prompt."""
        formatted = []
        for i, source in enumerate(sources, 1):
            title = source.get("title", "Untitled")
            url = source.get("url", "")
            formatted.append(f"[{i}] {title}\n    URL: {url}")
        
        return "\n\n".join(formatted)
    
    def _clean_cited_text(self, text: str) -> str:
        """Clean up the cited text."""
        # Remove any XML tags that might have been included
        text = re.sub(r'</?exact_text_with_citation>', '', text)
        text = re.sub(r'</?synthesized_text>', '', text)
        
        # Remove any preamble
        if "Here is the text with citations" in text:
            parts = text.split('\n', 2)
            if len(parts) > 2:
                text = parts[2]
        
        return text.strip()
    
    def _append_references(self, text: str, sources: List[Dict[str, str]]) -> str:
        """Append reference list to the text."""
        if not sources:
            return text
        
        references = ["\n\n## References\n"]
        for i, source in enumerate(sources, 1):
            title = source.get("title", "Untitled")
            url = source.get("url", "")
            if url:
                references.append(f"[{i}] {title}. Available at: {url}")
            else:
                references.append(f"[{i}] {title}")
        
        return text + "\n".join(references)
    
    async def verify_citations(
        self,
        cited_text: str,
        sources: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Verify that citations are properly placed.
        
        Args:
            cited_text: Text with citations
            sources: List of sources
            
        Returns:
            Verification results
        """
        # Count citations
        citation_pattern = r'\[(\d+)\]'
        citations = re.findall(citation_pattern, cited_text)
        
        # Check citation coverage
        unique_citations = set(citations)
        total_sources = len(sources)
        
        verification = {
            "total_citations": len(citations),
            "unique_citations": len(unique_citations),
            "total_sources": total_sources,
            "uncited_sources": [],
            "citation_density": len(citations) / max(len(cited_text.split()), 1)
        }
        
        # Find uncited sources
        cited_indices = {int(c) for c in unique_citations}
        for i in range(1, total_sources + 1):
            if i not in cited_indices:
                verification["uncited_sources"].append(i)
        
        logger.info(f"Citation verification: {verification['total_citations']} citations, "
                   f"{verification['unique_citations']} unique, "
                   f"{len(verification['uncited_sources'])} uncited sources")
        
        return verification
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Execute a task (required by base class).
        
        Args:
            task: Task description (should include text and sources)
            
        Returns:
            Citation results
        """
        # Parse task to extract text and sources
        try:
            task_data = json.loads(task)
            text = task_data.get("text", "")
            sources = task_data.get("sources", [])
        except:
            # If not JSON, treat as plain text
            text = task
            sources = []
        
        cited_text = await self.add_citations(text, sources)
        verification = await self.verify_citations(cited_text, sources)
        
        return {
            "cited_text": cited_text,
            "verification": verification
        }