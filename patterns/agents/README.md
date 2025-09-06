<!--
 * @Author: Chunlei Cai
 * @Date: 2025-09-06 09:38:31
 * @LastEditTime: 2025-09-06 10:01:59
 * @LastEditors: Chunlei Cai
 * @FilePath: /deep_research/patterns/agents/README.md
 * @Description: 
-->
# Building Effective Agents Cookbook

Reference implementation for [Building Effective Agents](https://anthropic.com/research/building-effective-agents) by Erik Schluntz and Barry Zhang.

https://www.anthropic.com/engineering/multi-agent-research-system

This repository contains example minimal implementations of common agent workflows discussed in the blog:

- Basic Building Blocks
  - Prompt Chaining
  - Routing
  - Multi-LLM Parallelization
- Advanced Workflows
  - Orchestrator-Subagents
  - Evaluator-Optimizer

## Getting Started
See the Jupyter notebooks for detailed examples:

- [Basic Workflows](basic_workflows.ipynb)
- [Evaluator-Optimizer Workflow](evaluator_optimizer.ipynb) 
- [Orchestrator-Workers Workflow](orchestrator_workers.ipynb)