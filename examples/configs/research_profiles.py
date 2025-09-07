#!/usr/bin/env python3
"""
Example configuration profiles for different research scenarios.

This file demonstrates how to configure the Deep Research system
for various use cases and research types.
"""

from typing import Dict, Any

# Academic Research Profile
ACADEMIC_RESEARCH = {
    "lead_agent_model": "claude-3-5-sonnet-20241022",
    "subagent_model": "claude-3-5-sonnet-20241022", 
    "citation_agent_model": "claude-3-5-sonnet-20241022",
    "max_concurrent_subagents": 8,
    "max_iterations": 7,
    "context_window_tokens": 200000,
    "search_depth": "comprehensive",
    "citation_style": "academic",
    "quality_threshold": 0.85,
    "description": "Optimized for in-depth academic research with comprehensive citations"
}

# Business Intelligence Profile  
BUSINESS_INTELLIGENCE = {
    "lead_agent_model": "claude-3-5-sonnet-20241022",
    "subagent_model": "claude-3-5-sonnet-20241022",
    "citation_agent_model": "claude-3-5-sonnet-20241022", 
    "max_concurrent_subagents": 12,
    "max_iterations": 5,
    "context_window_tokens": 150000,
    "search_depth": "market_focused",
    "citation_style": "business",
    "quality_threshold": 0.80,
    "description": "Fast market research with focus on recent data and trends"
}

# Journalist Research Profile
JOURNALISM = {
    "lead_agent_model": "claude-3-5-sonnet-20241022",
    "subagent_model": "claude-3-5-sonnet-20241022",
    "citation_agent_model": "claude-3-5-sonnet-20241022",
    "max_concurrent_subagents": 6,
    "max_iterations": 4,
    "context_window_tokens": 100000,
    "search_depth": "current_events",
    "citation_style": "news",
    "quality_threshold": 0.75,
    "description": "Balanced speed and accuracy for news and current events research"
}

# Quick Fact-Check Profile
FACT_CHECK = {
    "lead_agent_model": "claude-3-5-sonnet-20241022",
    "subagent_model": "claude-3-5-sonnet-20241022",
    "citation_agent_model": "claude-3-5-sonnet-20241022",
    "max_concurrent_subagents": 3,
    "max_iterations": 2,
    "context_window_tokens": 50000,
    "search_depth": "verification",
    "citation_style": "minimal",
    "quality_threshold": 0.90,
    "description": "Fast verification with high accuracy requirements"
}

# Deep Dive Analysis Profile
DEEP_ANALYSIS = {
    "lead_agent_model": "claude-3-5-sonnet-20241022",
    "subagent_model": "claude-3-5-sonnet-20241022",
    "citation_agent_model": "claude-3-5-sonnet-20241022",
    "max_concurrent_subagents": 15,
    "max_iterations": 10,
    "context_window_tokens": 300000,
    "search_depth": "exhaustive",
    "citation_style": "detailed",
    "quality_threshold": 0.95,
    "description": "Maximum depth and quality for complex research projects"
}

# Budget-Conscious Profile (fewer API calls)
BUDGET_FRIENDLY = {
    "lead_agent_model": "claude-3-5-sonnet-20241022",
    "subagent_model": "claude-3-5-sonnet-20241022", 
    "citation_agent_model": "claude-3-5-sonnet-20241022",
    "max_concurrent_subagents": 2,
    "max_iterations": 3,
    "context_window_tokens": 75000,
    "search_depth": "focused",
    "citation_style": "minimal",
    "quality_threshold": 0.70,
    "description": "Cost-optimized while maintaining reasonable quality"
}

# All available profiles
RESEARCH_PROFILES: Dict[str, Dict[str, Any]] = {
    "academic": ACADEMIC_RESEARCH,
    "business": BUSINESS_INTELLIGENCE, 
    "journalism": JOURNALISM,
    "fact_check": FACT_CHECK,
    "deep_dive": DEEP_ANALYSIS,
    "budget": BUDGET_FRIENDLY
}

def get_profile(profile_name: str) -> Dict[str, Any]:
    """Get a research profile by name.
    
    Args:
        profile_name: Name of the profile to retrieve
        
    Returns:
        Profile configuration dictionary
        
    Raises:
        KeyError: If profile name is not found
    """
    if profile_name not in RESEARCH_PROFILES:
        available = ", ".join(RESEARCH_PROFILES.keys())
        raise KeyError(f"Profile '{profile_name}' not found. Available: {available}")
    
    return RESEARCH_PROFILES[profile_name].copy()

def list_profiles() -> None:
    """Print all available research profiles."""
    print("Available Research Profiles:")
    print("=" * 50)
    
    for name, config in RESEARCH_PROFILES.items():
        print(f"\n{name.upper()}:")
        print(f"  Description: {config['description']}")
        print(f"  Max Agents: {config['max_concurrent_subagents']}")
        print(f"  Iterations: {config['max_iterations']}")
        print(f"  Quality: {config['quality_threshold']}")

def create_custom_profile(
    name: str,
    max_agents: int = 5,
    iterations: int = 5,
    quality: float = 0.80,
    **kwargs
) -> Dict[str, Any]:
    """Create a custom research profile.
    
    Args:
        name: Profile name
        max_agents: Maximum concurrent subagents
        iterations: Maximum research iterations
        quality: Quality threshold (0.0-1.0)
        **kwargs: Additional configuration options
        
    Returns:
        Custom profile configuration
    """
    profile = {
        "lead_agent_model": "claude-3-5-sonnet-20241022",
        "subagent_model": "claude-3-5-sonnet-20241022",
        "citation_agent_model": "claude-3-5-sonnet-20241022",
        "max_concurrent_subagents": max_agents,
        "max_iterations": iterations,
        "context_window_tokens": 150000,
        "search_depth": "balanced",
        "citation_style": "standard", 
        "quality_threshold": quality,
        "description": f"Custom profile: {name}"
    }
    
    # Override with any additional parameters
    profile.update(kwargs)
    
    return profile

if __name__ == "__main__":
    # Demo the profiles
    list_profiles()
    
    print("\n" + "="*50)
    print("EXAMPLE USAGE:")
    print("="*50)
    
    # Example of using a profile
    profile = get_profile("academic")
    print(f"\nAcademic Research Profile:")
    for key, value in profile.items():
        if key != "description":
            print(f"  {key}: {value}")
    
    # Example of creating custom profile
    custom = create_custom_profile(
        "my_research",
        max_agents=7,
        iterations=6,
        quality=0.85,
        search_depth="comprehensive"
    )
    print(f"\nCustom Profile Example:")
    for key, value in custom.items():
        if key != "description":
            print(f"  {key}: {value}")