# Contributing to Deep Research Multi-Agent System

Thank you for your interest in contributing to the Deep Research Multi-Agent System! This document provides guidelines and information to help you get started.

## 🎯 Ways to Contribute

### 🐛 Bug Reports
- Use the issue template to report bugs
- Include Python version, OS, and dependency versions
- Provide minimal reproduction steps
- Share logs and error messages when possible

### ✨ Feature Requests  
- Search existing issues first
- Describe the problem you're solving
- Propose a specific solution or API
- Consider backward compatibility

### 📝 Documentation
- Fix typos and improve clarity
- Add examples and use cases
- Update API documentation
- Create tutorials and guides

### 🔧 Code Contributions
- Bug fixes
- Performance improvements
- New features and agents
- Test coverage improvements

## 🚀 Getting Started

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/deep-research.git
   cd deep-research
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Run tests to verify setup**
   ```bash
   python -m pytest tests/
   ```

### Environment Configuration

Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your API keys for testing
```

## 📋 Development Guidelines

### Code Style

We use automated code formatting and linting:

- **Black** for code formatting (line length: 88)
- **Ruff** for linting and import sorting  
- **MyPy** for type checking

Run before committing:
```bash
# Format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Type checking
mypy src/
```

### Code Standards

1. **Type Hints**: Use type hints for all public functions and methods
2. **Docstrings**: Follow Google-style docstrings
3. **Error Handling**: Use proper exception handling with informative messages
4. **Logging**: Use the project's logger, not `print()` statements
5. **Async/Await**: Prefer async patterns for I/O operations

### Example Function

```python
async def research_topic(
    topic: str,
    max_sources: int = 10,
    timeout: float = 300.0
) -> Dict[str, Any]:
    """Research a specific topic using multiple agents.
    
    Args:
        topic: The research topic to investigate
        max_sources: Maximum number of sources to collect
        timeout: Maximum time to spend on research in seconds
        
    Returns:
        Dictionary containing research results and metadata
        
    Raises:
        ResearchError: When research fails due to configuration issues
        TimeoutError: When research exceeds the specified timeout
    """
    logger.info(f"Starting research on topic: {topic}")
    
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise ResearchError(f"Failed to research topic '{topic}': {e}")
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src tests/

# Run specific test categories
python -m pytest tests/unit/          # Unit tests
python -m pytest tests/integration/   # Integration tests  
python -m pytest tests/e2e/          # End-to-end tests

# Run tests matching a pattern
python -m pytest -k "test_search"
```

### Writing Tests

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **E2E Tests**: Test complete user workflows

#### Test Structure

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from src.agents.lead_agent import LeadResearchAgent

class TestLeadAgent:
    """Test cases for Lead Research Agent."""
    
    @pytest.fixture
    async def agent(self):
        """Create a test agent instance."""
        return LeadResearchAgent()
    
    @pytest.mark.asyncio
    async def test_simple_query(self, agent):
        """Test handling of simple research queries."""
        query = "What is the capital of France?"
        result = await agent.research(query)
        
        assert result["success"] is True
        assert "Paris" in result["report"]
        assert len(result["sources"]) > 0
    
    @pytest.mark.asyncio
    @patch('src.tools.search.WebSearchTool')
    async def test_search_failure_handling(self, mock_search, agent):
        """Test graceful handling of search failures."""
        mock_search.return_value = AsyncMock()
        mock_search.return_value.search.side_effect = Exception("API Error")
        
        result = await agent.research("test query")
        assert result["success"] is False
        assert "error" in result
```

## 🏗️ Project Architecture

### Core Components

- **src/agents/**: Agent implementations (lead, subagent, citation)
- **src/tools/**: Research tools (search, memory, etc.)
- **src/graph/**: LangGraph workflow definitions
- **src/managers/**: Resource managers (tools, subagents)
- **src/utils/**: Utility functions (config, logging, etc.)

### Adding New Features

#### Adding a New Agent

1. Create agent class in `src/agents/`
2. Implement the `BaseAgent` interface
3. Add agent to appropriate workflow
4. Write comprehensive tests
5. Update documentation

#### Adding a New Tool

1. Inherit from `BaseTool` in `src/tools/`
2. Implement required methods
3. Register in `ToolManager`
4. Add integration tests
5. Document usage examples

#### Adding a New Workflow Node

1. Define node function in `src/graph/nodes.py`
2. Update state schema if needed
3. Add node to workflow graph
4. Test node in isolation and integration
5. Update workflow documentation

## 📦 Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)  
- **PATCH**: Bug fixes

### Changelog

Update `CHANGELOG.md` with:
- New features
- Bug fixes
- Breaking changes
- Deprecations

## 🎯 Contribution Workflow

### 1. Create an Issue
- Describe the problem or feature
- Get feedback from maintainers
- Ensure it aligns with project goals

### 2. Fork and Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 3. Implement Changes
- Follow code standards
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes
```bash
# Run full test suite
python -m pytest

# Check code quality
black src/ tests/
ruff check src/ tests/
mypy src/
```

### 5. Commit Changes
```bash
git add .
git commit -m "feat: add new research agent for academic papers"
```

Use conventional commit messages:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code restructuring
- `perf:` Performance improvements

### 6. Submit Pull Request
- Link to related issue
- Describe changes clearly
- Include screenshots/demos if applicable
- Request review from maintainers

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the [Contributor Covenant](https://www.contributor-covenant.org/)

### Communication

- **Issues**: Bug reports and feature requests
- **Discussions**: General questions and ideas  
- **Pull Requests**: Code review and implementation

## ❓ Getting Help

### Resources

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/your-username/deep-research/issues)
- 💬 [Discussions](https://github.com/your-username/deep-research/discussions)

### Common Questions

**Q: How do I add a new search provider?**
A: Implement `BaseSearchTool` interface and register in `ToolManager`. See existing implementations for examples.

**Q: Can I use different AI models?**
A: Yes! Configure via environment variables. The system supports any Anthropic Claude model.

**Q: How do I debug agent behavior?**  
A: Enable debug logging with `DEBUG=true` in `.env` and check `logs/` directory.

## 🙏 Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- Release notes for significant contributions  
- GitHub contributor graphs

Thank you for helping make Deep Research better! 🚀