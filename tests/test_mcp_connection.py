#!/usr/bin/env python3
"""
Quick test to verify AWS MCP connection works locally
"""

import asyncio
from aws_mcp_tools import get_aws_mcp_tools


async def main():
    print("🔍 Testing AWS MCP connection...\n")
    
    try:
        # Get AWS MCP tools
        tools = await get_aws_mcp_tools()
        
        print(f"✅ Successfully connected to AWS MCP server!")
        print(f"📦 Found {len(tools)} AWS MCP tools:\n")
        
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        print("\n✅ AWS MCP is ready for the security demo!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to AWS MCP server:")
        print(f"   {str(e)}")
        print("\n💡 Make sure your .env file has the correct OAuth credentials")
        return False


if __name__ == "__main__":
    asyncio.run(main())
