# 参考设计完整分析：真正的多智能体研究系统

基于 `patterns/agents/prompts/` 中的设计文档，以下是对真正多智能体系统的深度分析。

## 1. 整体架构设计

### 1.1 三层智能体架构

```
用户查询
    ↓
Lead Research Agent (战略指挥层)
    ↓ run_blocking_subagent
Research Subagents (执行层) - 并行自主工作
    ↓ complete_task  
Citations Agent (后处理层)
    ↓
最终报告
```

### 1.2 核心设计原理

#### **智能体自治性 (Agent Autonomy)**
- **Lead Agent**: 战略决策者，不执行具体研究
- **Subagents**: 完全自主的研究专家，各自独立工作
- **Citations Agent**: 专门的后处理智能体

#### **任务驱动的动态架构 (Task-Driven Dynamic Architecture)**
- 根据查询复杂度动态确定子智能体数量 (1-20个)
- 基于查询类型选择不同的执行策略
- 实时调整研究策略和资源分配

## 2. Lead Research Agent 深度分析

### 2.1 核心职责和能力

#### **A. 查询分析和战略规划**
```
1. Assessment and breakdown (深度分析)
   - 识别主要概念和关键实体
   - 列出所需的具体事实和数据点  
   - 分析时间和上下文约束
   - 确定用户期望和最终结果形式

2. Query type determination (查询分类)
   - Depth-first: 多角度深入分析单一主题
   - Breadth-first: 独立子问题并行研究
   - Straightforward: 单一聚焦调查

3. Detailed research plan development (详细计划制定)
   - 基于查询类型制定具体研究计划
   - 明确任务分配和子智能体职责
   - 定义任务边界，避免重叠
```

#### **B. 动态执行和策略调整 (关键发现!)**

这是我之前分析中遗漏的重要特征：

```python
# 执行过程中的动态调整机制
* Throughout execution:
- Continuously monitor progress toward answering the user's query
- Update the search plan and your subagent delegation strategy based on findings from tasks
- Adapt to new information well - analyze the results, use Bayesian reasoning to update your priors
- Adjust research depth based on time constraints and efficiency
```

**核心特征：**
1. **持续监控**: 实时跟踪研究进度
2. **计划更新**: 根据子智能体结果动态调整研究计划
3. **贝叶斯推理**: 基于新信息更新先验知识
4. **效率优化**: 根据时间约束动态调整研究深度

#### **C. 智能委托策略**

```python
# 任务分配原则
For depth-first queries: 
- 部署子智能体探索不同方法论或视角
- 从最可能产生全面结果的方法开始
- 使用替代观点填补空白或提供对比分析

For breadth-first queries:
- 按主题重要性和研究复杂度排序子智能体
- 从建立关键事实或框架信息的子智能体开始
- 后续子智能体探索更具体或依赖性的子主题

For straightforward queries:
- 部署单一综合子智能体
- 将子智能体视为平等合作者
- 子智能体处理约一半工作
```

### 2.2 工具使用模式

#### **A. 核心工具**
- `run_blocking_subagent`: 创建并执行子智能体任务
- `complete_task`: 提交最终研究报告
- 标准工具：web_search, web_fetch（用于非委托任务）

#### **B. 并行执行策略**
```python
# 强制并行工具调用
You MUST use parallel tool calls for creating multiple subagents 
(typically running 3 subagents at the same time) at the start of the research

# 高效执行模式  
For all other queries, do any necessary quick initial planning or investigation yourself, 
then run multiple subagents in parallel
```

#### **C. 内部工具智能使用**
```python
# 工具发现和使用
For instance, if they are available, use:
- slack_search once to find some info relevant to the query
- asana_user_info to read the user's profile  
- asana_search_tasks to find their tasks

# 委托给专门子智能体
create an Asana subagent, a Slack subagent, a Google Drive subagent, 
and a Web Search subagent
```

## 3. Research Subagent 深度分析

### 3.1 自主研究能力

#### **A. OODA循环实现**
```python
# 完整的观察-调整-决策-行动循环
Execute an excellent OODA loop:
(a) observing what information has been gathered so far, what still needs to be gathered
(b) orienting toward what tools and queries would be best to gather needed information  
(c) making an informed, well-reasoned decision to use a specific tool in a certain way
(d) acting to use this tool

# 关键特征
- Execute a MINIMUM of five distinct tool calls, up to ten for complex queries
- Reason carefully after receiving tool results
- Make inferences based on each tool result and determine which tools to use next
- NEVER repeatedly use the exact same queries for the same tools
```

#### **B. 智能工具选择**
```python
# 基于任务的工具选择逻辑
Use the right tools when a task implies they would be helpful:
- google_drive_search (internal docs)
- gmail tools (emails)  
- gcal tools (schedules)
- repl (difficult calculations)
- web_search (getting snippets of web results)
- web_fetch (retrieving full webpages)

# 内部工具优先级
ALWAYS use internal tools for tasks that might require the user's personal data, 
work, or internal context. Internal tools strictly take priority.
```

#### **C. 研究质量控制**
```python
# 源质量评估
Pay attention to the indicators of potentially problematic sources:
- news aggregators rather than original sources
- false authority, pairing of passive voice with nameless sources
- general qualifiers without specifics, unconfirmed reports
- marketing language, spin language, speculation
- misleading and cherry-picked data

# 停止条件
As soon as you have the necessary information, complete the task 
rather than wasting time by continuing research unnecessarily
```

### 3.2 预算和效率管理

#### **A. 研究预算系统**
```python
# 工具调用预算分配
Determine a 'research budget' - roughly how many tool calls to conduct:
- Simpler tasks: under 5 tool calls
- Medium tasks: 5 tool calls  
- Hard tasks: about 10 tool calls
- Very difficult tasks: up to 15 tool calls

# 硬限制
Maximum upper limit: 20 tool calls and under about 100 sources
If you exceed this limit, the subagent will be terminated
```

#### **B. 并行执行优化**
```python
# 并行工具调用
For maximum efficiency, whenever you need to perform multiple independent operations, 
invoke 2 relevant tools simultaneously rather than sequentially
```

## 4. Citations Agent 分析

### 4.1 专门职责
```python
# 单一职责
Add citations to the input text using the format specified earlier
Output the resulting report, unchanged except for the added citations

# 核心原则
- Do NOT modify the <synthesized_text> in any way - keep all content 100% identical
- ONLY add citations where the source documents directly support claims
- Pay careful attention to whitespace: DO NOT add or remove any whitespace
```

### 4.2 引用策略
```python
# 智能引用原则
- Avoid citing unnecessarily: Focus on key facts, conclusions, and substantive claims
- Cite meaningful semantic units: Complete thoughts, findings, or claims
- Minimize sentence fragmentation: Avoid multiple citations within single sentence
- No redundant citations close to each other: Single citation per source per sentence
```

## 5. 关键设计特征总结

### 5.1 动态适应性架构

#### **A. 实时策略调整**
```python
# 关键能力
- Continuously monitor progress toward answering the user's query
- Update the search plan and subagent delegation strategy based on findings
- Use Bayesian reasoning to update your priors  
- Adjust research depth based on time constraints and efficiency
```

#### **B. 智能资源管理**
```python
# 效率优化机制
- When you have reached the point where further research has diminishing returns, 
  STOP FURTHER RESEARCH and do not create any new subagents
- Adjust research depth based on time constraints and efficiency
- Prefer fewer, more capable subagents over many overly narrow ones
```

### 5.2 真正的多智能体协作

#### **A. 清晰的职责分工**
- **Lead Agent**: 战略规划、协调、综合，不做具体研究
- **Subagents**: 独立自主研究，完全负责分配的任务域
- **Citations Agent**: 专门后处理，只负责添加引用

#### **B. 异步并行执行**
```python
# 并行策略
You MUST use parallel tool calls for creating multiple subagents 
(typically running 3 subagents at the same time)

# 独立工作
Each subagent is a fully capable researcher that can search the web 
and use the other search tools available
```

### 5.3 智能决策系统

#### **A. 查询类型智能识别**
```python
# 三种查询类型的精确定义
- Depth-first: Multiple perspectives on the same issue, "going deep"
- Breadth-first: Distinct, independent sub-questions, "going wide"  
- Straightforward: Focused, well-defined, single focused investigation
```

#### **B. 动态子智能体数量**
```python
# 智能规模调整
Simple/Straightforward: 1 subagent
Standard complexity: 2-3 subagents  
Medium complexity: 3-5 subagents
High complexity: 5-10 subagents (maximum 20)
```

## 6. 与当前实现的根本性差异

### 6.1 架构模式
- **参考设计**: 智能体主导的动态协作系统
- **当前实现**: LangGraph节点驱动的固定工作流

### 6.2 执行模式  
- **参考设计**: 真正的异步并行，实时策略调整
- **当前实现**: 批量并行处理，固定执行流程

### 6.3 智能体能力
- **参考设计**: 完全自主的OODA循环，智能停止条件
- **当前实现**: 预定义流程执行，简单阈值停止

### 6.4 工具使用
- **参考设计**: 基于任务的智能工具选择和组合
- **当前实现**: 统一工具集，固定分配模式

---

**结论**: 参考设计是一个真正的动态、自适应、智能协作的多智能体系统，核心特征是智能体的完全自主性、实时策略调整能力、和基于任务的动态资源分配。当前实现虽然功能完整，但本质上是一个固定的工作流系统，缺乏真正多智能体系统的动态适应性和智能协作能力。