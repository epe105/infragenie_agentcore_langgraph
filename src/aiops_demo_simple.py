#!/usr/bin/env python3
"""
Simplified AIOps Demo Infrastructure
No OpenSearch, no CodePipeline - just minimal S3 for demo purposes
"""

import random
from typing import TypedDict, List
from aws_mcp_tools import get_aws_mcp_tools


async def simple_infrastructure_setup() -> dict:
    """
    Deploy MINIMAL AIOps infrastructure - just S3 bucket
    FAST - completes in seconds, not minutes
    """
    print("\n[SETUP] Deploying minimal AIOps infrastructure...")
    print("   (This is fast - no OpenSearch, no heavy resources)")

    result = {
        "success": False,
        "s3_bucket_name": "",
        "api_gateway_url": "",
        "message": ""
    }

    tools = await get_aws_mcp_tools()
    call_aws_tool = next((t for t in tools if t.name == "aws_call_aws"), None)

    if not call_aws_tool:
        result["message"] = "AWS MCP tools not available"
        return result

    try:
        # Generate unique resource names
        rnum = random.randint(1000, 9999)
        bucket_name = f"aiops-demo-events-{rnum}"

        print(f"   Creating S3 bucket: {bucket_name}")

        # Create S3 bucket for demo purposes
        await call_aws_tool._arun(
            cli_command=f"""aws s3api create-bucket --bucket {bucket_name} --region us-east-1"""
        )

        result["success"] = True
        result["s3_bucket_name"] = bucket_name
        result["message"] = f"✅ Infrastructure ready! S3 bucket: {bucket_name}"

        print(f"   ✅ S3 bucket created: {bucket_name}")
        print(f"   ✅ Setup complete - ready for demo execution")

    except Exception as e:
        result["message"] = f"Setup failed: {str(e)}"
        print(f"   ❌ Setup failed: {str(e)}")

    return result


async def simple_infrastructure_cleanup(bucket_name: str = None) -> dict:
    """
    Cleanup MINIMAL AIOps infrastructure - just delete S3 bucket
    FAST - completes in seconds
    """
    print("\n[CLEANUP] Removing AIOps demo infrastructure...")

    result = {
        "success": False,
        "message": ""
    }

    tools = await get_aws_mcp_tools()
    call_aws_tool = next((t for t in tools if t.name == "aws_call_aws"), None)

    if not call_aws_tool:
        result["message"] = "AWS MCP tools not available"
        return result

    try:
        if bucket_name:
            print(f"   Deleting S3 bucket: {bucket_name}")

            # Empty bucket first
            await call_aws_tool._arun(
                cli_command=f"""aws s3 rm s3://{bucket_name} --recursive"""
            )

            # Delete bucket
            await call_aws_tool._arun(
                cli_command=f"""aws s3api delete-bucket --bucket {bucket_name} --region us-east-1"""
            )

            result["success"] = True
            result["message"] = f"✅ Deleted S3 bucket: {bucket_name}"
            print(f"   ✅ Cleanup complete")
        else:
            result["message"] = "💡 List AIOps demo buckets:\n   aws s3 ls | grep aiops-demo-events"
            print(f"   💡 No bucket name provided")
            print(f"   List buckets: aws s3 ls | grep aiops-demo-events")

    except Exception as e:
        result["message"] = f"Cleanup failed: {str(e)}"
        print(f"   ❌ Cleanup failed: {str(e)}")

    return result
