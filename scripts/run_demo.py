#!/usr/bin/env python3
"""
🏗️ InfraGenie Demo Runner

Demonstrates InfraGenie via your deployed AWS AgentCore agent.
No local dependencies required - calls your production agent.

Choose from:
1. Infrastructure Lifecycle Demo - Full 7-agent workflow (Ansible + AWS MCP)
2. Security Scan Demo - S3 bucket security scanning (AWS MCP only)
3. Natural Language Query - Ask the agent anything

Usage:
    python run_demo.py                           # Interactive menu
    python run_demo.py --infrastructure          # Infrastructure demo
    python run_demo.py --security                # Security scan demo
    python run_demo.py --query "your question"   # Custom query

Requirements:
    - AgentCore CLI installed
    - Agent deployed to AgentCore
    - AWS credentials configured
"""

import subprocess
import json
import sys
import re
import os

def invoke_agent(prompt: str) -> str:
    """Invoke the deployed AgentCore agent"""
    print(f"📨 Sending to AgentCore: {prompt}\n")
    print("⏳ Waiting for response...\n")

    try:
        # Find agentcore CLI - check in venv first, then PATH
        agentcore_cmd = '.venv/bin/agentcore'
        if not os.path.exists(agentcore_cmd):
            agentcore_cmd = 'agentcore'

        # Call the deployed agent via agentcore CLI
        result = subprocess.run(
            [agentcore_cmd, 'invoke', json.dumps({"prompt": prompt})],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Extract the JSON response
        output = result.stdout
        
        # Try to find and parse the JSON response
        # Look for the Response: line
        if 'Response:' in output:
            # Extract everything after "Response:"
            response_part = output.split('Response:', 1)[1].strip()
            
            # Try to parse as JSON
            try:
                # Handle potential JSON with escaped newlines
                response_data = json.loads(response_part)
                result_text = response_data.get('result', '')
                
                # Decode escaped newlines if present
                if isinstance(result_text, str):
                    result_text = result_text.replace('\\n', '\n')
                
                return result_text
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract just the result field
                result_match = re.search(r'"result"\s*:\s*"(.*?)"(?:\s*,|\s*})', response_part, re.DOTALL)
                if result_match:
                    result_text = result_match.group(1)
                    # Decode escaped characters
                    result_text = result_text.replace('\\n', '\n')
                    result_text = result_text.replace('\\"', '"')
                    result_text = result_text.replace('\\t', '\t')
                    return result_text
                else:
                    return f"❌ Could not extract result from response.\n\nRaw output:\n{output}"
        else:
            return f"❌ No 'Response:' found in output.\n\nRaw output:\n{output}"
            
    except subprocess.TimeoutExpired:
        return "❌ Request timed out after 5 minutes"
    except FileNotFoundError:
        return "❌ 'agentcore' command not found. Make sure AgentCore CLI is installed and agent is deployed."
    except Exception as e:
        return f"❌ Error: {e}\n\nIf you see the raw output above, the agent responded but parsing failed."


def print_banner():
    """Print the banner"""
    print("\n" + "="*70)
    print("🏗️  INFRAGENIE AGENTCORE DEMO")
    print("="*70)
    print("Calling your DEPLOYED agent in AWS AgentCore")
    print("="*70 + "\n")


def print_menu():
    """Print the menu"""
    print("Select a demo:\n")
    print("1. 🏗️  Infrastructure Lifecycle Demo")
    print("   - Full 7-agent workflow via deployed agent")
    print("   - Provision EC2, create S3, detect & fix security issues\n")
    
    print("2. 🔒 Security Scan Demo")
    print("   - Scan all S3 buckets for vulnerabilities")
    print("   - Remediate public buckets\n")
    
    print("3. 💬 Custom Query")
    print("   - Ask your deployed agent anything")
    print("   - List inventories, check jobs, etc.\n")
    
    print("0. Exit\n")


def run_infrastructure_demo():
    """Run infrastructure lifecycle demo via deployed agent"""
    print("\n" + "="*70)
    print("🏗️  INFRASTRUCTURE LIFECYCLE DEMO")
    print("="*70 + "\n")
    
    # Use exact keyword that triggers the workflow
    prompt = "Run the infrastructure lifecycle demo"
    print(f"💡 Tip: Using trigger phrase to activate specialized workflow\n")
    response = invoke_agent(prompt)
    
    print("🤖 InfraGenie Response:\n")
    print(response)
    print("\n" + "="*70 + "\n")


def run_security_demo():
    """Run security scan demo via deployed agent"""
    print("\n" + "="*70)
    print("🔒 SECURITY SCAN DEMO")
    print("="*70 + "\n")
    
    # Use exact keyword that triggers the workflow
    prompt = "security scan"
    response = invoke_agent(prompt)
    
    print("🤖 InfraGenie Response:\n")
    print(response)
    print("\n" + "="*70 + "\n")


def run_custom_query():
    """Run a custom query via deployed agent"""
    print("\n" + "="*70)
    print("💬 CUSTOM QUERY")
    print("="*70)
    print("Examples:")
    print("  - List my Ansible inventories")
    print("  - Show me recent job executions")
    print("  - What S3 buckets do I have?")
    print("="*70 + "\n")
    
    prompt = input("📨 Your question: ").strip()
    
    if not prompt:
        print("❌ No question provided\n")
        return
    
    print()
    response = invoke_agent(prompt)
    
    print("🤖 InfraGenie Response:\n")
    print(response)
    print("\n" + "="*70 + "\n")


def main():
    """Main entry point"""
    print_banner()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--infrastructure', '-i']:
            run_infrastructure_demo()
            return
        elif sys.argv[1] in ['--security', '-s']:
            run_security_demo()
            return
        elif sys.argv[1] in ['--query', '-q']:
            if len(sys.argv) > 2:
                prompt = ' '.join(sys.argv[2:])
                print(f"\n📨 Query: {prompt}\n")
                response = invoke_agent(prompt)
                print("🤖 InfraGenie Response:\n")
                print(response)
                print()
            else:
                print("❌ Error: --query requires a message")
                print("   Usage: python demo_via_agentcore.py --query 'List my inventories'")
            return
        elif sys.argv[1] in ['--help', '-h']:
            print(__doc__)
            return
    
    # Interactive menu
    while True:
        print_menu()
        choice = input("Enter your choice (0-3): ").strip()
        
        if choice == '1':
            run_infrastructure_demo()
            break
        elif choice == '2':
            run_security_demo()
            break
        elif choice == '3':
            run_custom_query()
            break
        elif choice == '0':
            print("\n👋 Goodbye!\n")
            break
        else:
            print("\n❌ Invalid choice. Please try again.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user\n")
        sys.exit(0)
