# Deep Research 智能体系统架构图

## 系统整体架构

```mermaid
graph TB
    subgraph "用户接口层"
        U[用户查询]
    end
    
    subgraph "协调层"
        LRA[Lead Research Agent<br/>主研究智能体]
    end
    
    subgraph "执行层"
        SA1[Research Subagent 1<br/>子研究智能体]
        SA2[Research Subagent 2<br/>子研究智能体]
        SA3[Research Subagent 3<br/>子研究智能体]
        SAN[Research Subagent N<br/>子研究智能体]
    end
    
    subgraph "后处理层"
        CA[Citation Agent<br/>引用智能体]
    end
    
    subgraph "工具层"
        WS[Web Search<br/>网络搜索]
        WF[Web Fetch<br/>网页获取]
        GD[Google Drive<br/>内部文档]
        GM[Gmail<br/>邮件系统]
        GC[Google Calendar<br/>日历系统]
        SL[Slack<br/>内部通信]
    end
    
    U --> LRA
    LRA --> SA1
    LRA --> SA2
    LRA --> SA3
    LRA --> SAN
    
    SA1 --> WS
    SA1 --> WF
    SA1 --> GD
    SA2 --> WS
    SA2 --> WF
    SA2 --> GM
    SA3 --> WS
    SA3 --> WF
    SA3 --> GC
    SAN --> WS
    SAN --> WF
    SAN --> SL
    
    SA1 --> LRA
    SA2 --> LRA
    SA3 --> LRA
    SAN --> LRA
    
    LRA --> CA
    CA --> U
```

## 智能体协作流程图

```mermaid
sequenceDiagram
    participant U as 用户
    participant LRA as Lead Research Agent
    participant SA1 as Subagent 1
    participant SA2 as Subagent 2
    participant SA3 as Subagent 3
    participant CA as Citation Agent
    
    U->>LRA: 提交研究查询
    
    Note over LRA: 查询分析与分类
    LRA->>LRA: 分析查询类型<br/>(Depth-first/Breadth-first/Straightforward)
    
    Note over LRA: 制定研究计划
    LRA->>LRA: 确定子智能体数量<br/>分配具体任务
    
    Note over LRA: 并行部署子智能体
    par 并行执行
        LRA->>SA1: 分配任务1
        LRA->>SA2: 分配任务2
        LRA->>SA3: 分配任务3
    end
    
    Note over SA1,SA3: 并行研究执行
    par 信息收集
        SA1->>SA1: 执行OODA循环<br/>收集相关信息
        SA2->>SA2: 执行OODA循环<br/>收集相关信息
        SA3->>SA3: 执行OODA循环<br/>收集相关信息
    end
    
    Note over SA1,SA3: 结果报告
    SA1->>LRA: 提交研究结果1
    SA2->>LRA: 提交研究结果2
    SA3->>LRA: 提交研究结果3
    
    Note over LRA: 结果综合
    LRA->>LRA: 收集所有结果<br/>进行批判性分析<br/>生成综合报告
    
    LRA->>CA: 传递综合报告
    
    Note over CA: 添加引用
    CA->>CA: 为关键声明添加引用<br/>保持内容完整性
    
    CA->>U: 返回最终报告
```

## 查询类型处理策略图

```mermaid
graph TD
    Q[用户查询] --> A{查询类型分析}
    
    A -->|Depth-first| DF[深度优先查询]
    A -->|Breadth-first| BF[广度优先查询]
    A -->|Straightforward| SF[直接查询]
    
    DF --> DF1[创建3-5个子智能体]
    DF1 --> DF2[不同方法论角度]
    DF2 --> DF3[多角度深入分析]
    DF3 --> DF4[综合多角度见解]
    
    BF --> BF1[识别独立子问题]
    BF1 --> BF2[为每个子问题分配智能体]
    BF2 --> BF3[并行收集信息]
    BF3 --> BF4[整合所有子问题结果]
    
    SF --> SF1[创建1个子智能体]
    SF1 --> SF2[直接高效路径]
    SF2 --> SF3[基本验证]
    SF3 --> SF4[简单综合]
    
    DF4 --> S[结果综合]
    BF4 --> S
    SF4 --> S
    
    S --> C[添加引用]
    C --> R[最终报告]
```

## 工具调用预算图

```mermaid
graph LR
    T[任务复杂度] --> B{预算分配}
    
    B -->|简单任务| S[3-5次工具调用]
    B -->|中等任务| M[5-10次工具调用]
    B -->|复杂任务| C[10-15次工具调用]
    B -->|最大限制| L[20次工具调用<br/>100个来源]
    
    S --> E[高效执行]
    M --> E
    C --> E
    L --> E
    
    E --> R[研究结果]
```

## 质量保证流程图

```mermaid
graph TD
    I[信息收集] --> Q{质量检查}
    
    Q -->|高质量| A[接受信息]
    Q -->|低质量| R[拒绝信息]
    Q -->|冲突信息| C[标记冲突]
    
    A --> V[事实验证]
    C --> V
    
    V -->|验证通过| S[存储结果]
    V -->|验证失败| F[进一步调查]
    
    F --> I
    S --> N[下一阶段]
    
    R --> N
```

## 智能体角色职责矩阵

| 智能体类型 | 主要职责 | 关键能力 | 工具使用 | 输出格式 |
|-----------|---------|---------|---------|---------|
| **Lead Research Agent** | 策略制定、任务分配、结果综合 | 战略思维、并行管理、质量控制 | 子智能体管理工具 | 综合研究报告 |
| **Research Subagent** | 信息收集、初步分析 | 工具精通、信息筛选、效率控制 | 搜索工具、获取工具、内部工具 | 结构化研究结果 |
| **Citation Agent** | 引用添加、格式控制 | 精确性、一致性、完整性 | 引用处理工具 | 带引用的最终报告 |

## 系统特性总结

### 核心优势
- **并行高效**：多个子智能体同时工作，最大化研究效率
- **智能分配**：根据查询复杂度动态调整资源分配
- **质量保证**：多层次质量检查确保信息准确性
- **灵活适应**：支持不同类型查询的处理策略

### 技术特点
- **模块化设计**：各智能体职责清晰，便于维护和扩展
- **状态管理**：使用LangGraph管理复杂的状态流转
- **错误处理**：完善的错误恢复和优雅降级机制
- **成本控制**：智能的工具调用预算管理
