#!/usr/bin/env python3
"""
Interactive Demo Runner with Human-in-the-Loop Approval

This script runs the infrastructure/security demos via AgentCore
and handles human approval prompts in the command line.

The agent runs in AWS AgentCore (deployed), but this script
detects when it pauses for approval and prompts you locally.
"""

import subprocess
import json
import sys
import os
import uuid

def print_banner():
    """Print the banner"""
    print("\n" + "="*70)
    print("🏗️  INFRAGENIE AGENTCORE DEMO - INTERACTIVE MODE")
    print("="*70)
    print("Features:")
    print("  📋 System Prompt-Based Planner (Deep Agent Pattern)")
    print("  ⏸️  Human-in-the-Loop Approval")
    print("  🤖 Multi-Agent Workflow Orchestration")
    print("="*70 + "\n")


def invoke_agent_with_config(prompt: str, config: dict = None):
    """Invoke the agent with a specific configuration"""
    # Find agentcore CLI - check multiple locations
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    agentcore_cmd = os.path.join(project_root, '.venv/bin/agentcore')
    if not os.path.exists(agentcore_cmd):
        agentcore_cmd = '.venv/bin/agentcore'
        if not os.path.exists(agentcore_cmd):
            agentcore_cmd = 'agentcore'

    # Debug: Print the command being used
    print(f"   🔍 Using agentcore at: {agentcore_cmd}")
    if not os.path.exists(agentcore_cmd) and agentcore_cmd != 'agentcore':
        print(f"   ⚠️  Warning: Path does not exist!")

    payload = {"prompt": prompt}
    if config:
        payload["config"] = config

    try:
        # Make sure we use the absolute path
        if not agentcore_cmd.startswith('/'):
            agentcore_cmd = os.path.abspath(agentcore_cmd)

        result = subprocess.run(
            [agentcore_cmd, 'invoke', json.dumps(payload)],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd=project_root,  # Run from project root
            env=os.environ.copy()  # Pass current environment
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return None, "Request timed out", 1
    except Exception as e:
        return None, str(e), 1


def parse_agent_response(output: str):
    """Parse the agent response"""
    if 'Response:' in output:
        response_part = output.split('Response:', 1)[1].strip()
        try:
            import re
            # Try to find JSON object - be more lenient
            json_match = re.search(r'\{[^\}]*"result"[^\}]*\}', response_part, re.DOTALL)
            if json_match:
                # Replace control characters before parsing
                json_str = json_match.group()
                # Try to parse
                response_data = json.loads(json_str)
                result = response_data.get('result', '')
                # Decode escaped newlines if present
                if isinstance(result, str):
                    result = result.replace('\\n', '\n')
                return result
        except Exception as e:
            # If JSON parsing fails, try to extract just the result value
            try:
                result_match = re.search(r'"result":\s*"(.*)"(?:\s*\}|,)', response_part, re.DOTALL)
                if result_match:
                    result = result_match.group(1)
                    # Unescape
                    result = result.replace('\\n', '\n')
                    result = result.replace('\\"', '"')
                    return result
            except:
                pass
    return output


def check_for_approval_needed(response: str):
    """Check if the response indicates workflow is paused for approval"""
    # Remove newlines to handle text wrapping in the response
    normalized = response.replace('\n', '').replace('\r', '')
    return "WORKFLOW_PAUSED_FOR_APPROVAL" in normalized and "APPROVAL_STATE_B64:" in response


def extract_approval_state(response: str):
    """Extract approval state from base64-encoded response"""
    try:
        import base64

        start_marker = "APPROVAL_STATE_B64:"
        end_marker = "END_APPROVAL_STATE"

        start_idx = response.find(start_marker)
        end_idx = response.find(end_marker)

        if start_idx == -1 or end_idx == -1:
            return None

        b64_str = response[start_idx + len(start_marker):end_idx].strip()
        if not b64_str:
            return None

        # Decode from base64
        json_str = base64.b64decode(b64_str).decode()
        return json.loads(json_str)
    except Exception as e:
        print(f"Error extracting approval state: {e}")
        return None


def extract_approval_details(response: str):
    """Extract approval request details from response for display"""
    import re

    details = {}

    # Extract bucket name
    bucket_match = re.search(r'Bucket:\s*([^\n]+)', response)
    if bucket_match:
        details['bucket_name'] = bucket_match.group(1).strip()

    # Extract risk score
    risk_match = re.search(r'Risk_Score:\s*(\d+)', response)
    if risk_match:
        details['risk_score'] = int(risk_match.group(1))

    # Try to get instance_id from approval state if available
    approval_data = extract_approval_state(response)
    if approval_data and approval_data.get("workflow_type") == "infrastructure":
        state = approval_data.get("state", {})
        if state.get("instance_id"):
            details['instance_id'] = state["instance_id"]

    return details


def prompt_for_approval(details: dict) -> bool:
    """Prompt the user for approval"""
    print("\n" + "="*70)
    print("🚨 REMEDIATION APPROVAL REQUEST")
    print("="*70)

    if details.get('instance_id'):
        print(f"\n📊 Infrastructure Context:")
        print(f"   • EC2 Instance: {details.get('instance_id', 'N/A')}")
        print(f"   • S3 Bucket: {details.get('bucket_name', 'unknown')}")
    else:
        print(f"\n📦 Bucket: {details.get('bucket_name', 'unknown')}")

    print(f"⚠️  Risk Score: {details.get('risk_score', 0)}/100")

    print(f"\n🔧 Proposed Remediation:")
    print(f"   • Action: Block all public access")
    print(f"   • Method: AWS S3 Public Access Block")
    print(f"   • Configuration:")
    print(f"     - BlockPublicAcls: true")
    print(f"     - IgnorePublicAcls: true")
    print(f"     - BlockPublicPolicy: true")
    print(f"     - RestrictPublicBuckets: true")

    print(f"\n📋 Compliance Frameworks:")
    print(f"   • CIS AWS Foundations: 2.1.5")
    print(f"   • NIST 800-53: AC-3")
    print(f"   • PCI DSS: 1.2.1")
    print(f"   • GDPR: Article 32")

    print(f"\n⚠️  Impact Assessment:")
    print(f"   • Public access to this bucket will be blocked")
    print(f"   • Applications relying on public access may be affected")

    print("\n" + "="*70)

    # Get user input
    while True:
        try:
            response = input("👤 Do you approve this remediation? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                print("✅ APPROVAL GRANTED\n")
                print("="*70)
                return True
            elif response in ['no', 'n']:
                print("❌ APPROVAL DENIED\n")
                print("="*70)
                return False
            else:
                print("Invalid input. Please enter 'yes' or 'no'")
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️  Cancelled by user\n")
            return False


def run_infrastructure_demo():
    """Run infrastructure demo with interactive approval"""
    print("\n📨 Starting Infrastructure Lifecycle Demo...")

    # Step 1: Create Plan
    print("\n" + "="*70)
    print("STEP 1: CREATING EXECUTION PLAN")
    print("="*70)
    print("⏳ Asking InfraGenie to create a plan...\n")

    plan_prompt = "Create a plan for the infrastructure lifecycle demo"
    output, error, returncode = invoke_agent_with_config(plan_prompt, None)

    if returncode != 0:
        print(f"❌ Error creating plan:")
        print(f"   Return code: {returncode}")
        print(f"   Stderr: {error}")
        print(f"   Stdout: {output}")
        return

    plan_response = parse_agent_response(output)
    print("\n🤖 InfraGenie Plan:\n")
    print(plan_response)
    print()

    # Step 2: Ask user if they want to proceed
    print("="*70)
    while True:
        try:
            proceed = input("👤 Do you want to execute this plan? (yes/no): ").strip().lower()
            if proceed in ['yes', 'y']:
                print("✅ PROCEEDING WITH EXECUTION\n")
                print("="*70)
                break
            elif proceed in ['no', 'n']:
                print("❌ EXECUTION CANCELLED\n")
                print("="*70)
                return
            else:
                print("Invalid input. Please enter 'yes' or 'no'")
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️  Cancelled by user\n")
            return

    # Step 3: Execute the workflow
    print("\n" + "="*70)
    print("STEP 2: EXECUTING WORKFLOW")
    print("="*70)
    print("⏳ Running Graph 1 & 2 via AgentCore...\n")

    prompt = "Run the infrastructure lifecycle demo"
    output, error, returncode = invoke_agent_with_config(prompt, None)

    if returncode != 0:
        print(f"❌ Error: {error}")
        return

    response = parse_agent_response(output)

    # Check if workflow needs approval
    if check_for_approval_needed(response):
        print("\n⏸️  Workflow paused for human approval\n")

        # Extract approval state
        approval_data = extract_approval_state(response)
        if not approval_data:
            print("❌ Error: Could not extract approval state")
            return

        # Extract display details
        details = extract_approval_details(response)

        # Prompt user for approval
        approved = prompt_for_approval(details)

        # Continue with Graph 3
        print(f"\n📨 Continuing to Graph 3 with approval decision...")
        print("⏳ Running remediation in AgentCore...\n")

        continuation_payload = {
            "prompt": "continue",  # Placeholder
            "approval_continuation": {
                "state": approval_data["state"],
                "approved": approved,
                "workflow_type": approval_data["workflow_type"]
            }
        }

        # Find agentcore CLI
        agentcore_cmd = '.venv/bin/agentcore'
        if not os.path.exists(agentcore_cmd):
            agentcore_cmd = 'agentcore'

        try:
            result = subprocess.run(
                [agentcore_cmd, 'invoke', json.dumps(continuation_payload)],
                capture_output=True,
                text=True,
                timeout=600
            )
            output = result.stdout
            response = parse_agent_response(output)
        except Exception as e:
            print(f"❌ Error continuing workflow: {e}")
            return

    # Display final response
    print("\n🤖 InfraGenie Response:\n")
    print(response)
    print()


def run_security_demo():
    """Run security demo with interactive approval"""
    print("\n📨 Starting Security Scan Demo...")

    # Step 1: Create Plan
    print("\n" + "="*70)
    print("STEP 1: CREATING EXECUTION PLAN")
    print("="*70)
    print("⏳ Asking InfraGenie to create a plan...\n")

    plan_prompt = "Create a plan for scanning S3 buckets for security issues"
    output, error, returncode = invoke_agent_with_config(plan_prompt, None)

    if returncode != 0:
        print(f"❌ Error creating plan: {error}")
        return

    plan_response = parse_agent_response(output)
    print("\n🤖 InfraGenie Plan:\n")
    print(plan_response)
    print()

    # Step 2: Ask user if they want to proceed
    print("="*70)
    while True:
        try:
            proceed = input("👤 Do you want to execute this plan? (yes/no): ").strip().lower()
            if proceed in ['yes', 'y']:
                print("✅ PROCEEDING WITH EXECUTION\n")
                print("="*70)
                break
            elif proceed in ['no', 'n']:
                print("❌ EXECUTION CANCELLED\n")
                print("="*70)
                return
            else:
                print("Invalid input. Please enter 'yes' or 'no'")
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️  Cancelled by user\n")
            return

    # Step 3: Execute the workflow
    print("\n" + "="*70)
    print("STEP 2: EXECUTING WORKFLOW")
    print("="*70)
    print("⏳ Running Graph 1 & 2 via AgentCore...\n")

    prompt = "security scan"
    output, error, returncode = invoke_agent_with_config(prompt, None)

    if returncode != 0:
        print(f"❌ Error: {error}")
        return

    response = parse_agent_response(output)

    # Check if workflow needs approval
    if check_for_approval_needed(response):
        print("\n⏸️  Workflow paused for human approval\n")

        # Extract approval state
        approval_data = extract_approval_state(response)
        if not approval_data:
            print("❌ Error: Could not extract approval state")
            return

        # Extract display details
        details = extract_approval_details(response)

        # Prompt user for approval
        approved = prompt_for_approval(details)

        # Continue with Graph 3
        print(f"\n📨 Continuing to Graph 3 with approval decision...")
        print("⏳ Running remediation in AgentCore...\n")

        continuation_payload = {
            "prompt": "continue",  # Placeholder
            "approval_continuation": {
                "state": approval_data["state"],
                "approved": approved,
                "workflow_type": approval_data["workflow_type"]
            }
        }

        # Find agentcore CLI
        agentcore_cmd = '.venv/bin/agentcore'
        if not os.path.exists(agentcore_cmd):
            agentcore_cmd = 'agentcore'

        try:
            result = subprocess.run(
                [agentcore_cmd, 'invoke', json.dumps(continuation_payload)],
                capture_output=True,
                text=True,
                timeout=600
            )
            output = result.stdout
            response = parse_agent_response(output)
        except Exception as e:
            print(f"❌ Error continuing workflow: {e}")
            return

    # Display final response
    print("\n🤖 InfraGenie Response:\n")
    print(response)
    print()


def run_with_prompt(user_prompt: str):
    """Run demo based on natural language prompt with two-level approval"""
    print(f"\n📨 Processing request: '{user_prompt}'")

    # Step 1: Create Plan
    print("\n" + "="*70)
    print("STEP 1: CREATING EXECUTION PLAN")
    print("="*70)
    print("⏳ Asking InfraGenie to create a plan...\n")

    plan_prompt = f"Create a plan for: {user_prompt}"
    output, error, returncode = invoke_agent_with_config(plan_prompt, None)

    if returncode != 0:
        print(f"❌ Error creating plan:")
        print(f"   Return code: {returncode}")
        print(f"   Stderr: {error}")
        print(f"   Stdout: {output}")
        return

    plan_response = parse_agent_response(output)
    print("\n🤖 InfraGenie Plan:\n")
    print(plan_response)
    print()

    # Step 2: Ask user if they want to proceed
    print("="*70)
    while True:
        try:
            proceed = input("👤 Do you want to execute this plan? (yes/no): ").strip().lower()
            if proceed in ['yes', 'y']:
                print("✅ PROCEEDING WITH EXECUTION\n")
                print("="*70)
                break
            elif proceed in ['no', 'n']:
                print("❌ EXECUTION CANCELLED\n")
                print("="*70)
                return
            else:
                print("Invalid input. Please enter 'yes' or 'no'")
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️  Cancelled by user\n")
            return

    # Step 3: Execute the workflow
    print("\n" + "="*70)
    print("STEP 2: EXECUTING WORKFLOW")
    print("="*70)
    print("⏳ Running workflow via AgentCore...\n")

    output, error, returncode = invoke_agent_with_config(user_prompt, None)

    if returncode != 0:
        print(f"❌ Error: {error}")
        return

    response = parse_agent_response(output)

    # Check if workflow needs approval
    if check_for_approval_needed(response):
        print("\n⏸️  Workflow paused for human approval\n")

        # Extract approval state
        approval_data = extract_approval_state(response)
        if not approval_data:
            print("❌ Error: Could not extract approval state")
            return

        # Extract display details
        details = extract_approval_details(response)

        # Prompt user for approval
        approved = prompt_for_approval(details)

        # Continue with Graph 3
        print(f"\n📨 Continuing to Graph 3 with approval decision...")
        print("⏳ Running remediation in AgentCore...\n")

        continuation_payload = {
            "prompt": "continue",
            "approval_continuation": {
                "state": approval_data["state"],
                "approved": approved,
                "workflow_type": approval_data["workflow_type"]
            }
        }

        # Find agentcore CLI
        agentcore_cmd = '.venv/bin/agentcore'
        if not os.path.exists(agentcore_cmd):
            agentcore_cmd = 'agentcore'

        try:
            result = subprocess.run(
                [agentcore_cmd, 'invoke', json.dumps(continuation_payload)],
                capture_output=True,
                text=True,
                timeout=600
            )
            output = result.stdout
            response = parse_agent_response(output)
        except Exception as e:
            print(f"❌ Error continuing workflow: {e}")
            return

    # Display final response
    print("\n🤖 InfraGenie Response:\n")
    print(response)
    print()


def run_aiops_setup():
    """Setup AIOps infrastructure (run before demo)"""
    print("\n📨 Starting AIOps Infrastructure Setup...")
    print("⚠️  This takes 15-20 minutes. Run this BEFORE your customer demo.\n")

    # Step 1: Create Plan
    print("\n" + "="*70)
    print("STEP 1: CREATING DEPLOYMENT PLAN")
    print("="*70)
    print("⏳ Asking InfraGenie to create a plan...\n")

    plan_prompt = "Deploy AIOps infrastructure for network event correlation including OpenSearch, Lambda, API Gateway, and CodePipeline"
    output, error, returncode = invoke_agent_with_config(plan_prompt, None)

    if returncode != 0:
        print(f"❌ Error creating plan:")
        print(f"   Return code: {returncode}")
        print(f"   Stderr: {error}")
        print(f"   Stdout: {output}")
        return

    plan_response = parse_agent_response(output)
    print("\n🤖 InfraGenie Plan:\n")
    print(plan_response)
    print()

    # Step 2: Ask user if they want to proceed
    print("="*70)
    while True:
        try:
            proceed = input("👤 Do you want to deploy this infrastructure? (yes/no): ").strip().lower()
            if proceed in ['yes', 'y']:
                print("✅ PROCEEDING WITH DEPLOYMENT\n")
                print("="*70)
                break
            elif proceed in ['no', 'n']:
                print("❌ DEPLOYMENT CANCELLED\n")
                print("="*70)
                return
            else:
                print("Invalid input. Please enter 'yes' or 'no'")
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️  Cancelled by user\n")
            return

    # Step 3: Execute deployment
    print("\n" + "="*70)
    print("STEP 2: DEPLOYING INFRASTRUCTURE")
    print("="*70)
    print("⏳ Deploying AIOps infrastructure...\n")
    print("⚠️  OpenSearch deployment takes 10-15 minutes...\n")

    prompt = "Deploy AIOps infrastructure for network event correlation"
    output, error, returncode = invoke_agent_with_config(prompt, None)

    if returncode != 0:
        print(f"❌ Error: {error}")
        return

    response = parse_agent_response(output)
    print("\n🤖 InfraGenie Response:\n")
    print(response)
    print()

    print("\n✅ Infrastructure deployed! You're ready to run the demo.\n")


def run_aiops_cleanup():
    """Cleanup AIOps infrastructure (run after demo)"""
    print("\n📨 Starting AIOps Infrastructure Cleanup...")

    # Step 1: Create Plan
    print("\n" + "="*70)
    print("STEP 1: CREATING CLEANUP PLAN")
    print("="*70)
    print("⏳ Asking InfraGenie to create a plan...\n")

    plan_prompt = "Cleanup AIOps demo infrastructure including OpenSearch domain, Lambda function, API Gateway, CodePipeline, and S3 buckets"
    output, error, returncode = invoke_agent_with_config(plan_prompt, None)

    if returncode != 0:
        print(f"❌ Error creating plan:")
        print(f"   Return code: {returncode}")
        print(f"   Stderr: {error}")
        print(f"   Stdout: {output}")
        return

    plan_response = parse_agent_response(output)
    print("\n🤖 InfraGenie Plan:\n")
    print(plan_response)
    print()

    # Step 2: Ask user if they want to proceed
    print("="*70)
    while True:
        try:
            proceed = input("👤 Do you want to delete all AIOps resources? (yes/no): ").strip().lower()
            if proceed in ['yes', 'y']:
                print("✅ PROCEEDING WITH CLEANUP\n")
                print("="*70)
                break
            elif proceed in ['no', 'n']:
                print("❌ CLEANUP CANCELLED\n")
                print("="*70)
                return
            else:
                print("Invalid input. Please enter 'yes' or 'no'")
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️  Cancelled by user\n")
            return

    # Step 3: Execute cleanup
    print("\n" + "="*70)
    print("STEP 2: CLEANING UP RESOURCES")
    print("="*70)
    print("⏳ Deleting AIOps infrastructure...\n")

    prompt = "Cleanup AIOps demo infrastructure"
    output, error, returncode = invoke_agent_with_config(prompt, None)

    if returncode != 0:
        print(f"❌ Error: {error}")
        return

    response = parse_agent_response(output)
    print("\n🤖 InfraGenie Response:\n")
    print(response)
    print()

    print("\n✅ All AIOps resources cleaned up!\n")


def run_aiops_demo():
    """Run AIOps network correlation demo (fast, customer-ready)"""
    print("\n📨 Starting AIOps Network Correlation Demo...")
    print("🚀 This is the FAST demo - infrastructure must be pre-deployed!\n")

    # Step 1: Create Plan
    print("\n" + "="*70)
    print("STEP 1: CREATING EXECUTION PLAN")
    print("="*70)
    print("⏳ Asking InfraGenie to create a plan...\n")

    plan_prompt = "Create a plan for running the AIOps network correlation demo that injects events from APM, Network Monitoring, and Infrastructure tools and uses AI to identify the root cause"
    output, error, returncode = invoke_agent_with_config(plan_prompt, None)

    if returncode != 0:
        print(f"❌ Error creating plan:")
        print(f"   Return code: {returncode}")
        print(f"   Stderr: {error}")
        print(f"   Stdout: {output}")
        return

    plan_response = parse_agent_response(output)
    print("\n🤖 InfraGenie Plan:\n")
    print(plan_response)
    print()

    # Step 2: Ask user if they want to proceed
    print("="*70)
    while True:
        try:
            proceed = input("👤 Do you want to execute this plan? (yes/no): ").strip().lower()
            if proceed in ['yes', 'y']:
                print("✅ PROCEEDING WITH EXECUTION\n")
                print("="*70)
                break
            elif proceed in ['no', 'n']:
                print("❌ EXECUTION CANCELLED\n")
                print("="*70)
                return
            else:
                print("Invalid input. Please enter 'yes' or 'no'")
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️  Cancelled by user\n")
            return

    # Step 3: Execute the workflow
    print("\n" + "="*70)
    print("STEP 2: EXECUTING WORKFLOW")
    print("="*70)
    print("⏳ Running AIOps demo via AgentCore...\n")

    prompt = "Run the AIOps demo"
    output, error, returncode = invoke_agent_with_config(prompt, None)

    if returncode != 0:
        print(f"❌ Error: {error}")
        return

    response = parse_agent_response(output)

    # Check if workflow needs approval
    if check_for_approval_needed(response):
        print("\n⏸️  Workflow paused for human approval\n")

        # Extract approval state
        approval_data = extract_approval_state(response)
        if not approval_data:
            print("❌ Error: Could not extract approval state")
            return

        # Extract display details
        details = extract_approval_details(response)

        # Prompt user for approval
        approved = prompt_for_approval(details)

        # Continue with Graph 3
        print(f"\n📨 Continuing to Graph 3 with approval decision...")
        print("⏳ Running remediation in AgentCore...\n")

        continuation_payload = {
            "prompt": "continue",
            "approval_continuation": {
                "state": approval_data["state"],
                "approved": approved,
                "workflow_type": approval_data["workflow_type"]
            }
        }

        # Find agentcore CLI
        agentcore_cmd = '.venv/bin/agentcore'
        if not os.path.exists(agentcore_cmd):
            agentcore_cmd = 'agentcore'

        try:
            result = subprocess.run(
                [agentcore_cmd, 'invoke', json.dumps(continuation_payload)],
                capture_output=True,
                text=True,
                timeout=600
            )
            output = result.stdout
            response = parse_agent_response(output)
        except Exception as e:
            print(f"❌ Error continuing workflow: {e}")
            return

    # Display final response
    print("\n🤖 InfraGenie Response:\n")
    print(response)
    print()


def main():
    """Main entry point"""
    print_banner()

    if len(sys.argv) > 1:
        if sys.argv[1] in ['--infrastructure', '-i']:
            run_infrastructure_demo()
            return
        elif sys.argv[1] in ['--security', '-s']:
            run_security_demo()
            return
        elif sys.argv[1] in ['--aiops', '-a']:
            run_aiops_demo()
            return
        elif sys.argv[1] in ['--prompt', '-p']:
            if len(sys.argv) < 3:
                print("❌ Error: --prompt requires a prompt argument")
                print("\nExample:")
                print("  python run_demo_interactive.py --prompt 'provision an ec2 vm and an s3 bucket'")
                print()
                return
            user_prompt = sys.argv[2]
            run_with_prompt(user_prompt)
            return
        elif sys.argv[1] in ['--help', '-h']:
            print("Usage:")
            print("  python run_demo_interactive.py --infrastructure  # Infrastructure demo")
            print("  python run_demo_interactive.py --security        # Security scan demo")
            print("  python run_demo_interactive.py --aiops           # AIOps observability demo")
            print("  python run_demo_interactive.py --prompt '<prompt>'  # Natural language prompt")
            print()
            print("Examples:")
            print("  python run_demo_interactive.py --prompt 'provision an ec2 vm and an s3 bucket'")
            print("  python run_demo_interactive.py --prompt 'scan my s3 buckets for security issues'")
            print()
            return

    # Interactive menu
    print("Select a demo:\n")
    print("1. 🏗️  Infrastructure Lifecycle Demo")
    print("   - 📋 CREATES PLAN using system prompt-based planner")
    print("   - Provision EC2 + S3, detect security issue")
    print("   - ⏸️  PROMPTS FOR APPROVAL before remediation\n")

    print("2. 🔒 Security Scan Demo")
    print("   - 📋 CREATES PLAN using system prompt-based planner")
    print("   - Scan all S3 buckets for vulnerabilities")
    print("   - ⏸️  PROMPTS FOR APPROVAL before remediation\n")

    print("3. 🤖 AIOps Network Correlation Demo")
    print("   a. 🔧 Setup Infrastructure (15-20 min - DO BEFORE DEMO)")
    print("   b. 🚀 Run Demo (2-3 min - CUSTOMER READY)")
    print("   c. 🗑️  Cleanup Resources (5-10 min - DO AFTER DEMO)\n")

    print("0. Exit\n")

    while True:
        choice = input("Enter your choice (0-3, or 3a/3b/3c): ").strip().lower()

        if choice == '1':
            run_infrastructure_demo()
            break
        elif choice == '2':
            run_security_demo()
            break
        elif choice == '3' or choice == '3b' or choice == 'b':
            run_aiops_demo()
            break
        elif choice == '3a' or choice == 'a':
            run_aiops_setup()
            break
        elif choice == '3c' or choice == 'c':
            run_aiops_cleanup()
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
