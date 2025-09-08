<!--
 * @Author: Chunlei Cai
 * @Date: 2025-09-08 15:22:49
 * @LastEditTime: 2025-09-08 15:38:05
 * @LastEditors: Chunlei Cai
 * @FilePath: /deep_research/docs/arch.md
 * @Description: 
-->

# 系统架构对比

## Workflow架构（基于步骤的流水线）

```mermaid
graph TD
    Start[开始] --> Analyze[查询分析Agent]
    Analyze --> Plan[制定研究计划Agent]
    Plan --> CheckComplexity{查询复杂度Agent}
    
    CheckComplexity -->|简单| SingleAgent[创建单个Search智能体
    （web search/fetch tool）]
    CheckComplexity -->|标准| MultiAgent[创建3-5个Search智能体
    web search/fetch tool）]
    CheckComplexity -->|复杂| ManyAgent[创建5-20个Search智能体
    （web search/fetch tool）]
    
    SingleAgent --> Execute[并行执行]
    MultiAgent --> Execute
    ManyAgent --> Execute
    
    Execute --> Collect[收集结果]
    Collect --> Evaluate{评估完整性Agent}
    
    Evaluate -->|需要更多信息| MoreResearch[创建补充子智能体]
    MoreResearch --> Execute
    
    Evaluate -->|信息充足| Synthesize[综合分析Agent]
    Synthesize --> Citations[添加引用生成报告Agent]
    Citations --> End[结束]
```

## React Agent架构（主从智能体）

```mermaid
graph TD
    Start[开始] --> Lead[LeadAgent Claude-Opus<br/>自主决策控制<br/>问题识别、定研究计划、
    子课题拆解、检查结果、
    重新制定计划部署任务、
    综合结果、撰写报告、
    添加引用]
    
    Lead -->|研究子课题列表|Deploy[部署子智能体<br/>run_subagents工具]
    
    Deploy --> |研究子课题1|SubAgent1[SubAgent1 Claude-Sonnet<br/>专项研究<br/>web search/fetch]
    Deploy --> |研究子课题2|SubAgent2[SubAgent2 Claude-Sonnet<br/>专项研究<br/>web search/fetch] 
    Deploy --> |研究子课题N|SubAgentN[SubAgentN Claude-Sonnet<br/>专项研究<br/>web search/fetch]
    
    SubAgent1 -->|子课题研究报告与信息来源| Lead
    SubAgent2 -->|子课题研究报告与信息来源| Lead
    SubAgentN -->|子课题研究报告与信息来源| Lead
    
    Lead --> Report[生成最终报告]
    Report --> End[结束]
```


