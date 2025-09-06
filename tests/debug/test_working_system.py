#!/usr/bin/env python3
"""测试修复后的系统是否正常工作"""

import asyncio
from src.graph.workflow import ResearchWorkflow
from src.utils.logger import logger

async def test_working_system():
    """测试系统是否正常工作"""
    logger.info("测试修复后的研究系统...")
    
    workflow = ResearchWorkflow()
    
    # 使用一个简单的查询测试
    query = "What are the main features of Python?"
    
    try:
        result = await workflow.run_research(query)
        
        if result:
            logger.info("✅ 成功：系统产生了最终结果")
            logger.info(f"原始结果数量: {len(result.get('raw_results', []))}")
            logger.info(f"完成的子代理: {len(result.get('completed_subagents', []))}")
            logger.info(f"失败的子代理: {len(result.get('failed_subagents', []))}")
            
            if result.get('raw_results'):
                logger.info("✅ 成功：找到了研究结果")
                logger.info(f"示例结果: {str(result['raw_results'][0])[:150]}...")
            else:
                logger.warning("⚠️  警告：没有原始研究结果")
            
            if result.get('cited_text'):
                logger.info("✅ 成功：生成了最终报告")
                logger.info(f"报告长度: {len(result['cited_text'])} 字符")
                print("\n" + "="*50)
                print("最终研究报告:")
                print("="*50)
                print(result['cited_text'])
                print("="*50)
            else:
                logger.warning("⚠️  警告：没有最终报告")
            
            if result.get('sources'):
                logger.info(f"✅ 成功：包含 {len(result['sources'])} 个信息源")
                for i, source in enumerate(result['sources'][:3], 1):
                    logger.info(f"来源 {i}: {source.get('title', 'Unknown')} - {source.get('url', 'No URL')}")
            else:
                logger.warning("⚠️  警告：没有信息源")
                
        else:
            logger.error("❌ 错误：没有返回最终结果")
            
    except Exception as e:
        logger.error(f"❌ 错误：{e}")

if __name__ == "__main__":
    asyncio.run(test_working_system())