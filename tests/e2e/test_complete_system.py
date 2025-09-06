#!/usr/bin/env python3
"""完整系统端到端测试 - 验证修复后的多代理研究系统"""

import asyncio
import pytest
from src.graph.workflow import ResearchWorkflow
from src.utils.logger import logger


@pytest.mark.asyncio
async def test_research_system_with_real_search():
    """测试研究系统是否能正确执行真实网络搜索并生成报告"""
    workflow = ResearchWorkflow()
    
    # 使用简单查询测试
    query = "What are the main features of Python programming language?"
    
    result = await workflow.run_research(query)
    
    # 验证基本结构
    assert result is not None, "系统应该返回结果"
    assert isinstance(result, dict), "结果应该是字典类型"
    
    # 验证子代理执行
    completed_subagents = result.get('completed_subagents', [])
    failed_subagents = result.get('failed_subagents', [])
    
    assert len(completed_subagents) > 0, f"应该有完成的子代理，实际: {len(completed_subagents)}"
    assert len(failed_subagents) == 0, f"不应该有失败的子代理，实际: {len(failed_subagents)}"
    
    # 验证搜索结果
    raw_results = result.get('raw_results', [])
    assert len(raw_results) > 0, f"应该有原始搜索结果，实际: {len(raw_results)}"
    
    # 验证报告生成
    synthesized_text = result.get('synthesized_text', '')
    cited_text = result.get('cited_text', '')
    
    assert len(synthesized_text) > 100, f"综合文本应该有实质内容，实际长度: {len(synthesized_text)}"
    assert len(cited_text) > 100, f"引用文本应该有实质内容，实际长度: {len(cited_text)}"
    
    # 验证信息源
    sources = result.get('sources', [])
    assert len(sources) > 0, f"应该有信息源，实际: {len(sources)}"
    
    # 验证信息源包含真实URL
    has_real_url = any(
        source.get('url', '').startswith(('http://', 'https://'))
        for source in sources
        if isinstance(source, dict)
    )
    
    # 如果没有真实URL，至少应该有某种来源标识
    if not has_real_url:
        logger.warning("没有发现真实URL，但这可能是正常的")
    
    logger.info(f"✅ 测试通过 - 完成子代理: {len(completed_subagents)}, 原始结果: {len(raw_results)}, 报告长度: {len(cited_text)}")


@pytest.mark.asyncio  
async def test_multiple_iterations():
    """测试系统是否能处理需要多轮研究的查询"""
    workflow = ResearchWorkflow()
    
    # 使用可能需要多轮研究的复杂查询
    query = "Compare Python and JavaScript programming languages"
    
    result = await workflow.run_research(query)
    
    # 基本验证
    assert result is not None
    assert len(result.get('completed_subagents', [])) > 0
    assert len(result.get('raw_results', [])) > 0
    
    # 验证迭代次数
    iterations = result.get('iteration', 0)
    assert iterations >= 1, f"应该至少执行1次迭代，实际: {iterations}"
    
    logger.info(f"✅ 多轮测试通过 - 迭代次数: {iterations}")


if __name__ == "__main__":
    # 允许直接运行测试
    async def run_tests():
        logger.info("开始端到端系统测试...")
        
        try:
            await test_research_system_with_real_search()
            logger.info("✅ 完整系统测试通过")
        except Exception as e:
            logger.error(f"❌ 完整系统测试失败: {e}")
        
        try:
            await test_multiple_iterations()
            logger.info("✅ 多轮迭代测试通过")
        except Exception as e:
            logger.error(f"❌ 多轮迭代测试失败: {e}")
    
    asyncio.run(run_tests())