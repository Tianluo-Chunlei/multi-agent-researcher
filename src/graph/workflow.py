"""Main workflow definition using LangGraph."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langsmith import traceable

from src.graph.state import ResearchState, create_initial_state
from src.graph.nodes import (
    analyze_query,
    create_plan,
    dispatch_subagents,
    execute_research,
    evaluate_results,
    synthesize_results,
    add_citations,
    complete_research,
    should_continue_research
)
from src.utils.logger import logger
from src.utils.tracing import tracing_manager


def create_research_graph():
    """Create the research workflow graph.
    
    Returns:
        Compiled LangGraph workflow
    """
    logger.info("Creating research workflow graph...")
    
    # Create state graph
    workflow = StateGraph(ResearchState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_query)
    workflow.add_node("plan", create_plan)
    workflow.add_node("dispatch", dispatch_subagents)
    workflow.add_node("execute", execute_research)
    workflow.add_node("evaluate", evaluate_results)
    workflow.add_node("synthesize", synthesize_results)
    workflow.add_node("cite", add_citations)
    workflow.add_node("complete", complete_research)
    
    # Add edges
    workflow.add_edge("analyze", "plan")
    workflow.add_edge("plan", "dispatch")
    workflow.add_edge("dispatch", "execute")
    workflow.add_edge("execute", "evaluate")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "evaluate",
        should_continue_research,
        {
            "dispatch": "dispatch",  # Need more research
            "synthesize": "synthesize"  # Research complete
        }
    )
    
    workflow.add_edge("synthesize", "cite")
    workflow.add_edge("cite", "complete")
    workflow.add_edge("complete", END)
    
    # Set entry point
    workflow.set_entry_point("analyze")
    
    # Compile with checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    logger.info("Research workflow graph created successfully")
    
    return app


class ResearchWorkflow:
    """High-level interface for the research workflow."""
    
    def __init__(self):
        """Initialize the research workflow."""
        self.graph = create_research_graph()
        self.active_sessions = {}
        
    @traceable(name="run_research")
    async def run_research(
        self, 
        query: str,
        config: dict = None
    ) -> ResearchState:
        """Run a research query through the workflow.
        
        Args:
            query: The research query
            config: Optional configuration
            
        Returns:
            Final research state with results
        """
        # Create initial state
        initial_state = create_initial_state(query)
        
        # Create config if not provided
        if config is None:
            config = {
                "configurable": {
                    "thread_id": initial_state['query_id'],
                    "checkpoint_ns": "research"
                }
            }
        
        # Store session
        self.active_sessions[initial_state['query_id']] = {
            "query": query,
            "started_at": initial_state['created_at'],
            "config": config
        }
        
        logger.info(f"Starting research for query ID: {initial_state['query_id']}")
        
        try:
            # Run the graph
            final_state = None
            async for event in self.graph.astream(initial_state, config):
                # Log progress
                if isinstance(event, dict):
                    for key, value in event.items():
                        logger.debug(f"Node {key} completed")
                        # Store the last state value
                        if isinstance(value, dict):
                            final_state = value
            
            # Clean up session
            if initial_state['query_id'] in self.active_sessions:
                del self.active_sessions[initial_state['query_id']]
            
            return final_state
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            # Mark session as failed
            if initial_state['query_id'] in self.active_sessions:
                self.active_sessions[initial_state['query_id']]['error'] = str(e)
            raise
    
    async def get_session_status(self, query_id: str) -> dict:
        """Get the status of a research session.
        
        Args:
            query_id: The query ID
            
        Returns:
            Session status
        """
        if query_id in self.active_sessions:
            return self.active_sessions[query_id]
        else:
            return {"status": "not_found"}
    
    async def cancel_research(self, query_id: str) -> bool:
        """Cancel an active research session.
        
        Args:
            query_id: The query ID
            
        Returns:
            True if cancelled successfully
        """
        if query_id in self.active_sessions:
            # In a real implementation, would need to handle actual cancellation
            del self.active_sessions[query_id]
            logger.info(f"Cancelled research session: {query_id}")
            return True
        return False