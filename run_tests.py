#!/usr/bin/env python3
"""Test runner for Deep Research system."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def run_unit_tests():
    """Run all unit tests."""
    print("\n" + "="*60)
    print("RUNNING UNIT TESTS")
    print("="*60)
    
    tests = [
        ("Basic Components", "tests.unit.test_basic_components", "test_all"),
        ("Database", "tests.unit.test_database", "test_database"),
        ("Real Search", "tests.unit.test_real_search", "test_real_search"),
        ("Web Fetch", "tests.unit.test_web_fetch", "test_web_fetch"),
    ]
    
    results = []
    for name, module_path, test_func in tests:
        try:
            print(f"\n[{name}]")
            module = __import__(module_path, fromlist=[test_func])
            func = getattr(module, test_func)
            result = await func()
            results.append((name, True))
            print(f"✅ {name} passed")
        except Exception as e:
            results.append((name, False))
            print(f"❌ {name} failed: {e}")
    
    return results


async def run_integration_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("RUNNING INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        ("Simple Flow", "tests.integration.test_simple_flow", "test_simple_flow"),
    ]
    
    results = []
    for name, module_path, test_func in tests:
        try:
            print(f"\n[{name}]")
            module = __import__(module_path, fromlist=[test_func])
            func = getattr(module, test_func)
            result = await func()
            results.append((name, True))
            print(f"✅ {name} passed")
        except Exception as e:
            results.append((name, False))
            print(f"❌ {name} failed: {e}")
    
    return results


async def run_e2e_tests():
    """Run all end-to-end tests."""
    print("\n" + "="*60)
    print("RUNNING END-TO-END TESTS")
    print("="*60)
    
    tests = [
        ("Simple Query", "tests.e2e.test_simple_query", "test_simple_query"),
        ("Enhanced System", "tests.e2e.test_enhanced_system", "test_enhanced_system"),
    ]
    
    results = []
    for name, module_path, test_func in tests:
        try:
            print(f"\n[{name}]")
            module = __import__(module_path, fromlist=[test_func])
            func = getattr(module, test_func)
            result = await func()
            results.append((name, True))
            print(f"✅ {name} passed")
        except Exception as e:
            results.append((name, False))
            print(f"❌ {name} failed: {e}")
    
    return results


async def main():
    """Run all tests."""
    print("="*60)
    print("DEEP RESEARCH SYSTEM - TEST SUITE")
    print("="*60)
    
    all_results = []
    
    # Run unit tests
    unit_results = await run_unit_tests()
    all_results.extend([("Unit/" + name, passed) for name, passed in unit_results])
    
    # Run integration tests
    integration_results = await run_integration_tests()
    all_results.extend([("Integration/" + name, passed) for name, passed in integration_results])
    
    # Run e2e tests (optional - they use API calls)
    if "--e2e" in sys.argv:
        e2e_results = await run_e2e_tests()
        all_results.extend([("E2E/" + name, passed) for name, passed in e2e_results])
    else:
        print("\n[Note: Skipping E2E tests. Use --e2e flag to include them]")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, p in all_results if p)
    total = len(all_results)
    
    for name, passed_flag in all_results:
        status = "✅" if passed_flag else "❌"
        print(f"{status} {name}")
    
    print("\n" + "-"*60)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)