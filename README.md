# Deep Research Multi-Agent System

基于 LangGraph 和 Anthropic Claude 的多智能体深度研究系统。

## 🚀 特性

- **多智能体协作**：主智能体协调多个子智能体并行研究
- **智能查询分析**：自动分类查询类型和复杂度
- **动态任务分配**：根据查询复杂度分配 1-20 个子智能体
- **OODA 循环执行**：子智能体使用观察-定位-决策-行动循环
- **自动引用管理**：智能添加和验证引用
- **LangGraph 工作流**：状态管理、检查点、条件路由

## 📦 安装

### 1. 克隆仓库
```bash
git clone <repository-url>
cd deep_research
```

### 2. 创建虚拟环境
```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
复制 `.env.example` 到 `.env` 并设置你的 API 密钥：
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_BASE_URL=https://api.anthropic.com  # 可选
```

## 🎯 使用方法

### 命令行使用
```bash
# 交互式模式
python src/main.py

# 直接查询
python src/main.py "What are the latest developments in AI?"
```

### Python API 使用
```python
from src.graph.workflow import ResearchWorkflow

async def research():
    workflow = ResearchWorkflow()
    result = await workflow.run_research("Your research query here")
    print(result["cited_text"])
```

## 🏗️ 系统架构

```
查询输入
    ↓
查询分析 (depth-first/breadth-first/straightforward)
    ↓
研究计划制定 (1-20个子智能体)
    ↓
并行执行子智能体
    ↓
结果评估 (是否需要更多研究)
    ↓
结果综合
    ↓
添加引用
    ↓
最终报告
```

### 核心组件

- **LeadResearchAgent**: 主研究智能体，负责分析、规划、综合
- **ResearchSubagent**: 子研究智能体，执行具体研究任务
- **CitationAgent**: 引用智能体，添加和验证引用
- **LangGraph Workflow**: 管理整个研究流程

## 🧪 测试

### 运行单元测试
```bash
python tests/unit/test_basic_components.py
```

### 运行集成测试
```bash
python tests/integration/test_simple_flow.py
```

### 运行端到端测试
```bash
python tests/e2e/test_simple_query.py
```

## 📊 配置选项

主要配置项（在 `.env` 文件中）：

- `LEAD_AGENT_MODEL`: 主智能体模型（默认：claude-3-5-sonnet）
- `SUBAGENT_MODEL`: 子智能体模型（默认：claude-3-5-sonnet）
- `MAX_CONCURRENT_SUBAGENTS`: 最大并发子智能体数（默认：5）
- `MAX_ITERATIONS`: 最大研究迭代次数（默认：5）
- `CONTEXT_WINDOW_TOKENS`: 上下文窗口大小（默认：200000）

## 🔍 查询类型

系统自动识别三种查询类型：

1. **Depth-first（深度优先）**: 需要多个视角研究同一问题
2. **Breadth-first（广度优先）**: 可分解为独立子问题
3. **Straightforward（直接）**: 单一聚焦的问题

## 📈 性能考虑

- Token 使用：多智能体系统使用约 15× 聊天模式的 tokens
- 并发控制：通过 `MAX_CONCURRENT_SUBAGENTS` 控制并发
- 缓存：使用 SQLite 存储研究记忆和计划

## 🛠️ 开发

### 项目结构
```
deep_research/
├── src/
│   ├── agents/          # 智能体实现
│   ├── tools/           # 工具（搜索、记忆等）
│   ├── graph/           # LangGraph 工作流
│   ├── managers/        # 管理器（工具、子智能体）
│   └── utils/           # 工具类
├── tests/               # 测试文件
├── docs/                # 文档
└── data/                # 本地数据库
```

### 添加新工具
1. 继承 `BaseTool` 类
2. 实现 `execute` 方法
3. 在 `ToolManager` 中注册

### 自定义智能体
1. 继承 `BaseAgent` 类
2. 实现 `execute_task` 方法
3. 添加到工作流节点

## 📝 许可证

MIT License

## 🤝 贡献

欢迎贡献！请提交 Pull Request 或创建 Issue。

## 📚 参考资料

- [Building Effective Agents - Anthropic](https://anthropic.com/research/building-effective-agents)
- [LangGraph Documentation](https://github.com/langchain-ai/langgraph)
- [Anthropic API Documentation](https://docs.anthropic.com)

## ⚠️ 注意事项

- 需要有效的 Anthropic API 密钥
- 建议使用 Python 3.11+
- 大型研究任务可能消耗大量 API credits