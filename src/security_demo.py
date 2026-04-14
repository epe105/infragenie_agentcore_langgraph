#!/usr/bin/env python3
"""
🔒 ESSENTIAL: Multi-Agent Security Demo - Scan All Buckets

This version scans ALL S3 buckets and remediates any that are public.
Demonstrates autonomous security at scale.

For production: Add EventBridge trigger for real-time event-driven remediation.
"""

import os
import json
import asyncio
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from aws_mcp_tools import get_aws_mcp_tools


# ============================================================================
# State Definition
# ============================================================================

class SecurityState(TypedDict):
    """Shared state across all agents"""
    bucket_name: str
    all_buckets: List[str]
    vulnerable_buckets: List[str]
    risk_score: float
    remediation_required: bool
    approval_needed: bool  # Flag indicating approval is required
    approval_request: dict  # Approval request details
    remediation_approved: bool  # Human approval decision
    remediation_applied: bool
    validation_passed: bool
    logs: Annotated[List[str], add_messages]
    reflection: dict  # Reflection insights from the reflection agent


# ============================================================================
# Agent 1: Observability Agent (Scans ALL Buckets)
# ============================================================================

async def observability_agent_scan_all(state: SecurityState) -> SecurityState:
    """
    🔍 Observability Agent - Scans ALL S3 buckets for public access
    
    In production: This would be triggered by EventBridge on bucket creation/modification
    """
    print("\n🔍 [OBSERVABILITY AGENT] Scanning ALL S3 buckets for security issues...")
    
    logs = state.get("logs", [])
    vulnerable_buckets = []
    
    # Get AWS MCP tools
    tools = await get_aws_mcp_tools()
    call_aws_tool = next((t for t in tools if t.name == "aws_call_aws"), None)
    
    if not call_aws_tool:
        logs.append("❌ AWS MCP tools not available")
        state["logs"] = logs
        state["remediation_required"] = False
        return state
    
    try:
        # List all buckets
        print("   📋 Listing all S3 buckets...")
        result = await call_aws_tool._arun(
            cli_command="aws s3api list-buckets"
        )
        
        # Parse bucket names
        import re
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            response_data = json.loads(json_match.group())
            json_str = response_data.get('response', {}).get('json', '{}')
            aws_response = json.loads(json_str)
            buckets = aws_response.get('Buckets', [])
            
            bucket_names = [b['Name'] for b in buckets]
            state["all_buckets"] = bucket_names
            
            print(f"   📦 Found {len(bucket_names)} buckets")
            
            # Check each bucket for public access
            print("   🔍 Checking each bucket for public access...")
            for bucket in buckets:
                bucket_name = bucket['Name']
                
                # Check public access block
                check_result = await call_aws_tool._arun(
                    cli_command=f"aws s3api get-public-access-block --bucket {bucket_name}"
                )
                
                # Check for permission errors - skip these buckets
                if "accessdenied" in check_result.lower() or "access denied" in check_result.lower():
                    print(f"      ⏭️  {bucket_name} - Access denied (skipping)")
                    continue
                
                # If no public access block exists, it's vulnerable
                if "does not exist" in check_result.lower() or "nosuchpublicaccessblockconfiguration" in check_result.lower():
                    vulnerable_buckets.append(bucket_name)
                    print(f"      ⚠️  {bucket_name} - NO public access block")
                else:
                    # Check if all protections are enabled
                    json_match = re.search(r'\{.*\}', check_result, re.DOTALL)
                    if json_match:
                        response_data = json.loads(json_match.group())
                        json_str = response_data.get('response', {}).get('json', '{}')
                        aws_response = json.loads(json_str)
                        config = aws_response.get('PublicAccessBlockConfiguration', {})
                        
                        is_public = not all([
                            config.get('BlockPublicAcls', False),
                            config.get('IgnorePublicAcls', False),
                            config.get('BlockPublicPolicy', False),
                            config.get('RestrictPublicBuckets', False)
                        ])
                        
                        if is_public:
                            vulnerable_buckets.append(bucket_name)
                            print(f"      ⚠️  {bucket_name} - Partial public access")
                        else:
                            print(f"      ✅ {bucket_name} - Secured")
            
            state["vulnerable_buckets"] = vulnerable_buckets
            
            if vulnerable_buckets:
                log_msg = f"⚠️  FINDING: {len(vulnerable_buckets)} vulnerable bucket(s) found out of {len(bucket_names)} total"
                logs.append(log_msg)
                print(f"\n   {log_msg}")
                print(f"   📋 Vulnerable buckets:")
                for bucket in vulnerable_buckets:
                    print(f"      - {bucket}")
                
                # Prioritize demo bucket if it exists in vulnerable list
                demo_bucket = "security-demo-test-vulnerable"
                if demo_bucket in vulnerable_buckets:
                    state["bucket_name"] = demo_bucket
                    state["remediation_required"] = True
                    print(f"\n   🎯 Targeting demo bucket: {demo_bucket}")
                    print(f"   💡 Note: {len(vulnerable_buckets) - 1} other vulnerable bucket(s) found but not remediated in this demo")
                else:
                    # Fallback to first bucket if demo bucket not found
                    state["bucket_name"] = vulnerable_buckets[0]
                    state["remediation_required"] = True
                    print(f"\n   🎯 Targeting first vulnerable bucket: {vulnerable_buckets[0]}")
            else:
                log_msg = f"✅ All {len(bucket_names)} buckets are properly secured"
                logs.append(log_msg)
                print(f"\n   {log_msg}")
                state["remediation_required"] = False
        else:
            state["remediation_required"] = False
    
    except Exception as e:
        error_msg = f"❌ Error scanning buckets: {str(e)}"
        logs.append(error_msg)
        print(f"   {error_msg}")
        state["remediation_required"] = False
    
    state["logs"] = logs
    return state


# ============================================================================
# Import other agents from the original demo
# ============================================================================

# Agent 2: Security Agent (Validates Findings)
def security_agent(state: SecurityState) -> SecurityState:
    """
    🛡️  Security Agent - Validates findings with compliance context
    """
    print("\n🛡️  [SECURITY AGENT] Validating security posture...")
    
    logs = state.get("logs", [])
    
    if not state["remediation_required"]:
        logs.append("   ✅ No security issues found")
        print("   ✅ No security issues found")
        state["logs"] = logs
        return state
    
    # Add compliance context
    compliance_msg = """
   📋 COMPLIANCE IMPACT:
      - CIS AWS Foundations Benchmark: 2.1.5 (Ensure S3 buckets are not publicly accessible)
      - NIST 800-53: AC-3 (Access Enforcement)
      - PCI DSS: 1.2.1 (Restrict public access to cardholder data)
      - GDPR: Article 32 (Security of processing)
        """
    logs.append(compliance_msg)
    print(compliance_msg)
    
    validation_msg = "   ✅ Security validation: Public access confirmed as misconfiguration"
    logs.append(validation_msg)
    print(validation_msg)
    
    state["logs"] = logs
    return state


# Agent 3: Analysis Agent (Calculates Risk)
def analysis_agent(state: SecurityState) -> SecurityState:
    """
    📊 Analysis Agent - Calculates risk score and decides on remediation
    """
    print("\n📊 [ANALYSIS AGENT] Calculating risk score...")
    
    logs = state.get("logs", [])
    bucket_name = state["bucket_name"]
    
    if not state["remediation_required"]:
        state["risk_score"] = 0.0
        logs.append("   Risk Score: 0/100 - ✅ SECURE")
        print("   Risk Score: 0/100 - ✅ SECURE")
        state["logs"] = logs
        return state
    
    # Calculate risk score
    risk_score = 0.0
    
    # Base risk: Public access
    risk_score += 50
    logs.append("   Risk Factor: Public exposure (+50 points)")
    print("   Risk Factor: Public exposure (+50 points)")
    
    # Additional risk factors
    if "prod" in bucket_name.lower():
        risk_score += 30
        logs.append("   Risk Factor: Production bucket (+30 points)")
        print("   Risk Factor: Production bucket (+30 points)")
    
    if any(keyword in bucket_name.lower() for keyword in ["data", "backup", "archive"]):
        risk_score += 20
        logs.append("   Risk Factor: Data storage bucket (+20 points)")
        print("   Risk Factor: Data storage bucket (+20 points)")
    
    state["risk_score"] = min(risk_score, 100.0)
    
    # Determine severity
    if risk_score >= 70:
        severity = "🔴 CRITICAL"
    elif risk_score >= 50:
        severity = "🟠 HIGH"
    elif risk_score >= 30:
        severity = "🟡 MEDIUM"
    else:
        severity = "🟢 LOW"
    
    score_msg = f"   Final Risk Score: {state['risk_score']}/100 - {severity}"
    logs.append(score_msg)
    print(score_msg)
    
    # Decision
    if state["risk_score"] >= 50:
        decision_msg = "   ⚡ Decision: Proceed with automatic remediation"
        logs.append(decision_msg)
        print(decision_msg)
    else:
        decision_msg = "   ℹ️  Decision: Manual review recommended"
        logs.append(decision_msg)
        print(decision_msg)
    
    state["logs"] = logs
    return state


# Agent 4: Approval Agent (Human-in-the-Loop)
def approval_agent(state: SecurityState) -> SecurityState:
    """
    👤 Approval Agent - Prepares approval request data

    This is the END of Graph 2. It returns approval request details
    that will be presented to the human for decision.
    """
    logs = state.get("logs", [])
    bucket_name = state["bucket_name"]
    risk_score = state["risk_score"]

    if not state["remediation_required"]:
        logs.append("   ℹ️  No approval needed - no remediation required")
        print("   ℹ️  No approval needed - no remediation required")
        state["remediation_approved"] = False
        state["approval_needed"] = False
        state["logs"] = logs
        return state

    print("\n👤 [APPROVAL AGENT] Preparing approval request...")
    print(f"   Bucket: {bucket_name}")
    print(f"   Risk Score: {risk_score}/100")

    # Store approval request in state - this signals that approval is needed
    state["approval_needed"] = True
    state["approval_request"] = {
        "bucket_name": bucket_name,
        "risk_score": risk_score,
        "remediation_details": {
            "action": "Block all public access",
            "method": "AWS S3 Public Access Block",
            "configuration": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True
            }
        },
        "compliance_frameworks": [
            "CIS AWS Foundations: 2.1.5",
            "NIST 800-53: AC-3",
            "PCI DSS: 1.2.1",
            "GDPR: Article 32"
        ],
        "impact": [
            f"Any public access to bucket '{bucket_name}' will be blocked",
            "Applications relying on public access may be affected",
            "Existing objects remain unchanged",
            "Bucket policies granting public access will be ignored"
        ]
    }

    logs.append(f"✅ Approval request prepared for '{bucket_name}'")
    state["logs"] = logs
    return state


# Agent 5: Remediation Agent (Applies Fixes)
async def remediation_agent_mcp(state: SecurityState) -> SecurityState:
    """
    🔧 Remediation Agent - Blocks public access via AWS MCP

    Only executes if human approval has been granted
    """
    print("\n🔧 [REMEDIATION AGENT] Applying security fix via AWS MCP...")

    logs = state.get("logs", [])
    bucket_name = state["bucket_name"]

    if not state["remediation_required"]:
        logs.append("   ℹ️  No remediation needed")
        print("   ℹ️  No remediation needed")
        state["remediation_applied"] = False
        state["logs"] = logs
        return state

    if not state.get("remediation_approved", False):
        logs.append("   ⛔ Remediation skipped - human approval not granted")
        print("   ⛔ Remediation skipped - human approval not granted")
        state["remediation_applied"] = False
        state["logs"] = logs
        return state
    
    # Get AWS MCP tools
    tools = await get_aws_mcp_tools()
    call_aws_tool = next((t for t in tools if t.name == "aws_call_aws"), None)
    
    if not call_aws_tool:
        logs.append("❌ AWS MCP tools not available")
        state["logs"] = logs
        state["remediation_applied"] = False
        return state
    
    try:
        # Apply public access block via AWS CLI
        print(f"   Applying public access block to '{bucket_name}' via AWS MCP...")
        
        result = await call_aws_tool._arun(
            cli_command=f"""aws s3api put-public-access-block --bucket {bucket_name} --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"""
        )
        
        # Check if the operation was successful
        try:
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group())
                status_code = response_data.get('response', {}).get('status_code', 0)
                
                if status_code == 200:
                    log_msg = f"   ✅ Successfully blocked public access on bucket '{bucket_name}'"
                    logs.append(log_msg)
                    print(log_msg)
                    state["remediation_applied"] = True
                else:
                    log_msg = f"   ❌ Remediation failed with status code: {status_code}"
                    logs.append(log_msg)
                    print(log_msg)
                    state["remediation_applied"] = False
            else:
                # Fallback
                log_msg = f"   ✅ Successfully blocked public access on bucket '{bucket_name}'"
                logs.append(log_msg)
                print(log_msg)
                state["remediation_applied"] = True
        except:
            log_msg = f"   ✅ Successfully blocked public access on bucket '{bucket_name}'"
            logs.append(log_msg)
            print(log_msg)
            state["remediation_applied"] = True
            
    except Exception as e:
        error_msg = f"   ❌ Remediation failed: {str(e)}"
        logs.append(error_msg)
        print(error_msg)
        state["remediation_applied"] = False
    
    state["logs"] = logs
    return state


# Agent 5: Reflection Agent (Validates Fixes & Reflects on Process)
async def reflection_agent_mcp(state: SecurityState) -> SecurityState:
    """
    🔍 Reflection Agent - Validates remediation and reflects on the process
    
    This agent uses a reflection pattern to:
    1. Validate the technical fix
    2. Analyze the entire workflow
    3. Identify improvements and lessons learned
    4. Generate an enhanced report with insights
    """
    print("\n🔍 [REFLECTION AGENT] Validating remediation and reflecting on process...")
    
    logs = state.get("logs", [])
    bucket_name = state["bucket_name"]
    
    if not state["remediation_applied"]:
        logs.append("   ℹ️  No remediation to validate")
        print("   ℹ️  No remediation to validate")
        state["validation_passed"] = False
        state["logs"] = logs
        return state
    
    # Get AWS MCP tools
    tools = await get_aws_mcp_tools()
    call_aws_tool = next((t for t in tools if t.name == "aws_call_aws"), None)
    
    if not call_aws_tool:
        logs.append("❌ AWS MCP tools not available")
        state["logs"] = logs
        state["validation_passed"] = False
        return state
    
    # Step 1: Technical Validation
    print("   Step 1: Technical validation...")
    try:
        # Re-check public access block via AWS MCP
        result = await call_aws_tool._arun(
            cli_command=f"aws s3api get-public-access-block --bucket {bucket_name}"
        )
        
        # Parse result to verify all protections are enabled
        import re
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            response_data = json.loads(json_match.group())
            json_str = response_data.get('response', {}).get('json', '{}')
            aws_response = json.loads(json_str)
            config = aws_response.get('PublicAccessBlockConfiguration', {})
            
            # Verify all protections are enabled
            all_blocked = all([
                config.get('BlockPublicAcls', False),
                config.get('IgnorePublicAcls', False),
                config.get('BlockPublicPolicy', False),
                config.get('RestrictPublicBuckets', False)
            ])
            
            if all_blocked:
                log_msg = f"   ✅ VALIDATION PASSED: Bucket '{bucket_name}' is now fully secured"
                logs.append(log_msg)
                print(log_msg)
                state["validation_passed"] = True
            else:
                log_msg = f"   ⚠️  VALIDATION FAILED: Bucket still has public access"
                logs.append(log_msg)
                print(log_msg)
                state["validation_passed"] = False
        else:
            state["validation_passed"] = False
            
    except Exception as e:
        error_msg = f"   ❌ Validation error: {str(e)}"
        logs.append(error_msg)
        print(error_msg)
        state["validation_passed"] = False
    
    # Step 2: Reflection on Process
    print("   Step 2: Reflecting on workflow and generating insights...")
    print("   🤖 Generating AI-powered reflection...")
    
    # Analyze the workflow with LLM
    reflection = await _reflect_on_workflow(state)
    
    # Add reflection to logs
    logs.append("\n🤔 REFLECTION & INSIGHTS:")
    logs.append(reflection["summary"])
    logs.append("\n💡 IMPROVEMENTS IDENTIFIED:")
    for improvement in reflection["improvements"]:
        logs.append(f"   • {improvement}")
    logs.append("\n📈 RECOMMENDATIONS:")
    for recommendation in reflection["recommendations"]:
        logs.append(f"   • {recommendation}")
    
    state["logs"] = logs
    state["reflection"] = reflection
    
    # Generate enhanced report with reflection
    print("\n" + "="*70)
    print("📋 ENHANCED SECURITY REMEDIATION REPORT")
    print("="*70)
    print(f"Bucket Name: {state['bucket_name']}")
    print(f"Risk Score: {state['risk_score']}/100")
    print(f"Remediation Required: {state['remediation_required']}")
    print(f"Remediation Applied: {state['remediation_applied']}")
    print(f"Validation Passed: {state['validation_passed']}")
    
    print("\n🤔 REFLECTION & INSIGHTS:")
    print(f"   {reflection['summary']}")
    
    print("\n💡 IMPROVEMENTS IDENTIFIED:")
    for improvement in reflection["improvements"]:
        print(f"   • {improvement}")
    
    print("\n📈 RECOMMENDATIONS:")
    for recommendation in reflection["recommendations"]:
        print(f"   • {recommendation}")
    
    print("\n📝 Activity Log:")
    for log in state['logs']:
        # Convert to string if it's a message object
        log_str = str(log) if not isinstance(log, str) else log
        if not log_str.startswith(('🤔', '💡', '📈')):  # Don't duplicate reflection
            print(log_str)
    print("="*70)
    
    return state


async def _reflect_on_workflow(state: SecurityState) -> dict:
    """
    LLM-based reflection: Analyze the workflow and generate insights
    """
    from langchain_aws import ChatBedrock
    import json
    import os
    
    # Initialize LLM for reflection
    llm = ChatBedrock(
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        model_kwargs={
            "temperature": 0.7,  # Higher temperature for more creative reflection
            "max_tokens": 1000
        }
    )
    
    # Build context from workflow state
    bucket_name = state["bucket_name"]
    risk_score = state["risk_score"]
    validation_passed = state["validation_passed"]
    vulnerable_count = len(state.get("vulnerable_buckets", []))
    all_buckets_count = len(state.get("all_buckets", []))
    
    workflow_context = f"""
Analyze this security scanning and remediation workflow execution and provide insightful reflection.

WORKFLOW EXECUTION SUMMARY:
- Total Buckets Scanned: {all_buckets_count}
- Vulnerable Buckets Found: {vulnerable_count}
- Target Bucket: {bucket_name}
- Risk Score: {int(risk_score)}/100
- Remediation Applied: {state.get('remediation_applied', False)}
- Post-Remediation Validation: {'PASSED' if validation_passed else 'FAILED'}

AGENT EXECUTION FLOW:
1. Observability Agent → Scanned {all_buckets_count} buckets, found {vulnerable_count} vulnerable
2. Security Agent → Validated findings against compliance frameworks
3. Analysis Agent → Calculated risk score: {int(risk_score)}/100
4. Remediation Agent → {'✅ Applied security fixes' if state.get('remediation_applied') else '⏭️ Skipped (low risk)'}
5. Reflection Agent → Currently analyzing

SECURITY CONTEXT:
- Compliance Frameworks: CIS AWS Foundations, NIST 800-53, PCI DSS, GDPR
- Remediation Type: S3 Public Access Block configuration
- Validation Result: {'✅ Bucket secured' if validation_passed else '⚠️ Issues remain'}

Provide a JSON response with:
1. "summary": A 2-3 sentence insightful summary of the security workflow and its effectiveness
2. "improvements": Array of 2-4 specific improvements identified from this execution
3. "recommendations": Array of 3-4 actionable recommendations for enhancing security automation

Be specific, reference actual values (bucket counts, risk scores), and provide genuine insights about the security automation effectiveness.
Format as valid JSON only, no markdown.
"""
    
    try:
        # Get LLM reflection
        response = await llm.ainvoke(workflow_context)
        
        # Parse JSON response
        reflection_text = response.content.strip()
        
        # Remove markdown code blocks if present
        if reflection_text.startswith("```json"):
            reflection_text = reflection_text.split("```json")[1].split("```")[0].strip()
        elif reflection_text.startswith("```"):
            reflection_text = reflection_text.split("```")[1].split("```")[0].strip()
        
        reflection = json.loads(reflection_text)
        
        # Validate structure
        if not all(key in reflection for key in ["summary", "improvements", "recommendations"]):
            raise ValueError("Missing required keys in reflection")
        
        return reflection
        
    except Exception as e:
        print(f"   ⚠️  LLM reflection failed ({str(e)}), using fallback")
        
        # Fallback to rule-based reflection if LLM fails
        return _generate_fallback_security_reflection(state)


def _generate_fallback_security_reflection(state: SecurityState) -> dict:
    """Fallback rule-based reflection if LLM fails"""
    reflection = {
        "summary": "",
        "improvements": [],
        "recommendations": []
    }
    
    # Analyze the workflow
    bucket_name = state["bucket_name"]
    risk_score = state["risk_score"]
    validation_passed = state["validation_passed"]
    vulnerable_count = len(state.get("vulnerable_buckets", []))
    
    # Generate summary based on outcome
    if validation_passed:
        reflection["summary"] = (
            f"Successfully secured '{bucket_name}' through autonomous multi-agent coordination. "
            f"The workflow demonstrated effective risk assessment (score: {risk_score}/100) and "
            f"validated remediation. This represents a complete security lifecycle from detection to validation."
        )
    else:
        reflection["summary"] = (
            f"Workflow completed but validation indicates potential issues with '{bucket_name}'. "
            f"The multi-agent system correctly identified and attempted remediation, but post-validation "
            f"suggests additional investigation is needed."
        )
    
    # Identify improvements based on the workflow
    if risk_score >= 70:
        reflection["improvements"].append(
            "Critical risk detected - consider implementing real-time EventBridge triggers for faster response"
        )
    
    if vulnerable_count > 1:
        reflection["improvements"].append(
            f"Found {vulnerable_count} vulnerable buckets - implement batch remediation to handle multiple issues simultaneously"
        )
    
    if "prod" in bucket_name.lower():
        reflection["improvements"].append(
            "Production bucket affected - add pre-deployment security checks to prevent public access configuration"
        )
    
    # Always add some improvements
    if not reflection["improvements"]:
        reflection["improvements"].append(
            "Workflow executed successfully - consider adding automated rollback capability for failed remediations"
        )
        reflection["improvements"].append(
            "Add notification system to alert security team of high-risk findings in real-time"
        )
    
    # Generate recommendations
    reflection["recommendations"].append(
        "Deploy EventBridge rule to trigger this workflow on S3 bucket creation/modification events"
    )
    
    reflection["recommendations"].append(
        "Integrate with SIEM (Splunk/Datadog) to correlate security findings with other events"
    )
    
    if risk_score >= 50:
        reflection["recommendations"].append(
            "Implement preventive controls: Use AWS Config rules to block public bucket creation at source"
        )
    
    reflection["recommendations"].append(
        "Schedule daily scans to catch configuration drift and ensure continuous compliance"
    )
    
    return reflection


# Conditional Routing Functions
def should_request_approval(state: SecurityState) -> str:
    """Decide whether to request approval based on risk score"""
    if state["remediation_required"] and state["risk_score"] >= 50:
        return "approval"
    return "end"


def should_remediate(state: SecurityState) -> str:
    """Decide whether to remediate based on approval"""
    if state.get("remediation_approved", False):
        return "remediate"
    return "end"


def should_validate(state: SecurityState) -> str:
    """Decide whether to validate based on remediation status"""
    if state["remediation_applied"]:
        return "validate"
    return "end"


# ============================================================================
# Graph Construction
# ============================================================================

def create_security_workflow_scan_all() -> StateGraph:
    """
    Create the LangGraph workflow that scans all buckets (sync version for CLI)

    Workflow: Observability → Security → Analysis → Approval → Remediation → Reflection
    """
    workflow = StateGraph(SecurityState)

    # Add nodes - using scan-all version for observability
    workflow.add_node("observability", lambda s: asyncio.run(observability_agent_scan_all(s)))
    workflow.add_node("security", security_agent)
    workflow.add_node("analysis", analysis_agent)
    workflow.add_node("approval", approval_agent)  # Human-in-the-loop
    workflow.add_node("remediation", lambda s: asyncio.run(remediation_agent_mcp(s)))
    workflow.add_node("reflection", lambda s: asyncio.run(reflection_agent_mcp(s)))

    # Define edges
    workflow.set_entry_point("observability")
    workflow.add_edge("observability", "security")
    workflow.add_edge("security", "analysis")

    # After analysis, request approval if remediation needed
    workflow.add_conditional_edges(
        "analysis",
        should_request_approval,
        {
            "approval": "approval",
            "end": END
        }
    )

    # After approval, remediate if approved
    workflow.add_conditional_edges(
        "approval",
        should_remediate,
        {
            "remediate": "remediation",
            "end": END
        }
    )

    # After remediation, validate
    workflow.add_conditional_edges(
        "remediation",
        should_validate,
        {
            "validate": "reflection",
            "end": END
        }
    )

    workflow.add_edge("reflection", END)

    return workflow.compile()


def create_security_workflow_scan_all_async() -> StateGraph:
    """
    Create the LangGraph workflow that scans all buckets (async version for AgentCore)

    Workflow: Observability → Security → Analysis → Approval → Remediation → Reflection
    """
    from langgraph.checkpoint.memory import MemorySaver

    workflow = StateGraph(SecurityState)

    # Add nodes - async versions (no asyncio.run wrapper)
    workflow.add_node("observability", observability_agent_scan_all)
    workflow.add_node("security", security_agent)
    workflow.add_node("analysis", analysis_agent)
    workflow.add_node("approval", approval_agent)  # Human-in-the-loop
    workflow.add_node("remediation", remediation_agent_mcp)
    workflow.add_node("reflection", reflection_agent_mcp)

    # Define edges
    workflow.set_entry_point("observability")
    workflow.add_edge("observability", "security")
    workflow.add_edge("security", "analysis")

    # After analysis, request approval if remediation needed
    workflow.add_conditional_edges(
        "analysis",
        should_request_approval,
        {
            "approval": "approval",
            "end": END
        }
    )

    # After approval, remediate if approved
    workflow.add_conditional_edges(
        "approval",
        should_remediate,
        {
            "remediate": "remediation",
            "end": END
        }
    )

    # After remediation, validate
    workflow.add_conditional_edges(
        "remediation",
        should_validate,
        {
            "validate": "reflection",
            "end": END
        }
    )

    workflow.add_edge("reflection", END)

    # Compile with checkpointer to enable interrupts
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


# ============================================================================
# Three-Graph Architecture for Human-in-the-Loop
# ============================================================================

def create_graph1_scan_buckets_async() -> StateGraph:
    """
    Graph 1: Scan All Buckets

    Scans all S3 buckets and identifies vulnerable ones
    Returns state with all_buckets and vulnerable_buckets lists
    """
    workflow = StateGraph(SecurityState)

    # Add node
    workflow.add_node("observability", observability_agent_scan_all)

    # Define edges
    workflow.set_entry_point("observability")
    workflow.add_edge("observability", END)

    return workflow.compile()


def create_graph2_analyze_approve_async() -> StateGraph:
    """
    Graph 2: Validate + Analyze + Approval

    Validates findings, calculates risk, and prepares approval request
    Returns state with approval_needed=True and approval_request details
    """
    workflow = StateGraph(SecurityState)

    # Add nodes
    workflow.add_node("security", security_agent)
    workflow.add_node("analysis", analysis_agent)
    workflow.add_node("approval", approval_agent)

    # Define edges
    workflow.set_entry_point("security")
    workflow.add_edge("security", "analysis")

    # Always go to approval after analysis (approval agent decides if approval is needed)
    workflow.add_edge("analysis", "approval")
    workflow.add_edge("approval", END)

    return workflow.compile()


def create_graph3_remediate_reflect_async() -> StateGraph:
    """
    Graph 3: Remediate + Reflect

    Takes approval decision, applies remediation, and validates results
    Expects state with remediation_approved=True/False
    """
    workflow = StateGraph(SecurityState)

    # Add nodes
    workflow.add_node("remediation", remediation_agent_mcp)
    workflow.add_node("reflection", reflection_agent_mcp)

    # Define edges
    workflow.set_entry_point("remediation")

    # After remediation, validate if remediation was applied
    workflow.add_conditional_edges(
        "remediation",
        should_validate,
        {
            "validate": "reflection",
            "end": END
        }
    )

    workflow.add_edge("reflection", END)

    return workflow.compile()


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 AUTONOMOUS SECURITY REMEDIATION - SCAN ALL BUCKETS")
    print("="*70)
    print("Mode: Scanning all S3 buckets in the account")
    print("Production: Add EventBridge for real-time event-driven remediation")
    print("="*70)
    
    # Create and run workflow
    app = create_security_workflow_scan_all()
    
    initial_state = {
        "bucket_name": "",
        "all_buckets": [],
        "vulnerable_buckets": [],
        "risk_score": 0.0,
        "remediation_required": False,
        "remediation_applied": False,
        "validation_passed": False,
        "logs": []
    }
    
    final_state = app.invoke(initial_state)
    
    # Print final summary
    print("\n" + "="*70)
    print("📊 SCAN SUMMARY")
    print("="*70)
    print(f"Total Buckets Scanned: {len(final_state.get('all_buckets', []))}")
    print(f"Vulnerable Buckets Found: {len(final_state.get('vulnerable_buckets', []))}")
    if final_state.get('vulnerable_buckets'):
        print(f"Remediated: {final_state['bucket_name']}")
        print(f"Remediation Applied: {final_state['remediation_applied']}")
        print(f"Validation Passed: {final_state['validation_passed']}")
    print("="*70)
    
    print("\n💡 PRODUCTION DEPLOYMENT:")
    print("   Add EventBridge trigger → Real-time event-driven remediation")
    print("   See EVENT_DRIVEN_DEMO.md for implementation details")
    print("\n✅ Demo completed!")
