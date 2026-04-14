#!/usr/bin/env python3
"""
Direct test of AIOps demo - bypass Streamlit
"""

import sys
import asyncio

# Disable bytecode compilation
sys.dont_write_bytecode = True

# Add src to path
sys.path.insert(0, '/Users/eevangelista/work/infragenie_agentcore_langgraph/src')

from infragenie_langgraph_agent import InfraGenieAgentCore

async def main():
    print("=" * 70)
    print("Testing AIOps Demo Detection & Execution")
    print("=" * 70)
    print()

    # Create agent
    agent = InfraGenieAgentCore()

    # Test message
    message = "Run the AIOps network correlation demo"
    print(f"Test message: '{message}'")
    print()

    # Check detection
    is_demo = agent._is_aiops_demo_request(message)
    print(f"Detection result: {is_demo}")
    print()

    if is_demo:
        print("✅ Detection works! Running demo...")
        print()

        # Initialize and run
        await agent.initialize()
        response = await agent.process_message(message)

        print()
        print("=" * 70)
        print("Demo Response:")
        print("=" * 70)
        print(response)
    else:
        print("❌ Detection FAILED - debug output above should show why")

if __name__ == "__main__":
    asyncio.run(main())
