#!/usr/bin/env python3

from setuptools import setup, find_packages
import pathlib

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="deep-research",
    version="1.0.0",
    description="Multi-agent research system using LangGraph and Anthropic Claude",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/deep-research",
    author="Deep Research Team",
    author_email="contact@deep-research.ai",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "anthropic>=0.39.0",
        "langgraph>=0.2.0",
        "langchain>=0.3.0",
        "langsmith>=0.1.0",
        "aiohttp>=3.9.0",
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "httpx>=0.25.0",
        "ddgs>=0.1.0",
        "sqlalchemy>=2.0.0",
        "aiosqlite>=0.19.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "pydantic-settings",
        "tiktoken>=0.5.0",
        "tenacity>=8.2.0",
        "loguru>=0.7.0",
        "rich>=13.7.0",
        "click>=8.1.0",
        "IPython",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.12.0",
            "pytest-cov",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.7.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "deep-research=multi_reactagent:main",
            "deep-research-workflow=workflow_agent:main",
        ]
    },
    include_package_data=True,
    zip_safe=False,
)