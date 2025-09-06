#!/usr/bin/env python3
"""运行系统测试脚本"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import logger


async def main():
    """运行主要系统测试"""
    logger.info("🚀 开始运行系统测试...")
    
    try:
        # 运行端到端测试
        from tests.e2e.test_complete_system import test_research_system_with_real_search
        
        logger.info("📋 运行完整系统测试...")
        await test_research_system_with_real_search()
        logger.info("✅ 完整系统测试成功完成")
        
    except Exception as e:
        logger.error(f"❌ 系统测试失败: {e}")
        return False
    
    logger.info("🎉 所有系统测试完成！")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)