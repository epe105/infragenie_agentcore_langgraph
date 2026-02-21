#!/usr/bin/env python3
"""
🧹 InfraGenie Demo Cleanup Script

Cleans up resources created by InfraGenie demos:
- EC2 instances created by Ansible AAP
- S3 buckets created by the demo
- Optionally lists resources before deletion

Usage:
    python cleanup_demo.py                    # Interactive cleanup
    python cleanup_demo.py --all              # Clean up everything
    python cleanup_demo.py --ec2              # Clean up EC2 only
    python cleanup_demo.py --s3               # Clean up S3 only
    python cleanup_demo.py --list             # List resources only
    python cleanup_demo.py --bucket <name>    # Clean up specific bucket
"""

import asyncio
import sys
import os
import re
from pathlib import Path
from typing import List, Dict

# Add src directory to Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

# Load environment variables
try:
    from dotenv import load_dotenv
    # Look for .env in project root
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        # Try scripts directory
        env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
except:
    pass


def print_banner():
    """Print the cleanup banner"""
    print("\n" + "="*70)
    print("🧹 INFRAGENIE DEMO CLEANUP")
    print("="*70)
    print("Clean up resources created by InfraGenie demos")
    print("="*70 + "\n")


def print_menu():
    """Print the cleanup menu"""
    print("Select cleanup option:\n")
    print("1. 🗑️  Clean up ALL resources (EC2 + S3)")
    print("2. 🖥️  Clean up EC2 instances only")
    print("3. 📦 Clean up S3 buckets only")
    print("4. 📋 List resources (no deletion)")
    print("5. 🎯 Clean up specific bucket")
    print("0. Exit\n")


async def list_s3_buckets() -> List[str]:
    """List all InfraGenie demo S3 buckets"""
    try:
        from aws_mcp_tools import get_aws_mcp_tools
        
        print("🔍 Scanning for InfraGenie S3 buckets...")
        
        tools = await get_aws_mcp_tools()
        call_aws_tool = next((t for t in tools if t.name == "aws_call_aws"), None)
        
        if not call_aws_tool:
            print("❌ AWS MCP tools not available")
            return []
        
        # List all buckets
        result = await call_aws_tool._arun(cli_command="aws s3api list-buckets")
        
        # Parse bucket names
        import json
        buckets = []
        try:
            result_data = json.loads(result)
            bucket_list = json.loads(result_data.get("response", {}).get("json", "{}"))
            
            for bucket in bucket_list.get("Buckets", []):
                bucket_name = bucket.get("Name", "")
                # Only include InfraGenie demo buckets
                if "infragenie" in bucket_name.lower():
                    buckets.append(bucket_name)
        except:
            # Fallback - parse from text
            for line in result.split('\n'):
                if 'infragenie' in line.lower():
                    match = re.search(r'infragenie-[a-z]+-\d+', line)
                    if match:
                        buckets.append(match.group())
        
        return buckets
    except Exception as e:
        print(f"❌ Error listing S3 buckets: {e}")
        return []


async def delete_s3_bucket(bucket_name: str) -> bool:
    """Delete a specific S3 bucket"""
    try:
        from aws_mcp_tools import get_aws_mcp_tools
        
        print(f"🗑️  Deleting bucket: {bucket_name}")
        
        tools = await get_aws_mcp_tools()
        call_aws_tool = next((t for t in tools if t.name == "aws_call_aws"), None)
        
        if not call_aws_tool:
            print("❌ AWS MCP tools not available")
            return False
        
        # First, try to empty the bucket
        print(f"   📦 Emptying bucket contents...")
        await call_aws_tool._arun(
            cli_command=f"aws s3 rm s3://{bucket_name} --recursive"
        )
        
        # Then delete the bucket
        print(f"   🗑️  Removing bucket...")
        result = await call_aws_tool._arun(
            cli_command=f"aws s3api delete-bucket --bucket {bucket_name}"
        )
        
        # Check if successful
        import json
        try:
            result_data = json.loads(result)
            status_code = result_data.get("response", {}).get("status_code")
            if status_code == 204 or status_code == 200:
                print(f"   ✅ Bucket '{bucket_name}' deleted successfully")
                return True
        except:
            pass
        
        # Fallback check
        if "error" not in result.lower():
            print(f"   ✅ Bucket '{bucket_name}' deleted successfully")
            return True
        else:
            print(f"   ❌ Failed to delete bucket: {result[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error deleting bucket '{bucket_name}': {e}")
        return False


async def cleanup_s3_buckets(bucket_name: str = None) -> int:
    """Clean up S3 buckets"""
    print("\n📦 S3 Bucket Cleanup")
    print("-" * 70)
    
    if bucket_name:
        # Clean up specific bucket
        success = await delete_s3_bucket(bucket_name)
        return 1 if success else 0
    else:
        # Clean up all InfraGenie buckets
        buckets = await list_s3_buckets()
        
        if not buckets:
            print("✅ No InfraGenie S3 buckets found")
            return 0
        
        print(f"Found {len(buckets)} InfraGenie bucket(s):")
        for bucket in buckets:
            print(f"   • {bucket}")
        
        print()
        confirm = input(f"Delete all {len(buckets)} bucket(s)? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("❌ Cleanup cancelled")
            return 0
        
        deleted = 0
        for bucket in buckets:
            if await delete_s3_bucket(bucket):
                deleted += 1
        
        print(f"\n✅ Deleted {deleted}/{len(buckets)} bucket(s)")
        return deleted


async def cleanup_ec2_instances():
    """Clean up EC2 instances via Ansible AAP job template"""
    print("\n🖥️  EC2 Instance Cleanup")
    print("-" * 70)
    
    try:
        from mcp_tools import get_mcp_tools
        
        print("🔍 Looking up AAP job template: 'AWS - Delete VM'...")
        
        # Get Ansible MCP tools
        tools = await get_mcp_tools()
        list_job_templates = next((t for t in tools if "list_job_templates" in t.name.lower()), None)
        run_job = next((t for t in tools if "run_job" in t.name.lower()), None)
        
        if not run_job or not list_job_templates:
            print("❌ Ansible MCP tools not available")
            print("   Please run manually: ansible-playbook ansible_demo/delete-aws-vm.yaml")
            return False
        
        # List job templates to find the ID
        templates_result = await list_job_templates._arun()
        
        # Parse to find the template ID for "AWS - Delete VM"
        import re
        template_id = None
        
        if "AWS - Delete VM" in templates_result:
            lines = templates_result.split('\n')
            for i, line in enumerate(lines):
                if 'AWS - Delete VM' in line:
                    # Look for ID in this line or nearby lines
                    for j in range(max(0, i-3), min(len(lines), i+4)):
                        id_match = re.search(r'(?:ID|id):\s*(\d+)', lines[j])
                        if id_match:
                            template_id = int(id_match.group(1))
                            break
                    if template_id:
                        break
        
        if not template_id:
            print("❌ Could not find 'AWS - Delete VM' job template in AAP")
            print("   Please run manually: ansible-playbook ansible_demo/delete-aws-vm.yaml")
            return False
        
        print(f"✅ Found template ID: {template_id}")
        
        confirm = input("\nRun AAP job template 'AWS - Delete VM' to delete EC2 instances? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("❌ Cleanup cancelled")
            return False
        
        print(f"📋 Launching AAP job template...")
        
        # Run the AAP job template
        result = await run_job._arun(
            template_id=template_id,
            extra_vars={}
        )
        
        # Try to extract job ID from result
        job_id_match = re.search(r'(?:ID|id):\s*(\d+)', result)
        if job_id_match:
            job_id = job_id_match.group(1)
            print(f"✅ AAP Job ID: {job_id} launched successfully")
            print(f"   Job is running in AAP. Check AAP for completion status.")
        else:
            print(f"✅ Job launched successfully")
            print(f"   Check AAP for job status and completion.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error launching AAP job: {e}")
        print("   Please run manually: ansible-playbook ansible_demo/delete-aws-vm.yaml")
        return False


async def list_resources():
    """List all InfraGenie resources"""
    print("\n📋 InfraGenie Resources")
    print("=" * 70)
    
    # List S3 buckets
    print("\n📦 S3 Buckets:")
    buckets = await list_s3_buckets()
    if buckets:
        for bucket in buckets:
            print(f"   • {bucket}")
    else:
        print("   (none found)")
    
    # EC2 instances
    print("\n🖥️  EC2 Instances:")
    print("   Run: aws ec2 describe-instances --filters 'Name=tag:ManagedBy,Values=ansible'")
    print("   Or check Ansible Automation Platform for running jobs")
    
    print("\n" + "=" * 70)


async def cleanup_all():
    """Clean up all resources"""
    print("\n🗑️  Cleaning up ALL InfraGenie resources")
    print("=" * 70)
    
    confirm = input("\n⚠️  This will delete ALL InfraGenie resources. Continue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Cleanup cancelled")
        return
    
    # Clean up S3 buckets
    s3_deleted = await cleanup_s3_buckets()
    
    # Clean up EC2 instances
    print()
    ec2_success = await cleanup_ec2_instances()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 CLEANUP SUMMARY")
    print("=" * 70)
    print(f"S3 Buckets Deleted: {s3_deleted}")
    print(f"EC2 Cleanup: {'✅ Success' if ec2_success else '❌ Failed or Skipped'}")
    print("=" * 70)


async def main():
    """Main entry point"""
    print_banner()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--all', '-a']:
            await cleanup_all()
            return
        elif arg in ['--ec2', '-e']:
            await cleanup_ec2_instances()
            return
        elif arg in ['--s3', '-s']:
            await cleanup_s3_buckets()
            return
        elif arg in ['--list', '-l']:
            await list_resources()
            return
        elif arg in ['--bucket', '-b']:
            if len(sys.argv) > 2:
                bucket_name = sys.argv[2]
                await cleanup_s3_buckets(bucket_name=bucket_name)
            else:
                print("❌ Error: --bucket requires a bucket name")
                print("   Usage: python cleanup_demo.py --bucket <bucket-name>")
            return
        elif arg in ['--help', '-h']:
            print(__doc__)
            return
        else:
            print(f"❌ Unknown option: {arg}")
            print("   Use --help for usage information")
            return
    
    # Interactive menu
    while True:
        print_menu()
        choice = input("Enter your choice (0-5): ").strip()
        
        if choice == '1':
            await cleanup_all()
            break
        elif choice == '2':
            await cleanup_ec2_instances()
            break
        elif choice == '3':
            await cleanup_s3_buckets()
            break
        elif choice == '4':
            await list_resources()
            break
        elif choice == '5':
            bucket_name = input("\nEnter bucket name: ").strip()
            if bucket_name:
                await cleanup_s3_buckets(bucket_name=bucket_name)
            else:
                print("❌ Invalid bucket name")
            break
        elif choice == '0':
            print("\n👋 Goodbye!\n")
            break
        else:
            print("\n❌ Invalid choice. Please try again.\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cleanup interrupted by user\n")
        sys.exit(0)
