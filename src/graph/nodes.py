"""Node functions for the research graph."""

import asyncio
from typing import Dict, Any, List
from datetime import datetime
from langsmith import traceable

from src.graph.state import ResearchState
from src.agents.lead_agent import LeadResearchAgent
from src.agents.subagent import ResearchSubagent
from src.agents.citation_agent import CitationAgent
from src.managers.subagent_manager import SubagentManager
from src.utils.logger import logger


@traceable(name="analyze_query_node")
async def analyze_query(state: ResearchState) -> ResearchState:
    """Analyze the user's query to determine type and complexity.
    
    Args:
        state: Current research state
        
    Returns:
        Updated state with query analysis
    """
    logger.info(f"Analyzing query: {state['query'][:100]}...")
    
    # Create lead agent
    lead_agent = LeadResearchAgent()
    
    # Analyze query
    analysis = await lead_agent.analyze_query(state['query'])
    
    # Update state
    state['query_type'] = analysis['query_type']
    state['query_complexity'] = analysis['complexity']
    state['updated_at'] = datetime.now().isoformat()
    
    logger.info(f"Query type: {state['query_type']}, Complexity: {state['query_complexity']}")
    
    return state


@traceable(name="create_plan_node")
async def create_plan(state: ResearchState) -> ResearchState:
    """Create a research plan based on query analysis.
    
    Args:
        state: Current research state
        
    Returns:
        Updated state with research plan
    """
    logger.info("Creating research plan...")
    
    # Create lead agent
    lead_agent = LeadResearchAgent()
    
    # Create research plan
    plan = await lead_agent.create_research_plan(
        query=state['query'],
        query_type=state['query_type'],
        complexity=state['query_complexity']
    )
    
    # Update state
    state['research_plan'] = plan
    state['subagent_count'] = plan['subagent_count']
    state['subagent_tasks'] = plan['tasks']
    state['updated_at'] = datetime.now().isoformat()
    
    logger.info(f"Created plan with {state['subagent_count']} subagents")
    
    return state


@traceable(name="dispatch_subagents_node")
async def dispatch_subagents(state: ResearchState) -> ResearchState:
    """Dispatch subagents to execute research tasks.
    
    Args:
        state: Current research state
        
    Returns:
        Updated state with active subagents
    """
    logger.info(f"Dispatching {len(state['subagent_tasks'])} subagents...")
    
    # Create subagent manager
    manager = SubagentManager()
    
    # Dispatch subagents
    active_agents = await manager.dispatch_agents(state['subagent_tasks'])
    
    # Update state - store agent IDs and tasks for reconstruction
    state['active_subagents'] = active_agents
    # Store a copy of current tasks for execution phase (important: make a copy to avoid reference issues)
    state['subagent_tasks_for_execution'] = [task.copy() for task in state['subagent_tasks']]
    logger.info(f"Stored {len(state['subagent_tasks_for_execution'])} tasks for execution")
    state['updated_at'] = datetime.now().isoformat()
    
    logger.info(f"Dispatched {len(active_agents)} subagents")
    
    return state


@traceable(name="execute_research_node")
async def execute_research(state: ResearchState) -> ResearchState:
    """Execute research tasks with subagents.
    
    Args:
        state: Current research state
        
    Returns:
        Updated state with research results
    """
    logger.info(f"Executing research with {len(state['active_subagents'])} subagents...")
    
    # Create subagent manager and recreate agents
    manager = SubagentManager()
    
    # Recreate agents from stored tasks
    tasks_for_execution = state.get('subagent_tasks_for_execution', [])
    logger.info(f"Found {len(tasks_for_execution)} stored tasks for {len(state['active_subagents'])} agents")
    if len(tasks_for_execution) >= len(state['active_subagents']):
        # Map agent IDs to their original tasks and recreate agents
        for i, agent_id in enumerate(state['active_subagents']):
            if i < len(tasks_for_execution):
                task = tasks_for_execution[i]
                # Recreate the subagent
                subagent = ResearchSubagent(
                    agent_id=agent_id,
                    task_description=task.get('description', ''),
                    tools=task.get('tools', [])
                )
                manager.active_agents[agent_id] = subagent
                logger.debug(f"Recreated subagent {agent_id} for execution")
    else:
        logger.warning(f"Task count mismatch: {len(tasks_for_execution)} tasks vs {len(state['active_subagents'])} agents")
    
    # Execute research in parallel
    results = await manager.execute_parallel(state['active_subagents'])
    
    # Process results
    for agent_id, result in results.items():
        if result.get('success', False):
            state['completed_subagents'].append(agent_id)
            state['subagent_results'].append(result)
            state['raw_results'].extend(result.get('findings', []))
        else:
            state['failed_subagents'].append(agent_id)
            state['error_count'] += 1
    
    # Clear active subagents and tasks
    state['active_subagents'] = []
    if 'subagent_tasks_for_execution' in state:
        del state['subagent_tasks_for_execution']
    state['iteration'] += 1
    state['updated_at'] = datetime.now().isoformat()
    
    logger.info(f"Research execution complete. Completed: {len(state['completed_subagents'])}, Failed: {len(state['failed_subagents'])}")
    
    return state


@traceable(name="evaluate_results_node")
async def evaluate_results(state: ResearchState) -> ResearchState:
    """Evaluate if research results are sufficient.
    
    Args:
        state: Current research state
        
    Returns:
        Updated state with evaluation
    """
    logger.info("Evaluating research results...")
    
    # Create lead agent
    lead_agent = LeadResearchAgent()
    
    # Evaluate completeness
    evaluation = await lead_agent.evaluate_completeness(
        query=state['query'],
        results=state['raw_results'],
        iteration=state['iteration']
    )
    
    # Update state
    state['needs_more_research'] = evaluation['needs_more'] and state['iteration'] < state['max_iterations']
    
    if state['needs_more_research']:
        # Create additional tasks for missing information
        additional_tasks = evaluation.get('additional_tasks', [])
        state['subagent_tasks'] = additional_tasks
        logger.info(f"Need more research. Adding {len(additional_tasks)} tasks")
    else:
        state['should_continue'] = False
        logger.info("Research is complete")
    
    state['updated_at'] = datetime.now().isoformat()
    
    return state


@traceable(name="synthesize_results_node")
async def synthesize_results(state: ResearchState) -> ResearchState:
    """Synthesize research results into a coherent report.
    
    Args:
        state: Current research state
        
    Returns:
        Updated state with synthesized text
    """
    logger.info("Synthesizing research results...")
    
    # Create lead agent
    lead_agent = LeadResearchAgent()
    
    # Synthesize results
    synthesis = await lead_agent.synthesize_results(
        query=state['query'],
        results=state['raw_results'],
        plan=state['research_plan']
    )
    
    # Update state
    state['synthesized_text'] = synthesis['report']
    state['sources'] = synthesis['sources']
    state['updated_at'] = datetime.now().isoformat()
    
    logger.info(f"Synthesized report: {len(state['synthesized_text'])} characters")
    
    return state


@traceable(name="add_citations_node")
async def add_citations(state: ResearchState) -> ResearchState:
    """Add citations to the synthesized report.
    
    Args:
        state: Current research state
        
    Returns:
        Updated state with cited text
    """
    logger.info("Adding citations to report...")
    
    # Create citation agent
    citation_agent = CitationAgent()
    
    # Add citations
    cited_report = await citation_agent.add_citations(
        text=state['synthesized_text'],
        sources=state['sources']
    )
    
    # Update state
    state['cited_text'] = cited_report
    state['updated_at'] = datetime.now().isoformat()
    
    logger.info("Citations added successfully")
    
    return state


@traceable(name="complete_research_node")
async def complete_research(state: ResearchState) -> ResearchState:
    """Complete the research process and prepare final output.
    
    Args:
        state: Current research state
        
    Returns:
        Final state
    """
    logger.info("Completing research...")
    
    # Calculate final metrics
    end_time = datetime.now()
    start_time = datetime.fromisoformat(state['created_at'])
    state['execution_time'] = (end_time - start_time).total_seconds()
    
    # Log summary
    logger.info(f"""
Research Complete:
- Query ID: {state['query_id']}
- Total tokens: {state['total_tokens_used']}
- Execution time: {state['execution_time']:.2f}s
- Subagents used: {len(state['completed_subagents'])}
- Sources found: {len(state['sources'])}
""")
    
    state['should_continue'] = False
    state['updated_at'] = datetime.now().isoformat()
    
    return state


# Conditional edge functions

def should_continue_research(state: ResearchState) -> str:
    """Determine if more research is needed.
    
    Args:
        state: Current research state
        
    Returns:
        Next node name
    """
    if state['needs_more_research'] and state['iteration'] < state['max_iterations']:
        return "dispatch"
    else:
        return "synthesize"


def check_error_state(state: ResearchState) -> str:
    """Check if there's an error that needs handling.
    
    Args:
        state: Current research state
        
    Returns:
        Next node name
    """
    if state['error_state'] and state['retry_count'] < 3:
        return "error_handler"
    elif state['error_state']:
        return "fail"
    else:
        return "continue"