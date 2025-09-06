"""State definition for the research graph."""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime
import uuid


class ResearchState(TypedDict):
    """State for the research workflow."""
    
    # User input
    query: str
    query_id: str
    
    # Query analysis
    query_type: Literal["depth-first", "breadth-first", "straightforward"]
    query_complexity: Literal["simple", "standard", "medium", "high"]
    
    # Research planning
    research_plan: Dict[str, Any]
    subagent_count: int
    subagent_tasks: List[Dict[str, Any]]
    
    # Execution state
    active_subagents: List[str]
    completed_subagents: List[str]
    failed_subagents: List[str]
    subagent_results: List[Dict[str, Any]]
    
    # Research results
    raw_results: List[Dict[str, Any]]
    synthesized_text: str
    cited_text: str
    sources: List[Dict[str, str]]
    
    # Memory and context
    memory: Dict[str, Any]
    context_tokens: int
    conversation_history: List[Dict[str, str]]
    
    # Control flow
    iteration: int
    max_iterations: int
    should_continue: bool
    needs_more_research: bool
    
    # Error handling
    error_state: Optional[str]
    error_count: int
    retry_count: int
    
    # Metadata
    created_at: str
    updated_at: str
    total_tokens_used: int
    total_cost: float
    execution_time: float


def create_initial_state(query: str) -> ResearchState:
    """Create initial state for a research query.
    
    Args:
        query: The user's research query
        
    Returns:
        Initial research state
    """
    now = datetime.now().isoformat()
    
    return ResearchState(
        # User input
        query=query,
        query_id=str(uuid.uuid4()),
        
        # Query analysis (to be filled)
        query_type="straightforward",
        query_complexity="simple",
        
        # Research planning (to be filled)
        research_plan={},
        subagent_count=1,
        subagent_tasks=[],
        
        # Execution state
        active_subagents=[],
        completed_subagents=[],
        failed_subagents=[],
        subagent_results=[],
        
        # Research results
        raw_results=[],
        synthesized_text="",
        cited_text="",
        sources=[],
        
        # Memory and context
        memory={},
        context_tokens=0,
        conversation_history=[],
        
        # Control flow
        iteration=0,
        max_iterations=5,
        should_continue=True,
        needs_more_research=False,
        
        # Error handling
        error_state=None,
        error_count=0,
        retry_count=0,
        
        # Metadata
        created_at=now,
        updated_at=now,
        total_tokens_used=0,
        total_cost=0.0,
        execution_time=0.0
    )