#!/usr/bin/env python3
"""
Streamlit Frontend for InfraGenie AgentCore Demo

A professional web interface for running infrastructure demos with approval gates.
Shows all steps in a continuous timeline for easy review.
"""

import sys
sys.dont_write_bytecode = True  # Disable .pyc files

import streamlit as st

# Clear all caches to ensure fresh code
st.cache_data.clear()
st.cache_resource.clear()
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Intelligent Operations Demos",
    page_icon="🏗️",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .timeline-step {
        padding: 2rem;
        border-radius: 12px;
        background: white;
        border-left: 5px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1.5rem 0;
    }
    .timeline-step.completed {
        border-left-color: #48bb78;
        background: #f0fff4;
    }
    .timeline-step.pending {
        border-left-color: #f6ad55;
        background: #fffaf0;
    }
    .step-number {
        display: inline-block;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        line-height: 40px;
        font-weight: bold;
        font-size: 1.2rem;
        margin-right: 1rem;
    }
    .step-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2d3748;
        display: inline-block;
        vertical-align: middle;
    }
    .response-container {
        padding: 2rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-left: 5px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1.5rem 0;
        font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
        white-space: pre-wrap;
        line-height: 1.8;
        font-size: 0.95rem;
        color: #2d3748;
    }
    .response-container h1, .response-container h2, .response-container h3 {
        color: #667eea;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    .response-container strong {
        color: #4a5568;
        font-weight: 600;
    }
    .approval-box {
        padding: 2rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: 2rem 0;
    }
    .approval-decision {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 600;
        font-size: 1.1rem;
    }
    .approval-approved {
        background: #c6f6d5;
        color: #22543d;
        border-left: 4px solid #48bb78;
    }
    .approval-denied {
        background: #fed7d7;
        color: #742a2a;
        border-left: 4px solid #f56565;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'timeline' not in st.session_state:
    st.session_state.timeline = []
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'select'
if 'demo_type' not in st.session_state:
    st.session_state.demo_type = None
if 'plan_response' not in st.session_state:
    st.session_state.plan_response = None
if 'approval_data' not in st.session_state:
    st.session_state.approval_data = None
if 'approval_details' not in st.session_state:
    st.session_state.approval_details = None


def invoke_agent(prompt, config=None):
    """Invoke the AgentCore agent"""
    project_root = Path(__file__).parent.parent
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
                        # The result is already a proper string with \n for newlines
                        # json.loads() automatically unescapes it, so just return it
                        return result
            except json.JSONDecodeError:
                # If JSON parsing fails, try regex approach
                json_match = re.search(r'\{"result":\s*"(.*?)"\s*\}', response_part, re.DOTALL)
                if json_match:
                    result = json_match.group(1)
                    # Manually unescape the common escapes
                    result = result.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                    return result

        # If we couldn't parse it, return the original
        return output

    except Exception as e:
        # If anything goes wrong, return original output
        return output


def format_response_html(text):
    """Format response text for HTML display with proper line breaks and styling"""
    import html
    import re

    # Escape HTML special characters
    text = html.escape(text)

    # Strategy: Mark important line breaks we want to keep, then unwrap the rest

    # 1. Mark paragraph breaks (double newlines)
    text = re.sub(r'\n\n+', '<<<PARAGRAPH_BREAK>>>', text)

    # 2. Mark line breaks before numbered list items (e.g., "   1. ", "   2. ")
    text = re.sub(r'\n(\s+\d+\.\s)', '<<<LIST_BREAK>>>\n\\1', text)

    # 3. Mark line breaks before bullet points (• or -)
    text = re.sub(r'\n(\s*[•\-]\s)', '<<<BULLET_BREAK>>>\n\\1', text)

    # 4. Mark line breaks after section headers (lines ending with :)
    text = re.sub(r':\n', ':<<<HEADER_BREAK>>>\n', text)

    # 5. Now remove all remaining single newlines (these are hard wraps)
    text = text.replace('\n', ' ')

    # 6. Restore the marked line breaks
    text = text.replace('<<<PARAGRAPH_BREAK>>>', '\n\n')
    text = text.replace('<<<LIST_BREAK>>>', '\n')
    text = text.replace('<<<BULLET_BREAK>>>', '\n')
    text = text.replace('<<<HEADER_BREAK>>>', '\n')

    # Enhance formatting for common patterns
    # Make headers bold and larger (lines with ======)
    text = re.sub(r'={50,}', '<div style="border-top: 2px solid #667eea; margin: 1rem 0;"></div>', text)

    # Make section headers stand out (lines starting with **)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #667eea; font-size: 1.1em;">\1</strong>', text)

    # Format bullet points
    text = re.sub(r'•', '<span style="color: #667eea;">•</span>', text)
    text = re.sub(r'✅', '<span style="color: #48bb78;">✅</span>', text)
    text = re.sub(r'⚠️', '<span style="color: #f6ad55;">⚠️</span>', text)
    text = re.sub(r'❌', '<span style="color: #f56565;">❌</span>', text)
    text = re.sub(r'📋|📊|🔧|🛡️|🔍|🚀|💾', r'<span style="font-size: 1.2em;">\g<0></span>', text)

    # Convert newlines to <br> tags
    text = text.replace('\n\n', '<br><br>')
    text = text.replace('\n', '<br>')

    return text


def check_for_approval_needed(response):
    """Check if approval is needed"""
    normalized = response.replace('\n', '').replace('\r', '')
    # Check for both old and new formats
    # Simplify: if we have the approval state base64, we need approval
    has_old_format = "APPROVAL_STATE_B64:" in response and "END_APPROVAL_STATE" in response
    has_new_format = "<!-- APPROVAL_STATE_B64:" in response and "END_APPROVAL_STATE -->" in response
    return has_old_format or has_new_format


def extract_approval_state(response):
    """Extract approval state from response"""
    try:
        import base64
        import re

        # First try new HTML comment format (cleaner)
        comment_pattern = r'<!-- APPROVAL_STATE_B64:([A-Za-z0-9+/=]+):END_APPROVAL_STATE -->'
        comment_match = re.search(comment_pattern, response)
        if comment_match:
            b64_str = comment_match.group(1).strip()
            json_str = base64.b64decode(b64_str).decode()
            return json.loads(json_str)

        # Debug: show what we're trying to parse
        st.write(f"🔍 Looking for approval state in response (length: {len(response)})")

        # Show markers we're looking for
        has_start = "APPROVAL_STATE_B64:" in response
        has_end = "END_APPROVAL_STATE" in response
        st.write(f"   Start marker present: {has_start}")
        st.write(f"   End marker present: {has_end}")

        # Show a snippet around the markers
        if has_start:
            start_pos = response.find("APPROVAL_STATE_B64:")
            snippet = response[max(0, start_pos-50):start_pos+100]
            st.code(f"Start context: ...{snippet}...", language="text")

        # Look for the approval state pattern - be very flexible
        # The response format is: APPROVAL_STATE_B64:\n<base64>\nEND_APPROVAL_STATE
        # But the end marker might be missing, corrupted, or split (EN\nD_APPROVAL_STATE)
        pattern = r'APPROVAL_STATE_B64:\s*([A-Za-z0-9+/=\n]+?)(?:\s*(?:END_APPROVAL_STATE|ECD_APPROVAL_STATE|ND_APPROVAL_STATE|D_APPROVAL_STATE)|$)'
        match = re.search(pattern, response, re.DOTALL)

        if match:
            b64_str = match.group(1).strip().replace('\n', '').replace(' ', '')
            st.write(f"✅ Found base64 via regex (length: {len(b64_str)})")
            try:
                json_str = base64.b64decode(b64_str).decode()
                data = json.loads(json_str)
                st.write(f"✅ Successfully parsed approval state via regex")
                return data
            except Exception as e:
                st.error(f"Failed to decode base64 via regex: {e}")
                # Continue to fallback method

        # Fallback: Try to extract everything between markers more liberally
        start_marker = "APPROVAL_STATE_B64:"
        # The end marker might be split across lines: "EN\nD_APPROVAL_STATE" or "END_APPROVAL_\nSTATE"
        # So we need to normalize newlines first or use a more flexible search

        # Try to find just "END_APPROVAL_" which should be unique enough
        start_idx = response.find(start_marker)

        # Look for END_APPROVAL_ or D_APPROVAL_STATE (in case it's split as EN\nD_APPROVAL_STATE)
        end_approx_idx = response.find("END_APPROVAL_")
        if end_approx_idx == -1:
            # Try D_APPROVAL_STATE in case the split is EN\nD_APPROVAL_STATE
            end_approx_idx = response.find("D_APPROVAL_STATE")

        st.write(f"   Start marker at: {start_idx}")
        st.write(f"   END_APPROVAL_ or D_APPROVAL_STATE at: {end_approx_idx}")

        if start_idx != -1 and end_approx_idx != -1 and end_approx_idx > start_idx:
            # Extract base64 between the markers
            b64_str = response[start_idx + len(start_marker):end_approx_idx].strip()
            # Remove all whitespace and newlines from base64
            b64_str = ''.join(b64_str.split())

            st.write(f"✅ Found base64 using flexible end marker (length: {len(b64_str)})")
            try:
                json_str = base64.b64decode(b64_str).decode()
                data = json.loads(json_str)
                st.write(f"✅ Successfully parsed approval state!")
                return data
            except Exception as e:
                st.error(f"Failed to decode: {e}")

        # Legacy: Try exact markers as fallback
        for end_marker in ["END_APPROVAL_STATE", "\nEND_APPROVAL_STATE", "ECD_APPROVAL_STATE", "D_APPROVAL_STATE"]:
            start_idx = response.find(start_marker)
            end_idx = response.find(end_marker)

            st.write(f"   Trying exact marker '{repr(end_marker)}': start={start_idx}, end={end_idx}")

            if start_idx != -1 and end_idx != -1:
                b64_str = response[start_idx + len(start_marker):end_idx].strip()
                # Remove any whitespace/newlines
                b64_str = ''.join(b64_str.split())

                if b64_str:
                    st.write(f"✅ Found base64 using marker '{end_marker}' (length: {len(b64_str)})")
                    try:
                        json_str = base64.b64decode(b64_str).decode()
                        data = json.loads(json_str)
                        st.write(f"✅ Successfully parsed approval state with workflow_type: {data.get('workflow_type')}")
                        return data
                    except Exception as e:
                        st.error(f"Failed to decode with marker '{end_marker}': {e}")
                        continue
                else:
                    st.warning(f"Empty base64 string with marker '{end_marker}'")

        st.error("❌ Could not find approval state markers in response")
        # Show a sample of the response for debugging
        with st.expander("🐛 Response sample"):
            st.code(response[-1000:] if len(response) > 1000 else response)
        return None

    except Exception as e:
        st.error(f"Error extracting approval state: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None


def extract_approval_details(response):
    """Extract approval details for display"""
    import re
    details = {}

    bucket_match = re.search(r'Bucket:\s*([^\n]+)', response)
    if bucket_match:
        details['bucket_name'] = bucket_match.group(1).strip()

    risk_match = re.search(r'Risk_Score:\s*([\d.]+)', response)
    if risk_match:
        details['risk_score'] = float(risk_match.group(1))

    approval_data = extract_approval_state(response)
    if approval_data:
        workflow_type = approval_data.get("workflow_type", "")
        state = approval_data.get("state", {})

        # Infrastructure workflow
        if workflow_type == "infrastructure" and state.get("instance_id"):
            details['instance_id'] = state["instance_id"]

        # Security/AIOps workflow - extract from approval_request
        approval_request = state.get("approval_request", {})
        if approval_request:
            details['incident_type'] = approval_request.get('incident_type', 'unknown')
            details['severity'] = approval_request.get('severity', 'UNKNOWN')
            details['root_cause'] = approval_request.get('root_cause', 'unknown')
            details['network_device'] = approval_request.get('network_device', 'unknown')
            details['affected_services'] = approval_request.get('affected_services', [])
            details['proposed_remediation'] = approval_request.get('proposed_remediation', '')

    return details


def add_timeline_step(step_number, title, content, step_type="completed"):
    """Add a step to the timeline"""
    st.session_state.timeline.append({
        'number': step_number,
        'title': title,
        'content': content,
        'type': step_type,
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })


def display_timeline():
    """Display all timeline steps"""
    for step in st.session_state.timeline:
        st.markdown(f'<div class="timeline-step {step["type"]}">', unsafe_allow_html=True)
        st.markdown(
            f'<span class="step-number">{step["number"]}</span>'
            f'<span class="step-title">{step["title"]}</span>'
            f'<span style="float: right; color: #718096; font-size: 0.9rem;">{step["timestamp"]}</span>',
            unsafe_allow_html=True
        )
        st.markdown(step['content'], unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# Header
st.markdown('<div class="main-header">🏗️ Intelligent Operations Demos</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Features")
    st.markdown("""
    - 📋 **System Prompt-Based Planner**
    - ⏸️ **Human-in-the-Loop Approval**
    - 🤖 **Multi-Agent Workflow**
    - 🔒 **Security Compliance**
    """)

    st.divider()

    st.header("Workflow Progress")
    total_steps = len(st.session_state.timeline)
    if total_steps > 0:
        st.metric("Steps Completed", total_steps)
    else:
        st.info("No steps yet")

    st.divider()

    if st.button("🔄 Start New Demo", use_container_width=True):
        st.session_state.timeline = []
        st.session_state.current_step = 'select'
        st.session_state.demo_type = None
        st.session_state.plan_response = None
        st.session_state.approval_data = None
        st.session_state.approval_details = None
        st.rerun()


# Display existing timeline
display_timeline()

# Current step actions
if st.session_state.current_step == 'select':
    st.markdown("## Select Demo Type")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🏗️ Infrastructure Lifecycle", use_container_width=True, type="primary"):
            st.session_state.demo_type = 'infrastructure'
            st.session_state.prompt_text = "Create a plan for the infrastructure lifecycle demo"
            st.session_state.current_step = 'creating_plan'
            st.rerun()

    with col2:
        if st.button("🔒 Security Scan", use_container_width=True, type="primary"):
            st.session_state.demo_type = 'security'
            st.session_state.prompt_text = "Create a plan for scanning S3 buckets for security issues"
            st.session_state.current_step = 'creating_plan'
            st.rerun()

    with col3:
        if st.button("🌐 AIOps Network Correlation", use_container_width=True, type="primary"):
            st.session_state.demo_type = 'aiops'
            st.session_state.prompt_text = "Create a plan for the AIOps network correlation demo"
            st.session_state.current_step = 'creating_plan'
            st.rerun()

    st.divider()

    st.markdown("### Or enter a custom prompt:")
    custom_prompt = st.text_input(
        "Prompt",
        placeholder="provision an ec2 vm and an s3 bucket",
        label_visibility="collapsed"
    )

    if st.button("▶️ Run Custom Prompt", use_container_width=True):
        if custom_prompt:
            # Check if the prompt is AIOps-related
            aiops_keywords = ['network', 'root cause', 'correlation', 'aiops', 'network issue']
            prompt_lower = custom_prompt.lower()
            is_aiops = any(keyword in prompt_lower for keyword in aiops_keywords)

            if is_aiops:
                st.session_state.demo_type = 'aiops'
                st.session_state.prompt_text = f"Create a plan for: {custom_prompt}"
                st.session_state.custom_prompt = custom_prompt
            else:
                st.session_state.demo_type = 'custom'
                st.session_state.prompt_text = f"Create a plan for: {custom_prompt}"
                st.session_state.custom_prompt = custom_prompt

            st.session_state.current_step = 'creating_plan'
            st.rerun()
        else:
            st.warning("Please enter a prompt")

elif st.session_state.current_step == 'creating_plan':
    with st.spinner("⏳ Asking Intelligent Ops Agent to create a plan..."):
        output, error, returncode = invoke_agent(st.session_state.prompt_text)

        if returncode != 0:
            st.error(f"❌ Error creating plan: {error}")
        else:
            plan_response = parse_agent_response(output)
            st.session_state.plan_response = plan_response

            # Add to timeline
            content = f'<div class="response-container">{format_response_html(plan_response)}</div>'
            add_timeline_step(1, "📋 Execution Plan Created", content, "completed")

            st.session_state.current_step = 'approve_plan'
            st.rerun()

elif st.session_state.current_step == 'approve_plan':
    st.markdown('<div class="approval-box">', unsafe_allow_html=True)
    st.markdown("### 👤 Plan Approval Required")
    st.markdown("Review the execution plan above. Do you want to proceed with execution?")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("✅ Approve & Execute", use_container_width=True, type="primary"):
            # Add approval to timeline
            add_timeline_step(
                2,
                "✅ Plan Approved",
                '<div class="approval-decision approval-approved">User approved the execution plan</div>',
                "completed"
            )
            st.session_state.current_step = 'executing'
            st.rerun()

    with col2:
        if st.button("❌ Deny Plan", use_container_width=True):
            add_timeline_step(
                2,
                "❌ Plan Denied",
                '<div class="approval-decision approval-denied">User denied the execution plan</div>',
                "completed"
            )
            st.session_state.current_step = 'select'
            st.rerun()

elif st.session_state.current_step == 'executing':
    with st.spinner("⏳ Running workflow via AgentCore..."):
        # Determine execution prompt
        if st.session_state.demo_type == 'infrastructure':
            exec_prompt = "Run the infrastructure lifecycle demo"
        elif st.session_state.demo_type == 'security':
            exec_prompt = "security scan"
        elif st.session_state.demo_type == 'aiops':
            # If there's a custom prompt for AIOps, use it; otherwise use default
            exec_prompt = st.session_state.get('custom_prompt', "Run the AIOps demo")
        elif st.session_state.demo_type == 'aiops-setup':
            exec_prompt = "Deploy AIOps infrastructure for network event correlation"
        elif st.session_state.demo_type == 'aiops-cleanup':
            exec_prompt = "Cleanup AIOps demo infrastructure"
        else:
            exec_prompt = st.session_state.custom_prompt

        # Add debug info
        st.write(f"🔍 Executing prompt: `{exec_prompt}`")

        output, error, returncode = invoke_agent(exec_prompt)

        if returncode != 0:
            st.error(f"❌ Error: {error}")
            st.error(f"Output: {output}")
        else:
            response = parse_agent_response(output)

            # Show raw output for debugging
            with st.expander("🐛 Debug: Raw Agent Output"):
                st.code(output)

            # Show parsed response for debugging
            with st.expander("🐛 Debug: Parsed Response"):
                st.write(f"Length: {len(response)}")
                st.write(f"Has APPROVAL_STATE_B64: {'APPROVAL_STATE_B64:' in response}")
                st.write(f"Has END_APPROVAL_STATE: {'END_APPROVAL_STATE' in response}")
                st.write(f"Has ECD_APPROVAL_STATE: {'ECD_APPROVAL_STATE' in response}")

                # Show what's at the very end
                st.write(f"Last 200 characters (repr): {repr(response[-200:])}")

                # Show first and last 500 chars
                st.code(f"First 500 chars:\n{response[:500]}")
                st.code(f"Last 500 chars:\n{response[-500:]}")

            if check_for_approval_needed(response):
                # Extract approval data first
                approval_data = extract_approval_state(response)

                # Remove the HTML comment with base64 from display (ugly for demos)
                import re

                # First remove HTML comment format (new format)
                clean_response = re.sub(r'<!--\s*APPROVAL_STATE_B64:[^>]+-->', '', response, flags=re.DOTALL)

                # Also remove old format base64 if present (between markers on separate lines)
                clean_response = re.sub(r'APPROVAL_STATE_B64:\s*[A-Za-z0-9+/=\n\r]+\s*END_APPROVAL_STATE', '', clean_response, flags=re.DOTALL)

                # Extract just the execution progress section (everything before the approval prompt)
                if "⚠️  WORKFLOW PAUSED" in clean_response:
                    clean_response = clean_response.split("⚠️  WORKFLOW PAUSED")[0].strip()
                elif "WORKFLOW_PAUSED_FOR_APPROVAL" in clean_response:
                    clean_response = clean_response.split("WORKFLOW_PAUSED_FOR_APPROVAL")[0].strip()

                # If we got logs from execution, show them nicely formatted
                if not clean_response or len(clean_response) < 50:
                    # Extract execution logs from the approval state if available
                    if approval_data and "state" in approval_data and "logs" in approval_data["state"]:
                        execution_logs = approval_data["state"]["logs"]
                        # Format the logs nicely
                        log_html = "<div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;'>"
                        log_html += "<strong>📋 Execution Log:</strong><br/><br/>"
                        for log in execution_logs:
                            log_html += f"• {log}<br/>"
                        log_html += "</div>"
                        clean_response = log_html
                    else:
                        # If nothing before, show a nice message
                        clean_response = "🤖 AI Agent executed workflow and identified network issue requiring approval."

                # Add execution log to timeline
                add_timeline_step(
                    3,
                    "🤖 Workflow Execution",
                    f'<div class="response-container">{clean_response}</div>',
                    "completed"
                )
                if not approval_data:
                    st.error("❌ Error: Could not extract approval state - see debug output above")
                    st.stop()
                else:
                    st.session_state.approval_data = approval_data
                    st.session_state.approval_details = extract_approval_details(response)
                    st.session_state.current_step = 'approve_remediation'
                    st.rerun()
            else:
                # No approval needed, workflow complete
                add_timeline_step(
                    3,
                    "✅ Workflow Completed",
                    f'<div class="response-container">{format_response_html(response)}</div>',
                    "completed"
                )
                st.session_state.current_step = 'complete'
                st.rerun()

elif st.session_state.current_step == 'approve_remediation':
    details = st.session_state.approval_details

    st.markdown('<div class="approval-box">', unsafe_allow_html=True)
    st.markdown("### 🚨 Remediation Approval Request")

    # Network/AIOps incident
    if details.get('incident_type') == 'network_degradation':
        st.markdown("#### 🌐 Network Incident")
        st.markdown(f"- **Root Cause:** {details.get('root_cause', 'unknown')}")
        st.markdown(f"- **Network Device:** `{details.get('network_device', 'unknown')}`")
        st.markdown(f"- **Severity:** {details.get('severity', 'UNKNOWN')}")

        affected = details.get('affected_services', [])
        if affected:
            st.markdown(f"- **Affected Services:** {', '.join(affected)}")

        st.markdown(f"#### ⚠️ Risk Score: {int(details.get('risk_score', 0))}/100")

        st.markdown("#### 🔧 Proposed Remediation")
        if details.get('proposed_remediation'):
            st.markdown(f"- **Action:** {details.get('proposed_remediation')}")
        st.markdown("- **Method:** Terraform via CodePipeline")
        st.markdown("- **Steps:**")
        st.markdown("  - Switch traffic to backup network path")
        st.markdown("  - Adjust Quality of Service (QoS) policies")
        st.markdown("  - Enable network path monitoring")
        st.markdown("  - Increase bandwidth allocation")

    # Infrastructure workflow
    elif details.get('instance_id'):
        st.markdown("#### 📊 Infrastructure Context")
        st.markdown(f"- **EC2 Instance:** `{details.get('instance_id', 'N/A')}`")
        st.markdown(f"- **S3 Bucket:** `{details.get('bucket_name', 'unknown')}`")
        st.markdown(f"#### ⚠️ Risk Score: {int(details.get('risk_score', 0))}/100")

        st.markdown("#### 🔧 Proposed Remediation")
        st.markdown("""
        - **Action:** Block all public access
        - **Method:** AWS S3 Public Access Block
        - **Configuration:**
          - BlockPublicAcls: true
          - IgnorePublicAcls: true
          - BlockPublicPolicy: true
          - RestrictPublicBuckets: true
        """)

        st.markdown("#### 📋 Compliance Frameworks")
        st.markdown("""
        - CIS AWS Foundations: 2.1.5
        - NIST 800-53: AC-3
        - PCI DSS: 1.2.1
        - GDPR: Article 32
        """)

    # Security/S3 workflow
    else:
        st.markdown(f"#### 📦 Bucket: `{details.get('bucket_name', 'unknown')}`")
        st.markdown(f"#### ⚠️ Risk Score: {int(details.get('risk_score', 0))}/100")

        st.markdown("#### 🔧 Proposed Remediation")
        st.markdown("""
        - **Action:** Block all public access
        - **Method:** AWS S3 Public Access Block
        - **Configuration:**
          - BlockPublicAcls: true
          - IgnorePublicAcls: true
          - BlockPublicPolicy: true
          - RestrictPublicBuckets: true
        """)

        st.markdown("#### 📋 Compliance Frameworks")
        st.markdown("""
        - CIS AWS Foundations: 2.1.5
        - NIST 800-53: AC-3
        - PCI DSS: 1.2.1
        - GDPR: Article 32
        """)

    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("✅ Approve Remediation", use_container_width=True, type="primary"):
            add_timeline_step(
                4,
                "✅ Remediation Approved",
                '<div class="approval-decision approval-approved">User approved the remediation</div>',
                "completed"
            )
            st.session_state.remediation_approved = True
            st.session_state.current_step = 'remediating'
            st.rerun()

    with col2:
        if st.button("❌ Deny Remediation", use_container_width=True):
            add_timeline_step(
                4,
                "❌ Remediation Denied",
                '<div class="approval-decision approval-denied">User denied the remediation</div>',
                "completed"
            )
            st.session_state.remediation_approved = False
            st.session_state.current_step = 'remediating'
            st.rerun()

elif st.session_state.current_step == 'remediating':
    with st.spinner("⏳ Running remediation in AgentCore..."):
        approved = st.session_state.remediation_approved

        continuation_payload = {
            "prompt": "continue",
            "approval_continuation": {
                "state": st.session_state.approval_data["state"],
                "approved": approved,
                "workflow_type": st.session_state.approval_data["workflow_type"]
            }
        }

        project_root = Path(__file__).parent.parent
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

            # Add final result to timeline
            if approved:
                add_timeline_step(
                    5,
                    "✅ Remediation Applied",
                    f'<div class="response-container">{format_response_html(response)}</div>',
                    "completed"
                )
            else:
                add_timeline_step(
                    5,
                    "⏭️ Remediation Skipped",
                    f'<div class="response-container">{format_response_html(response)}</div>',
                    "completed"
                )

            st.session_state.current_step = 'complete'
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error continuing workflow: {e}")

elif st.session_state.current_step == 'complete':
    st.success("🎉 Demo workflow completed successfully!")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Run Another Demo", use_container_width=True, type="primary"):
            st.session_state.timeline = []
            st.session_state.current_step = 'select'
            st.session_state.demo_type = None
            st.session_state.plan_response = None
            st.session_state.approval_data = None
            st.session_state.approval_details = None
            st.rerun()


# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🏗️ Intelligent Ops Agent - Multi-Agent Infrastructure Automation</p>
    <p style="font-size: 0.9rem;">Powered by AWS Bedrock AgentCore & LangGraph</p>
</div>
""", unsafe_allow_html=True)
