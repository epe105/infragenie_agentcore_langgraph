#!/usr/bin/env python3
"""
Gradio Frontend for InfraGenie AgentCore Demo

An interactive web interface for running infrastructure demos with approval gates.
"""

import gradio as gr
import subprocess
import json
import os
from pathlib import Path

def invoke_agent(prompt, config=None):
    """Invoke the AgentCore agent"""
    project_root = Path(__file__).parent
    agentcore_cmd = project_root / '.venv/bin/agentcore'

    if not agentcore_cmd.exists():
        agentcore_cmd = 'agentcore'

    payload = {"prompt": prompt}
    if config:
        payload["config"] = config

    try:
        result = subprocess.run(
            [str(agentcore_cmd), 'invoke', json.dumps(payload)],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(project_root),
            env=os.environ.copy()
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return None, str(e), 1


def parse_agent_response(output):
    """Parse the agent response and extract clean content"""
    try:
        import re

        # First, try to find and parse the JSON response
        if 'Response:' in output:
            response_part = output.split('Response:', 1)[1].strip()

            # Try to parse as JSON - handle the full JSON structure properly
            try:
                # Find the JSON object (starts with { and handle nested structures)
                json_start = response_part.find('{')
                if json_start != -1:
                    # Simple approach: try to parse from the first { to the end
                    json_str = response_part[json_start:]
                    # Try to load it - json.loads will handle nested structures
                    response_data = json.loads(json_str)

                    if isinstance(response_data, dict) and 'result' in response_data:
                        result = response_data['result']
                        # The result string has escaped newlines - decode them
                        if isinstance(result, str):
                            # Replace literal \n with actual newlines
                            result = result.encode().decode('unicode_escape')
                        return result
            except json.JSONDecodeError:
                # If JSON parsing fails, try regex approach
                json_match = re.search(r'\{"result":\s*"(.*?)"\s*\}', response_part, re.DOTALL)
                if json_match:
                    result = json_match.group(1)
                    # Unescape the string
                    result = result.encode().decode('unicode_escape')
                    return result

        # If we couldn't parse it, return the original
        return output

    except Exception as e:
        # If anything goes wrong, return original output
        return output


def format_response_markdown(text):
    """Format response text for Gradio markdown display"""
    # Ensure proper line breaks in markdown by adding double spaces before newlines
    # Or wrap in code block for better formatting
    return f"```\n{text}\n```"


def check_for_approval_needed(response):
    """Check if approval is needed"""
    normalized = response.replace('\n', '').replace('\r', '')
    return "WORKFLOW_PAUSED_FOR_APPROVAL" in normalized and "APPROVAL_STATE_B64:" in response


def extract_approval_state(response):
    """Extract approval state from response"""
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

        json_str = base64.b64decode(b64_str).decode()
        return json.loads(json_str)
    except Exception as e:
        return None


def extract_approval_details(response):
    """Extract approval details for display"""
    import re
    details = {}

    bucket_match = re.search(r'Bucket:\s*([^\n]+)', response)
    if bucket_match:
        details['bucket_name'] = bucket_match.group(1).strip()

    risk_match = re.search(r'Risk_Score:\s*(\d+)', response)
    if risk_match:
        details['risk_score'] = int(risk_match.group(1))

    approval_data = extract_approval_state(response)
    if approval_data and approval_data.get("workflow_type") == "infrastructure":
        state = approval_data.get("state", {})
        if state.get("instance_id"):
            details['instance_id'] = state["instance_id"]

    return details


def create_plan(demo_type, custom_prompt=""):
    """Create execution plan"""
    if demo_type == "Infrastructure Lifecycle":
        prompt = "Create a plan for the infrastructure lifecycle demo"
    elif demo_type == "Security Scan":
        prompt = "Create a plan for scanning S3 buckets for security issues"
    elif demo_type == "Custom" and custom_prompt:
        prompt = f"Create a plan for: {custom_prompt}"
    else:
        return "❌ Error: Please select a demo type or enter a custom prompt", None, None

    output, error, returncode = invoke_agent(prompt)

    if returncode != 0:
        return f"❌ Error creating plan:\n{error}", None, None

    plan_response = parse_agent_response(output)

    formatted_plan = f"""
## 🤖 InfraGenie Execution Plan

{format_response_markdown(plan_response)}

---
**Status:** ✅ Plan created successfully
**Next Step:** Review and approve the plan to proceed with execution
"""

    return formatted_plan, prompt, plan_response


def execute_workflow(demo_type, custom_prompt=""):
    """Execute the workflow"""
    if demo_type == "Infrastructure Lifecycle":
        exec_prompt = "Run the infrastructure lifecycle demo"
    elif demo_type == "Security Scan":
        exec_prompt = "security scan"
    elif demo_type == "Custom" and custom_prompt:
        exec_prompt = custom_prompt
    else:
        return "❌ Error: Please select a demo type", None, None, None

    output, error, returncode = invoke_agent(exec_prompt)

    if returncode != 0:
        return f"❌ Error: {error}", None, None, None

    response = parse_agent_response(output)

    if check_for_approval_needed(response):
        approval_data = extract_approval_state(response)
        if not approval_data:
            return "❌ Error: Could not extract approval state", None, None, None

        details = extract_approval_details(response)

        # Format approval request
        approval_text = f"""
## 🚨 Remediation Approval Request

### 📊 Infrastructure Context
"""
        if details.get('instance_id'):
            approval_text += f"""
- **EC2 Instance:** `{details.get('instance_id', 'N/A')}`
- **S3 Bucket:** `{details.get('bucket_name', 'unknown')}`
"""
        else:
            approval_text += f"""
- **S3 Bucket:** `{details.get('bucket_name', 'unknown')}`
"""

        approval_text += f"""
### ⚠️ Risk Score: {details.get('risk_score', 0)}/100

### 🔧 Proposed Remediation
- **Action:** Block all public access
- **Method:** AWS S3 Public Access Block
- **Configuration:**
  - BlockPublicAcls: true
  - IgnorePublicAcls: true
  - BlockPublicPolicy: true
  - RestrictPublicBuckets: true

### 📋 Compliance Frameworks
- CIS AWS Foundations: 2.1.5
- NIST 800-53: AC-3
- PCI DSS: 1.2.1
- GDPR: Article 32

### ⚠️ Impact Assessment
- Public access to this bucket will be blocked
- Applications relying on public access may be affected

---
**Status:** ⏸️ Workflow paused - awaiting approval
"""

        return approval_text, approval_data, details, demo_type

    else:
        # No approval needed
        return f"## ✅ Workflow Completed\n\n{format_response_markdown(response)}", None, None, None


def apply_remediation(approval_data, approved, demo_type):
    """Apply or deny remediation"""
    if not approval_data:
        return "❌ Error: No approval data available"

    continuation_payload = {
        "prompt": "continue",
        "approval_continuation": {
            "state": approval_data["state"],
            "approved": approved,
            "workflow_type": approval_data["workflow_type"]
        }
    }

    project_root = Path(__file__).parent
    agentcore_cmd = project_root / '.venv/bin/agentcore'

    if not agentcore_cmd.exists():
        agentcore_cmd = 'agentcore'

    try:
        result = subprocess.run(
            [str(agentcore_cmd), 'invoke', json.dumps(continuation_payload)],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(project_root),
            env=os.environ.copy()
        )
        output = result.stdout
        response = parse_agent_response(output)

        if approved:
            return f"## ✅ Remediation Approved & Applied\n\n{format_response_markdown(response)}"
        else:
            return f"## ❌ Remediation Denied\n\n{format_response_markdown(response)}"

    except Exception as e:
        return f"❌ Error continuing workflow: {e}"


# Build the Gradio interface
with gr.Blocks(theme=gr.themes.Soft(), title="InfraGenie - Infrastructure Automation") as demo:

    # Store state
    plan_state = gr.State()
    approval_data_state = gr.State()
    demo_type_state = gr.State()

    # Header
    gr.Markdown("""
    # 🏗️ InfraGenie - Multi-Agent Infrastructure Automation

    Professional web interface for running infrastructure demos with approval gates.

    **Features:**
    - 📋 System Prompt-Based Planner (Deep Agent Pattern)
    - ⏸️ Human-in-the-Loop Approval Gates
    - 🤖 Multi-Agent Workflow Orchestration
    - 🔒 Security & Compliance Validation
    """)

    with gr.Tab("🚀 Run Demo"):
        gr.Markdown("## Step 1: Select Demo Type")

        demo_type = gr.Radio(
            ["Infrastructure Lifecycle", "Security Scan", "Custom"],
            label="Demo Type",
            value="Infrastructure Lifecycle"
        )

        custom_prompt = gr.Textbox(
            label="Custom Prompt (only if 'Custom' selected)",
            placeholder="provision an ec2 vm and an s3 bucket",
            visible=False
        )

        def show_custom(demo_type):
            return gr.update(visible=(demo_type == "Custom"))

        demo_type.change(show_custom, inputs=[demo_type], outputs=[custom_prompt])

        create_plan_btn = gr.Button("📋 Create Execution Plan", variant="primary", size="lg")

        plan_output = gr.Markdown()

        gr.Markdown("---")
        gr.Markdown("## Step 2: Approve Plan")

        with gr.Row():
            approve_plan_btn = gr.Button("✅ Approve & Execute", variant="primary")
            deny_plan_btn = gr.Button("❌ Deny Plan", variant="stop")

        execution_output = gr.Markdown()

        gr.Markdown("---")
        gr.Markdown("## Step 3: Approve Remediation")

        with gr.Row():
            approve_remediation_btn = gr.Button("✅ Approve Remediation", variant="primary")
            deny_remediation_btn = gr.Button("❌ Deny Remediation", variant="stop")

        final_output = gr.Markdown()

        # Event handlers
        def on_create_plan(demo_type, custom_prompt):
            plan_text, prompt, plan_data = create_plan(demo_type, custom_prompt)
            return plan_text, plan_data, demo_type

        create_plan_btn.click(
            on_create_plan,
            inputs=[demo_type, custom_prompt],
            outputs=[plan_output, plan_state, demo_type_state]
        )

        def on_approve_plan(demo_type, custom_prompt):
            exec_text, approval_data, details, dt = execute_workflow(demo_type, custom_prompt)
            return exec_text, approval_data

        approve_plan_btn.click(
            on_approve_plan,
            inputs=[demo_type, custom_prompt],
            outputs=[execution_output, approval_data_state]
        )

        deny_plan_btn.click(
            lambda: "❌ Plan denied by user. Execution cancelled.",
            outputs=[execution_output]
        )

        def on_approve_remediation(approval_data, demo_type):
            return apply_remediation(approval_data, True, demo_type)

        approve_remediation_btn.click(
            on_approve_remediation,
            inputs=[approval_data_state, demo_type_state],
            outputs=[final_output]
        )

        def on_deny_remediation(approval_data, demo_type):
            return apply_remediation(approval_data, False, demo_type)

        deny_remediation_btn.click(
            on_deny_remediation,
            inputs=[approval_data_state, demo_type_state],
            outputs=[final_output]
        )

    with gr.Tab("📚 Documentation"):
        gr.Markdown("""
        ## Architecture

        InfraGenie demonstrates the power of multi-agent orchestration:

        ### Components
        1. **Main Orchestrator Agent** - Routes requests to specialized components
        2. **Planner Component** - Creates execution plans using system prompt-based pattern
        3. **Infrastructure Workflow** - 7 specialized agents for infrastructure lifecycle
        4. **Security Workflow** - 5 specialized agents for security scanning

        ### Two-Level Approval Flow
        1. **Strategic Approval**: Review and approve the execution plan
        2. **Tactical Approval**: Review and approve specific remediations

        ### Technologies
        - AWS Bedrock AgentCore
        - LangGraph for multi-agent orchestration
        - Claude 3.5 Sonnet for intelligent decision-making
        - Ansible Automation Platform via MCP
        - AWS services via MCP

        ## Compliance Frameworks
        - CIS AWS Foundations Benchmark
        - NIST 800-53
        - PCI DSS
        - GDPR
        """)

    # Footer
    gr.Markdown("""
    ---
    <div style="text-align: center; color: #666;">
        <p>🏗️ InfraGenie - Multi-Agent Infrastructure Automation</p>
        <p style="font-size: 0.9rem;">Powered by AWS Bedrock AgentCore & LangGraph</p>
    </div>
    """)


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
