#!/usr/bin/env python3
"""
Test script to verify AgentCore integration of security demo
"""

import asyncio
from infragenie_langgraph_agent import InfraGenieAgentCore


async def test_security_scan_detection():
    """Test that security scan requests are detected correctly"""
    agent = InfraGenieAgentCore()
    
    # Test cases
    test_cases = [
        ("Run a security scan on all S3 buckets", True),
        ("Check for vulnerable buckets", True),
        ("Security audit", True),
        ("Scan buckets for security issues", True),
        ("List my S3 buckets", False),
        ("Show me ansible inventory", False),
        ("What's the weather?", False),
    ]
    
    print("Testing security scan detection...\n")
    
    all_passed = True
    for message, expected in test_cases:
        result = agent._is_security_scan_request(message)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message}' → {result} (expected {expected})")
        if result != expected:
            all_passed = False
    
    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")
    return all_passed


async def test_security_scan_integration():
    """Test that security scan can be invoked (without actually running it)"""
    agent = InfraGenieAgentCore()
    
    print("\nTesting security scan integration...\n")
    
    # Check that the method exists
    if not hasattr(agent, '_run_security_scan'):
        print("❌ _run_security_scan method not found")
        return False
    
    if not hasattr(agent, '_format_security_response'):
        print("❌ _format_security_response method not found")
        return False
    
    print("✅ _run_security_scan method exists")
    print("✅ _format_security_response method exists")
    
    # Test response formatting with mock data
    mock_state = {
        "bucket_name": "test-bucket",
        "all_buckets": ["bucket1", "bucket2", "test-bucket"],
        "vulnerable_buckets": ["test-bucket"],
        "risk_score": 50.0,
        "remediation_required": True,
        "remediation_applied": True,
        "validation_passed": True,
        "logs": ["Test log entry"]
    }
    
    response = agent._format_security_response(mock_state)
    
    if "MULTI-AGENT SECURITY SCAN COMPLETE" in response:
        print("✅ Response formatting works correctly")
        print("\nSample response:")
        print(response)
        return True
    else:
        print("❌ Response formatting failed")
        return False


async def main():
    """Run all tests"""
    print("="*70)
    print("AgentCore Integration Test Suite")
    print("="*70)
    
    test1 = await test_security_scan_detection()
    test2 = await test_security_scan_integration()
    
    print("\n" + "="*70)
    if test1 and test2:
        print("✅ ALL TESTS PASSED - Integration is working!")
    else:
        print("❌ SOME TESTS FAILED - Check the output above")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
