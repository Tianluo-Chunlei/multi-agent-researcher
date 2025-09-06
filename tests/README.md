# 测试目录结构

本目录包含Deep Research多代理系统的所有测试。

## 目录结构

```
tests/
├── unit/           # 单元测试 - 测试单个组件
├── integration/    # 集成测试 - 测试组件间交互
├── e2e/           # 端到端测试 - 测试完整工作流
├── debug/         # 调试测试 - 用于故障排除
└── run_tests.py   # 测试运行器
```

## 测试类型说明

### 单元测试 (unit/)
- 测试单个类和函数
- 使用模拟对象，不依赖外部服务
- 快速执行

### 集成测试 (integration/)
- 测试多个组件的交互
- 可能涉及数据库、API调用等
- 中等执行时间

### 端到端测试 (e2e/)
- 测试完整的用户场景
- 使用真实的外部服务（搜索引擎等）
- 较长执行时间

### 调试测试 (debug/)
- 用于故障排除和问题诊断
- 包含详细日志输出
- 手动运行以调试特定问题

## 运行测试

### 运行所有测试
```bash
python tests/run_tests.py
```

### 运行系统测试
```bash
python tests/run_system_tests.py
```

### 运行特定测试
```bash
# 端到端测试
python tests/e2e/test_complete_system.py

# 调试测试
python tests/debug/test_subagent_fix.py
```

### 使用pytest运行
```bash
# 运行所有测试
pytest tests/

# 运行特定目录
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# 运行特定测试文件
pytest tests/e2e/test_complete_system.py -v
```

## 测试要求

- 所有测试都应该有清晰的文档说明
- 使用合适的断言来验证行为
- 包含错误情况的测试
- 端到端测试需要真实的网络连接