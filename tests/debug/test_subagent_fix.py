#!/usr/bin/env python3
"""Test script to verify subagent execution fix."""

import asyncio
from src.graph.workflow import ResearchWorkflow
from src.utils.logger import logger

async def test_simple_query():
    """Test a simple query to verify subagents execute properly."""
    logger.info("Testing subagent execution fix...")
    
    workflow = ResearchWorkflow()
    
    # Test with a simple query
    query = "What is Python programming language?"
    
    try:
        result = await workflow.run_research(query)
        
        # Check if we got results
        if result:
            logger.info(f"Final result keys: {list(result.keys())}")
            logger.info(f"Raw results count: {len(result.get('raw_results', []))}")
            logger.info(f"Completed subagents: {len(result.get('completed_subagents', []))}")
            logger.info(f"Failed subagents: {len(result.get('failed_subagents', []))}")
            
            if result.get('raw_results'):
                logger.info("✅ SUCCESS: Research produced results!")
                logger.info(f"Sample result: {str(result['raw_results'][0])[:200]}...")
            else:
                logger.warning("❌ ISSUE: No research results found")
                
        else:
            logger.error("❌ ISSUE: No final result returned")
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_query())