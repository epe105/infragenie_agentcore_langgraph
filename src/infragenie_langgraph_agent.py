"""
InfraGenie AgentCore Implementation using LangGraph

AgentCore-compatible version that uses AWS Bedrock models instead of external APIs.
This provides the same functionality as the Strands version but with LangGraph workflows.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_aws import ChatBedrock
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict, Annotated
from system_prompt import INFRAGENIE_SYSTEM_PROMPT
from planner_agent import PlannerAgent
# Lazy import MCP tools to avoid initialization timeout
# from mcp_tools import get_mcp_tools, mcp_manager
# from aws_mcp_tools import get_aws_mcp_tools, aws_mcp_manager

# AWS Account Configuration
TARGET_AWS_ACCOUNT = os.getenv('TARGET_AWS_ACCOUNT', 'YOUR_TARGET_ACCOUNT_ID')
AGENT_AWS_ACCOUNT = os.getenv('AGENT_AWS_ACCOUNT', 'YOUR_AGENT_ACCOUNT_ID')

# Configure LangSmith tracing
def _get_langsmith_config():
    """Get LangSmith configuration from environment or SSM Parameter Store"""
    api_key = os.getenv("LANGSMITH_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT")

    # If not in environment, try to get from SSM Parameter Store
    if not api_key or not project:
        try:
            import boto3
            ssm = boto3.client('ssm', region_name=os.getenv("AWS_REGION", "us-east-1"))

            if not api_key:
                try:
                    response = ssm.get_parameter(Name="/infragenie/langsmith/api_key", WithDecryption=True)
                    api_key = response['Parameter']['Value']
                except Exception:
                    pass

            if not project:
                try:
                    response = ssm.get_parameter(Name="/infragenie/langsmith/project")
                    project = response['Parameter']['Value']
                except Exception:
                    pass
        except Exception as e:
            print(f"Warning: Could not fetch LangSmith config from SSM: {e}")

    return api_key, project

# Apply LangSmith configuration
langsmith_api_key, langsmith_project = _get_langsmith_config()
if langsmith_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
    if langsmith_project:
        os.environ["LANGCHAIN_PROJECT"] = langsmith_project
        print(f"LangSmith tracing enabled for project: {langsmith_project}")
    else:
        print("LangSmith tracing enabled (no project specified)")


class AgentState(TypedDict):
    """State for the InfraGenie agent"""
    messages: Annotated[List[Any], add_messages]
    tools_available: bool


class InfraGenieAgentCore:
    """InfraGenie agent implementation for AWS AgentCore using LangGraph"""
    
    def __init__(self):
        self.llm = self._initialize_bedrock_llm()
        self.tools: List[BaseTool] = []
        self.graph = None
        self.initialized = False
        self.planner = PlannerAgent(self.llm)
    
    def _initialize_bedrock_llm(self):
        """Initialize AWS Bedrock LLM"""
        # Use Claude Sonnet 4.5 via cross-region inference profile
        return ChatBedrock(
            model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            model_kwargs={
                "temperature": 0.1,
                "max_tokens": 8000
            }
        )
    
    async def initialize(self):
        """Initialize the agent with MCP tools and build the graph"""
        if self.initialized:
            return

        try:
            # Lazy import MCP tools
            from mcp_tools import get_mcp_tools
            from aws_mcp_tools import get_aws_mcp_tools

            # Load Ansible MCP tools
            ansible_tools = await get_mcp_tools()
            print(f"Loaded {len(ansible_tools)} Ansible MCP tools")

            # Load AWS MCP tools
            aws_tools = await get_aws_mcp_tools()
            print(f"Loaded {len(aws_tools)} AWS MCP tools")
            
            # Combine all tools
            self.tools = ansible_tools + aws_tools
            print(f"Total tools available: {len(self.tools)}")
            
            # Bind tools to LLM
            if self.tools:
                self.llm_with_tools = self.llm.bind_tools(self.tools)
            else:
                self.llm_with_tools = self.llm
            
            # Build the graph
            self._build_graph()
            self.initialized = True
            
        except Exception as e:
            print(f"Warning: Failed to initialize MCP tools: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to agent without tools
            self.tools = []
            self.llm_with_tools = self.llm
            self._build_graph()
            self.initialized = True
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        if self.tools:
            workflow.add_node("tools", ToolNode(self.tools))
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        if self.tools:
            workflow.add_conditional_edges(
                "agent",
                self._should_continue,
                {
                    "continue": "tools",
                    "end": END,
                }
            )
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge("agent", END)
        
        # Compile the graph
        self.graph = workflow.compile()
    
    def _agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Agent node that processes messages and decides on actions"""
        messages = state["messages"]
        
        # Add system message if not present
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            messages = [SystemMessage(content=INFRAGENIE_SYSTEM_PROMPT)] + messages
        
        # Get response from LLM
        response = self.llm_with_tools.invoke(messages)
        
        return {
            "messages": [response],
            "tools_available": len(self.tools) > 0
        }
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if we should continue to tools or end"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the last message has tool calls, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        else:
            return "end"
    
    async def continue_with_approval(self, state: Dict[str, Any], approved: bool, workflow_type: str) -> str:
        """Continue workflow from Graph 3 after receiving approval decision"""
        # Update state with approval decision
        state["remediation_approved"] = approved

        if workflow_type == "infrastructure":
            from infrastructure_lifecycle_demo import create_graph3_remediate_reflect_async

            print(f"\n📍 Graph 3: {'Applying' if approved else 'Skipping'} remediation...")
            graph3 = create_graph3_remediate_reflect_async()
            final_state = await graph3.ainvoke(state)

            return self._format_infrastructure_lifecycle_response(final_state)

        elif workflow_type == "security":
            from security_demo import create_graph3_remediate_reflect_async

            print(f"\n📍 Graph 3: {'Applying' if approved else 'Skipping'} remediation...")
            graph3 = create_graph3_remediate_reflect_async()
            final_state = await graph3.ainvoke(state)

            return self._format_security_response(final_state)

        elif workflow_type == "aiops":
            from aiops_demo import (
                remediation_agent,
                verification_agent,
                reflection_agent
            )

            print(f"\n📍 AIOps Continuation: {'Applying' if approved else 'Skipping'} network remediation...")

            # Run remediation (simulated)
            state = await remediation_agent(state)

            # Run verification (simulated)
            state = await verification_agent(state)

            # Generate reflection
            state = await reflection_agent(state)

            return self._format_aiops_response(state)

        return f"Unknown workflow type: {workflow_type}"

    async def process_message(self, message: str, config: dict = None) -> str:
        """Process a user message and return the agent's response"""

        # Check AIOps requests FIRST (before planner and initialization)
        # These should bypass the planner completely
        if self._is_aiops_setup_request(message):
            return await self._run_aiops_setup(message, config)

        if self._is_aiops_cleanup_request(message):
            return await self._run_aiops_cleanup(message, config)

        if self._is_aiops_demo_request(message):
            print("🎯 Detected AIOps demo request - bypassing planner, running demo directly")
            if not self.initialized:
                await self.initialize()
            return await self._run_aiops_demo(message, config)

        # Check if this is a planner request (after AIOps checks)
        # Planner only needs LLM, not MCP tools
        if self._is_planner_request(message):
            return await self.create_infrastructure_plan(message)

        # For all other requests, ensure initialization
        if not self.initialized:
            await self.initialize()

        try:
            # Lazy import and refresh tokens if needed
            from mcp_tools import mcp_manager
            from aws_mcp_tools import aws_mcp_manager
            await mcp_manager.refresh_token_if_needed()
            await aws_mcp_manager.refresh_token_if_needed()

            # Check if this is an infrastructure lifecycle request
            if self._is_infrastructure_lifecycle_request(message):
                return await self._run_infrastructure_lifecycle(message, config)

            # Check if this is a security scan request
            if self._is_security_scan_request(message):
                return await self._run_security_scan(message, config)

            # Check if this is an Ansible VM provisioning request
            if self._is_ansible_vm_request(message):
                return await self._run_ansible_vm_provisioning(message)

            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=message)],
                "tools_available": len(self.tools) > 0
            }

            # Run the graph
            result = await self.graph.ainvoke(initial_state)

            # Extract the final message
            final_messages = result["messages"]
            if final_messages:
                last_message = final_messages[-1]
                if isinstance(last_message, AIMessage):
                    return last_message.content
                else:
                    return str(last_message)
            else:
                return "I apologize, but I couldn't process your request."

        except Exception as e:
            return f"I encountered an error while processing your request: {str(e)}"
    
    def _is_infrastructure_lifecycle_request(self, message: str) -> bool:
        """Detect if the message is requesting the full infrastructure lifecycle demo"""
        message_lower = message.lower()
        lifecycle_keywords = [
            "infrastructure lifecycle",
            "full lifecycle",
            "complete lifecycle",
            "provision and secure",
            "provision ec2 and s3",
            "provision vm and bucket",
            "provision an ec2",
            "provision a vm",
            "create ec2 and s3",
            "create vm and s3",
            "create an ec2",
            "create a vm",
            "infrastructure demo",
            "full stack demo",
            "end to end infrastructure",
            "provision configure backup"
        ]
        # Check if message contains both compute (ec2/vm) and storage (s3/bucket) keywords
        has_compute = any(word in message_lower for word in ["ec2", "vm", "instance"])
        has_storage = any(word in message_lower for word in ["s3", "bucket", "storage"])
        has_provision = any(word in message_lower for word in ["provision", "create", "deploy", "setup"])

        # Match if contains provision + compute + storage, or matches a specific keyword
        if has_provision and has_compute and has_storage:
            return True

        return any(keyword in message_lower for keyword in lifecycle_keywords)
    
    def _is_security_scan_request(self, message: str) -> bool:
        """Detect if the message is requesting a security scan"""
        message_lower = message.lower()
        security_keywords = [
            "security scan",
            "scan for security",
            "check security",
            "security audit",
            "scan buckets",
            "check buckets",
            "public buckets",
            "vulnerable buckets",
            "security remediation"
        ]
        return any(keyword in message_lower for keyword in security_keywords)

    def _is_aiops_setup_request(self, message: str) -> bool:
        """Detect if the message is requesting AIOps infrastructure setup"""
        message_lower = message.lower()
        setup_keywords = [
            "deploy aiops infrastructure",
            "setup aiops infrastructure",
            "create aiops infrastructure",
            "aiops infrastructure setup",
            "deploy aiops",
            "setup aiops"
        ]
        return any(keyword in message_lower for keyword in setup_keywords)

    def _is_aiops_cleanup_request(self, message: str) -> bool:
        """Detect if the message is requesting AIOps infrastructure cleanup"""
        message_lower = message.lower()
        cleanup_keywords = [
            "cleanup aiops",
            "delete aiops",
            "remove aiops",
            "destroy aiops",
            "cleanup aiops infrastructure",
            "delete aiops infrastructure"
        ]
        return any(keyword in message_lower for keyword in cleanup_keywords)

    def _is_aiops_demo_request(self, message: str) -> bool:
        """Detect if the message is requesting the AIOps demo execution (not setup/cleanup or planning)"""
        message_lower = message.lower()

        print(f"🔍 Checking if AIOps demo request: '{message_lower[:50]}...'")

        # Exclude planning requests - these should go to the planner
        if any(word in message_lower for word in ["create a plan", "create plan", "make a plan", "plan for"]):
            print("   ❌ Excluded: planning keyword found - routing to planner")
            return False

        # Exclude setup and cleanup requests
        if any(word in message_lower for word in ["setup", "deploy infrastructure", "cleanup", "destroy", "delete", "create infrastructure"]):
            print("   ❌ Excluded: setup/cleanup keyword found")
            return False

        # More flexible matching - check for aiops + action words
        has_aiops = "aiops" in message_lower
        has_action = any(word in message_lower for word in [
            "run", "execute", "demo", "start", "show",
            "correlation", "network", "event", "inject"
        ])

        # If has both aiops and action word, it's a demo request
        if has_aiops and has_action:
            print(f"   ✅ Matched: has_aiops={has_aiops}, has_action={has_action}")
            return True

        # Check for root cause analysis + network (common AIOps request pattern)
        has_root_cause = "root cause" in message_lower
        has_network = "network" in message_lower
        if has_root_cause and has_network:
            print(f"   ✅ Matched: root cause + network analysis request")
            return True

        # Also catch specific phrases
        aiops_keywords = [
            "run the aiops demo",
            "run aiops demo",
            "execute aiops demo",
            "aiops network correlation",
            "run network correlation",
            "inject events and correlate",
            "event correlation demo",
            "aiops demo",
            "root cause analysis of my current network issues",
            "perform a root cause analysis",
            "analyze network issues"
        ]
        matched = any(keyword in message_lower for keyword in aiops_keywords)
        if matched:
            print(f"   ✅ Matched keyword")
        else:
            print(f"   ❌ No match")
        return matched

    def _is_ansible_vm_request(self, message: str) -> bool:
        """Detect if the message is requesting Ansible VM provisioning"""
        message_lower = message.lower()
        ansible_keywords = [
            "create vm",
            "provision vm",
            "create ec2",
            "provision ec2",
            "launch vm",
            "launch ec2",
            "deploy vm",
            "deploy ec2",
            "create instance",
            "provision instance",
            "ansible vm",
            "ansible ec2"
        ]
        return any(keyword in message_lower for keyword in ansible_keywords)

    def _is_planner_request(self, message: str) -> bool:
        """Detect if the message is requesting plan creation"""
        message_lower = message.lower()
        planner_keywords = [
            "create a plan",
            "make a plan",
            "plan for",
            "show me a plan",
            "what's the plan",
            "planning",
            "create plan"
        ]
        return any(keyword in message_lower for keyword in planner_keywords)

    async def create_infrastructure_plan(self, message: str) -> str:
        """
        Create an infrastructure plan using the planner agent (system prompt-based tool)

        This demonstrates the "deep agent pattern" where the planner tool is defined
        entirely in the system prompt, with no code implementation needed.
        """
        # Use the planner to create a plan
        plan = await self.planner.create_plan(message)

        if not plan:
            return "I couldn't create a plan for that request. Could you provide more details about what infrastructure you'd like to provision?"

        # Validate the plan
        if not self.planner.validate_plan(plan):
            return "I created a plan but it appears incomplete. Please try rephrasing your request."

        # Get a human-readable explanation
        explanation = await self.planner.explain_plan(plan)

        # Format the response
        lines = []
        lines.append("=" * 70)
        lines.append("📋 INFRASTRUCTURE PLAN")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"**Task:** {plan.get('task_summary', 'N/A')}")
        lines.append("")
        lines.append("**Explanation:**")
        lines.append(explanation)
        lines.append("")
        lines.append("**Execution Steps:**")
        for step in plan.get('steps', []):
            lines.append(f"   {step['step_number']}. [{step['agent'].upper()}] {step['action']}")
            lines.append(f"      Tool: {step['tool']} | Duration: {step.get('estimated_duration', 'Unknown')}")
        lines.append("")
        lines.append(f"**Risk Assessment:** {plan.get('risk_assessment', {}).get('level', 'Unknown').upper()}")
        lines.append(f"**Estimated Time:** {plan.get('estimated_total_time', 'Unknown')}")
        lines.append(f"**Approval Required:** {'Yes' if plan.get('approval_required') else 'No'}")
        lines.append("")

        resources = plan.get('resources_created', [])
        if resources:
            lines.append("**Resources to Create:**")
            for resource in resources:
                lines.append(f"   • {resource}")
            lines.append("")

        cleanup = plan.get('cleanup_steps', [])
        if cleanup:
            lines.append("**Cleanup Steps:**")
            for step in cleanup:
                lines.append(f"   • {step}")
            lines.append("")

        lines.append("=" * 70)
        lines.append("")
        lines.append("💡 To execute this plan, say: 'Execute the infrastructure lifecycle'")
        lines.append("")

        return "\n".join(lines)
    
    async def _run_infrastructure_lifecycle(self, message: str, config: dict = None) -> str:
        """Run the full infrastructure lifecycle workflow using three-graph architecture"""
        from infrastructure_lifecycle_demo import (
            create_graph1_provision_storage_async,
            create_graph2_analyze_approve_async,
            create_graph3_remediate_reflect_async
        )

        print("\n🏗️  Initiating Infrastructure Lifecycle Demo...")

        # Initial state
        state = {
            "instance_id": "",
            "instance_ip": "",
            "instance_name": "",
            "bucket_name": "",
            "bucket_is_public": False,
            "bucket_secured": False,
            "security_findings": [],
            "compliance_violations": [],
            "risk_score": 0.0,
            "ec2_provisioned": False,
            "s3_created": False,
            "security_issue_found": False,
            "findings_validated": False,
            "risk_calculated": False,
            "approval_needed": False,
            "approval_request": {},
            "remediation_approved": False,
            "security_remediated": False,
            "validation_passed": False,
            "logs": [],
            "reflection": {}
        }

        # Graph 1: Provision + Storage
        print("📍 Graph 1: Provisioning infrastructure...")
        graph1 = create_graph1_provision_storage_async()
        state = await graph1.ainvoke(state)

        # Graph 2: Observe + Analyze + Approval
        print("📍 Graph 2: Analyzing security...")
        graph2 = create_graph2_analyze_approve_async()
        state = await graph2.ainvoke(state)

        # Check if approval is needed
        if state.get("approval_needed"):
            # Return state with approval request - workflow will be interrupted here
            # The interactive script will prompt the user and call graph 3
            return self._format_approval_request(state)

        # If no approval needed, go straight to reflection
        print("📍 Graph 3: Completing workflow...")
        graph3 = create_graph3_remediate_reflect_async()
        state = await graph3.ainvoke(state)

        # Format the response
        response = self._format_infrastructure_lifecycle_response(state)
        return response
    
    async def _run_security_scan(self, message: str, config: dict = None) -> str:
        """Run the multi-agent security scan workflow using three-graph architecture"""
        from security_demo import (
            create_graph1_scan_buckets_async,
            create_graph2_analyze_approve_async,
            create_graph3_remediate_reflect_async
        )

        print("\n🔒 Initiating Multi-Agent Security Scan...")

        # Initial state
        state = {
            "bucket_name": "",
            "all_buckets": [],
            "vulnerable_buckets": [],
            "risk_score": 0.0,
            "remediation_required": False,
            "approval_needed": False,
            "approval_request": {},
            "remediation_approved": False,
            "remediation_applied": False,
            "validation_passed": False,
            "logs": []
        }

        # Graph 1: Scan all buckets
        print("📍 Graph 1: Scanning S3 buckets...")
        graph1 = create_graph1_scan_buckets_async()
        state = await graph1.ainvoke(state)

        # Check if any vulnerabilities were found
        if not state.get("vulnerable_buckets"):
            return self._format_security_response(state)

        # Select first vulnerable bucket for remediation
        state["bucket_name"] = state["vulnerable_buckets"][0]
        state["remediation_required"] = True

        # Graph 2: Validate + Analyze + Approval
        print("📍 Graph 2: Analyzing security...")
        graph2 = create_graph2_analyze_approve_async()
        state = await graph2.ainvoke(state)

        # Check if approval is needed
        if state.get("approval_needed"):
            # Return state with approval request - workflow will be interrupted here
            return self._format_approval_request(state)

        # If no approval needed, go straight to reflection
        print("📍 Graph 3: Completing workflow...")
        graph3 = create_graph3_remediate_reflect_async()
        state = await graph3.ainvoke(state)

        # Format the response
        response = self._format_security_response(state)
        return response

    async def _run_aiops_demo(self, message: str, config: dict = None) -> str:
        """Run the FAST AIOps demo - no infrastructure deployment (infrastructure must be pre-deployed)"""
        from aiops_demo import (
            event_injection_agent,
            root_cause_analysis_agent,
            approval_gate_agent,
            remediation_agent,
            verification_agent,
            reflection_agent
        )

        print("\n🤖 Running AIOps Network Correlation Demo (FAST - no infrastructure deployment)...")

        # Initial state - infrastructure already deployed
        state = {
            "injected_events": [],
            "apm_events": [],
            "network_events": [],
            "infra_events": [],
            "root_cause_event": {},
            "root_cause_layer": "",
            "root_cause_source": "",
            "correlated_events": [],
            "remediation_required": False,
            "infrastructure_deployed": True,  # Assume already deployed
            "events_injected": False,
            "events_analyzed": False,
            "approval_needed": False,
            "approval_request": {},
            "remediation_approved": False,
            "remediation_triggered": False,
            "remediation_verified": False,
            "risk_score": 0.0,
            "incident_severity": "",
            "affected_services": [],
            "logs": [],
            "reflection": {}
        }

        # Step 1: Inject simulated events (FAST)
        print("📍 Step 1: Injecting simulated events...")
        state = await event_injection_agent(state)

        # Step 2: AI analyzes and correlates events (FAST)
        print("📍 Step 2: AI correlation analysis...")
        state = await root_cause_analysis_agent(state)

        # Step 3: Prepare approval gate (FAST)
        print("📍 Step 3: Preparing remediation approval...")
        state = await approval_gate_agent(state)

        # Check if approval is needed
        if state.get("approval_needed"):
            # Return state with approval request
            return self._format_approval_request(state)

        # If no approval needed (auto-approve), execute remediation
        state["remediation_approved"] = True

        # Step 4: Execute remediation (FAST - simulated)
        print("📍 Step 4: Executing remediation...")
        state = await remediation_agent(state)

        # Step 5: Verify resolution (FAST)
        print("📍 Step 5: Verifying resolution...")
        state = await verification_agent(state)

        # Step 6: Generate insights (FAST)
        print("📍 Step 6: Generating insights...")
        state = await reflection_agent(state)

        # Format the response
        response = self._format_aiops_response(state)
        return response

    async def _run_aiops_setup(self, message: str, config: dict = None) -> str:
        """AIOps Network Demo Setup - NO infrastructure needed (pure simulation)"""

        print("\n🔧 AIOps Network Correlation Demo - Setup...")

        # Format response
        lines = []
        lines.append("=" * 70)
        lines.append("🔧 AIOPS NETWORK CORRELATION - DEMO READY")
        lines.append("=" * 70)
        lines.append("")
        lines.append("✅ No Setup Required!")
        lines.append("")
        lines.append("💡 This demo uses PURE SIMULATION:")
        lines.append("   • No AWS resources created")
        lines.append("   • No infrastructure deployed")
        lines.append("   • Events are simulated (network packet loss, latency, errors)")
        lines.append("   • AI correlation logic is demonstrated")
        lines.append("   • Network remediation is shown conceptually")
        lines.append("")
        lines.append("🎯 Demo Focus:")
        lines.append("   • Network packet loss (L3)")
        lines.append("   • Network latency issues")
        lines.append("   • Network interface errors (L2)")
        lines.append("   • Application impact (L7)")
        lines.append("")
        lines.append("✅ Ready to demonstrate!")
        lines.append("   Click 'Run Demo' to see AI correlate network events")
        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    async def _run_aiops_cleanup(self, message: str, config: dict = None) -> str:
        """AIOps Network Demo Cleanup - Nothing to cleanup (pure simulation)"""

        print("\n🗑️  AIOps Network Demo Cleanup...")

        lines = []
        lines.append("=" * 70)
        lines.append("🗑️  AIOPS NETWORK CORRELATION - CLEANUP")
        lines.append("=" * 70)
        lines.append("")
        lines.append("✅ Nothing to Cleanup!")
        lines.append("")
        lines.append("💡 This demo uses pure simulation:")
        lines.append("   • No AWS resources were created")
        lines.append("   • No infrastructure was deployed")
        lines.append("   • All events were simulated in memory")
        lines.append("   • Network remediation was conceptual")
        lines.append("")
        lines.append("🎯 Demo Benefits:")
        lines.append("   • Zero cost - no resources deployed")
        lines.append("   • Instant execution - no setup time")
        lines.append("   • Focus on AI correlation logic")
        lines.append("   • Shows network troubleshooting process")
        lines.append("")
        lines.append("✅ Demo complete - no cleanup needed!")
        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    async def _run_ansible_vm_provisioning(self, message: str) -> str:
        """Run Ansible VM provisioning via MCP"""
        print("\n🚀 Initiating Ansible VM Provisioning...")

        try:
            # Lazy import and get Ansible MCP tools
            from mcp_tools import get_mcp_tools
            ansible_tools = await get_mcp_tools()
            
            # Find the run_playbook tool
            run_playbook_tool = next((t for t in ansible_tools if "run_playbook" in t.name.lower()), None)
            
            if not run_playbook_tool:
                return "❌ Error: Ansible MCP run_playbook tool not available. Please check MCP server connection."
            
            # Extract parameters from message (simple parsing)
            vm_name = self._extract_vm_name(message)
            instance_type = self._extract_instance_type(message)
            aws_region = self._extract_region(message)
            
            print(f"   VM Name: {vm_name}")
            print(f"   Instance Type: {instance_type}")
            print(f"   Region: {aws_region}")
            
            # Run the playbook via Ansible MCP
            print("\n   📋 Executing create-aws-vm.yaml playbook...")
            
            result = await run_playbook_tool._arun(
                playbook_path="../ansible_demo/create-aws-vm.yaml",
                extra_vars={
                    "vm_name": vm_name,
                    "instance_type": instance_type,
                    "aws_region": aws_region,
                    "key_name": "InfraGenie",
                    "admin_username": "ec2-user",
                    "owner": "infragenie-demo"
                }
            )
            
            # Format the response
            response = self._format_ansible_response(result, vm_name, instance_type, aws_region)
            return response
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error provisioning VM via Ansible: {str(e)}"
    
    def _extract_vm_name(self, message: str) -> str:
        """Extract VM name from message or use default"""
        # Simple extraction - look for "name" or "called"
        import re
        match = re.search(r'(?:name|called)\s+["\']?(\w+[-\w]*)["\']?', message, re.IGNORECASE)
        if match:
            return match.group(1)
        return "infragenie-vm"
    
    def _extract_instance_type(self, message: str) -> str:
        """Extract instance type from message or use default"""
        import re
        # Look for t2.micro, t3.small, etc.
        match = re.search(r'(t[23]\.\w+|m[45]\.\w+)', message, re.IGNORECASE)
        if match:
            return match.group(1)
        return "t3.micro"
    
    def _extract_region(self, message: str) -> str:
        """Extract AWS region from message or use default"""
        import re
        # Look for us-east-1, us-west-2, etc.
        match = re.search(r'(us|eu|ap|sa|ca|me|af)-(east|west|south|north|central|northeast|southeast)-\d', message, re.IGNORECASE)
        if match:
            return match.group(0)
        return "us-east-1"
    
    def _format_ansible_response(self, result: str, vm_name: str, instance_type: str, region: str) -> str:
        """Format the Ansible playbook execution result"""
        lines = []
        lines.append("=" * 70)
        lines.append("🚀 ANSIBLE VM PROVISIONING COMPLETE")
        lines.append("=" * 70)
        lines.append("")
        lines.append("📋 CONFIGURATION:")
        lines.append(f"   • VM Name: {vm_name}")
        lines.append(f"   • Instance Type: {instance_type}")
        lines.append(f"   • Region: {region}")
        lines.append(f"   • SSH Key: InfraGenie")
        lines.append(f"   • Owner: infragenie-demo")
        lines.append("")
        
        # Try to extract public IP from result
        import re
        ip_match = re.search(r'public IP is (\d+\.\d+\.\d+\.\d+)', result)
        instance_id_match = re.search(r'Instance ID: (i-[a-f0-9]+)', result)
        
        if ip_match:
            public_ip = ip_match.group(1)
            lines.append("✅ VM CREATED SUCCESSFULLY:")
            lines.append(f"   • Public IP: {public_ip}")
            if instance_id_match:
                lines.append(f"   • Instance ID: {instance_id_match.group(1)}")
            lines.append(f"   • SSH Command: ssh -i ~/.ssh/InfraGenie.pem ec2-user@{public_ip}")
        else:
            lines.append("✅ PLAYBOOK EXECUTED:")
            lines.append("   Check Ansible output for details")
        
        lines.append("")
        lines.append("🔧 ANSIBLE AUTOMATION:")
        lines.append("   • Playbook: create-aws-vm.yaml")
        lines.append("   • Security Group: ansible-demo-ssh (reused)")
        lines.append("   • Network: Default VPC")
        lines.append("   • Tags: ManagedBy=ansible, Owner=infragenie-demo")
        lines.append("")
        lines.append("🗑️  TO DELETE:")
        lines.append("   Run: ansible-playbook delete-aws-vm.yaml")
        lines.append("   Or ask: 'Delete all Ansible-managed VMs'")
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def _format_infrastructure_lifecycle_response(self, state: Dict[str, Any]) -> str:
        """Format the infrastructure lifecycle results into a readable response"""
        lines = []
        lines.append("=" * 70)
        lines.append("🏗️  INFRASTRUCTURE LIFECYCLE DEMO")
        lines.append("=" * 70)
        lines.append("")
        
        # Add execution logs to show agent progress
        logs = state.get('logs', [])
        if logs:
            lines.append("📋 EXECUTION LOG:")
            lines.append("")
            for log in logs:
                lines.append(f"   {log}")
            lines.append("")
            lines.append("=" * 70)
            lines.append("")
        
        lines.append("📊 INFRASTRUCTURE SUMMARY:")
        lines.append(f"   • EC2 Instance: {state.get('instance_id', 'N/A')}")
        lines.append(f"   • Public IP: {state.get('instance_ip', 'N/A')}")
        lines.append(f"   • S3 Bucket: {state.get('bucket_name', 'N/A')}")
        lines.append(f"   • Security Status: {'✅ Secured' if state['bucket_secured'] else '❌ Not Secured'}")
        lines.append(f"   • Overall Status: {'✅ SUCCESS' if state['validation_passed'] else '⚠️  INCOMPLETE'}")
        lines.append("")
        
        # Workflow steps
        lines.append("🤖 MULTI-AGENT WORKFLOW:")
        lines.append("   1. 🔍 Observability Agent → Provisioned EC2 instance")
        lines.append("   2. 🛡️  Security Agent → Created S3 bucket")
        lines.append("   3. 📊 Analysis Agent → Scanned for security issues")
        if state.get('security_remediated'):
            lines.append("   4. 🔧 Remediation Agent → Applied security fixes")
            lines.append("   5. 🔍 Reflection Agent → Validated remediation & reflected on process")
        lines.append("")
        
        # Reflection insights
        reflection = state.get('reflection', {})
        if reflection:
            lines.append("🤔 REFLECTION & INSIGHTS:")
            lines.append(f"   {reflection.get('summary', '')}")
            
            achievements = reflection.get('achievements', [])
            if achievements:
                lines.append("")
                lines.append("💡 KEY ACHIEVEMENTS:")
                for achievement in achievements:
                    lines.append(f"   • {achievement}")
            
            recommendations = reflection.get('recommendations', [])
            if recommendations:
                lines.append("")
                lines.append("📈 RECOMMENDATIONS:")
                for recommendation in recommendations[:3]:  # Show top 3
                    lines.append(f"   • {recommendation}")
        
        # Cleanup instructions
        lines.append("")
        lines.append("🗑️  CLEANUP INSTRUCTIONS:")
        lines.append("   • Delete EC2: ansible-playbook ansible_demo/delete-aws-vm.yaml")
        lines.append(f"   • Delete S3: aws s3 rb s3://{state.get('bucket_name', 'BUCKET')} --force")
        lines.append("")
        
        # Demo value
        lines.append("🎯 DEMO VALUE:")
        lines.append("   • Multi-tool orchestration: Ansible MCP + AWS MCP")
        lines.append("   • Complete infrastructure story: Provision → Secure → Configure")
        lines.append("   • Autonomous workflow: No manual intervention")
        lines.append("   • Production-ready: Add EventBridge for real-time automation")
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def _format_approval_request(self, state: Dict[str, Any]) -> str:
        """Format approval request for human review"""
        import base64
        import json

        approval_req = state.get("approval_request", {})

        # Detect workflow type based on state keys
        if "instance_id" in state:
            workflow_type = "infrastructure"
        elif "incident_type" in approval_req and approval_req.get("incident_type") == "network_degradation":
            workflow_type = "aiops"
        elif "root_cause_layer" in state:
            workflow_type = "aiops"
        else:
            workflow_type = "security"

        lines = []

        # Display workflow execution logs first (show what happened before approval)
        logs = state.get("logs", [])
        if logs:
            lines.append("="*70)
            lines.append("📊 WORKFLOW EXECUTION PROGRESS")
            lines.append("="*70)
            lines.append("")
            for log in logs:
                log_str = log.content if hasattr(log, 'content') else str(log)
                lines.append(log_str)
            lines.append("")

        lines.append("="*70)
        lines.append("⚠️  WORKFLOW PAUSED - APPROVAL REQUIRED")
        lines.append("="*70)
        lines.append("")

        # Display workflow-specific details
        if workflow_type == "aiops":
            # AIOps Network Incident Details
            lines.append("🔴 NETWORK INCIDENT DETECTED")
            lines.append("")
            lines.append("📊 INCIDENT DETAILS:")
            lines.append(f"   • Type: {approval_req.get('incident_type', 'unknown')}")
            lines.append(f"   • Severity: {approval_req.get('severity', 'UNKNOWN')}")
            lines.append(f"   • Risk Score: {approval_req.get('risk_score', 0)}/100")
            lines.append("")
            lines.append("🎯 ROOT CAUSE ANALYSIS:")
            lines.append(f"   • Layer: {approval_req.get('osi_layer', 'unknown')}")
            lines.append(f"   • Source: {approval_req.get('source', 'unknown')}")
            lines.append(f"   • Root Cause: {approval_req.get('root_cause', 'unknown')}")
            lines.append(f"   • Network Device: {approval_req.get('network_device', 'unknown')}")
            lines.append(f"   • Metric Value: {approval_req.get('metric_value', 'unknown')}")
            lines.append("")

            affected_services = approval_req.get('affected_services', [])
            if affected_services:
                lines.append("🚨 AFFECTED SERVICES:")
                for service in affected_services:
                    lines.append(f"   • {service}")
                lines.append("")

            lines.append("🔧 PROPOSED REMEDIATION:")
            lines.append(f"   • Action: {approval_req.get('proposed_remediation', 'unknown')}")
            lines.append(f"   • Method: {approval_req.get('remediation_method', 'unknown')}")
            lines.append("")

            remediation_steps = approval_req.get('remediation_steps', [])
            if remediation_steps:
                lines.append("📋 REMEDIATION STEPS:")
                for i, step in enumerate(remediation_steps, 1):
                    lines.append(f"   {i}. {step}")
                lines.append("")

        elif workflow_type == "infrastructure":
            # Infrastructure Lifecycle Details
            lines.append("🏗️  INFRASTRUCTURE REMEDIATION")
            lines.append("")
            lines.append("📊 RESOURCE DETAILS:")
            lines.append(f"   • S3 Bucket: {approval_req.get('bucket_name', 'unknown')}")
            lines.append(f"   • EC2 Instance: {approval_req.get('instance_id', 'unknown')}")
            lines.append(f"   • Risk Score: {approval_req.get('risk_score', 0)}/100")
            lines.append("")

            remediation = approval_req.get('remediation_details', {})
            if remediation:
                lines.append("🔧 PROPOSED REMEDIATION:")
                lines.append(f"   • Action: {remediation.get('action', 'unknown')}")
                lines.append(f"   • Method: {remediation.get('method', 'unknown')}")
                lines.append("")

            compliance = approval_req.get('compliance_frameworks', [])
            if compliance:
                lines.append("📋 COMPLIANCE FRAMEWORKS:")
                for framework in compliance:
                    lines.append(f"   • {framework}")
                lines.append("")

        else:
            # Security Scan Details
            lines.append("🔒 SECURITY REMEDIATION")
            lines.append("")
            lines.append("📊 BUCKET DETAILS:")
            lines.append(f"   • Bucket Name: {approval_req.get('bucket_name', state.get('bucket_name', 'unknown'))}")
            lines.append(f"   • Risk Score: {approval_req.get('risk_score', state.get('risk_score', 0))}/100")
            lines.append("")

            remediation = approval_req.get('remediation_details', {})
            if remediation:
                lines.append("🔧 PROPOSED REMEDIATION:")
                lines.append(f"   • Action: {remediation.get('action', 'unknown')}")
                lines.append(f"   • Method: {remediation.get('method', 'unknown')}")
                lines.append("")

        lines.append("="*70)
        lines.append("⏸️  Workflow paused. Approve or deny the proposed remediation.")
        lines.append("="*70)

        # Clean the state for serialization
        clean_state = {}
        for key, value in state.items():
            if key == "logs":
                clean_logs = []
                for log in value:
                    if hasattr(log, 'content'):
                        clean_logs.append(log.content)
                    else:
                        clean_logs.append(str(log))
                clean_state[key] = clean_logs
            elif key == "reflection" and not value:
                clean_state[key] = {}
            else:
                clean_state[key] = value

        # Encode state as base64 for UI components in a compact hidden format
        state_json = json.dumps({
            "state": clean_state,
            "workflow_type": workflow_type
        })
        state_b64 = base64.b64encode(state_json.encode()).decode()

        # Hide the base64 in HTML comment for cleaner demos
        lines.append("")
        lines.append("<!-- APPROVAL_STATE_B64:" + state_b64 + ":END_APPROVAL_STATE -->")

        return "\n".join(lines)

    def _format_security_response(self, state: Dict[str, Any]) -> str:
        """Format the security scan results into a readable response"""
        # Summary
        total_buckets = len(state.get('all_buckets', []))
        vulnerable_count = len(state.get('vulnerable_buckets', []))
        
        lines = []
        lines.append("=" * 70)
        lines.append("🔒 MULTI-AGENT SECURITY SCAN COMPLETE")
        lines.append("=" * 70)
        lines.append("")
        lines.append("📊 SCAN SUMMARY:")
        lines.append(f"   • Total Buckets Scanned: {total_buckets}")
        lines.append(f"   • Vulnerable Buckets Found: {vulnerable_count}")
        
        if vulnerable_count > 0:
            lines.append("")
            lines.append("⚠️  VULNERABLE BUCKETS:")
            for bucket in state.get('vulnerable_buckets', []):
                lines.append(f"   • {bucket}")
            
            # Remediation details
            if state.get('remediation_applied'):
                lines.append("")
                lines.append("✅ REMEDIATION APPLIED:")
                lines.append(f"   • Target Bucket: {state['bucket_name']}")
                lines.append(f"   • Risk Score: {state['risk_score']}/100")
                lines.append(f"   • Status: {'✅ Validated' if state['validation_passed'] else '⚠️  Validation Pending'}")
                
                if vulnerable_count > 1:
                    lines.append("")
                    lines.append(f"💡 NOTE: {vulnerable_count - 1} other vulnerable bucket(s) found")
                    lines.append("   Run again to remediate additional buckets")
            else:
                lines.append("")
                lines.append("⚠️  No remediation applied (risk score below threshold)")
        else:
            lines.append("")
            lines.append("✅ All buckets are properly secured!")
        
        # Agent activity
        lines.append("")
        lines.append("🤖 MULTI-AGENT WORKFLOW:")
        lines.append(f"   1. 🔍 Observability Agent → Scanned {total_buckets} buckets")
        lines.append("   2. 🛡️  Security Agent → Validated findings")
        lines.append("   3. 📊 Analysis Agent → Calculated risk scores")
        if state.get('remediation_applied'):
            lines.append("   4. 🔧 Remediation Agent → Applied security fixes")
            lines.append("   5. 🔍 Reflection Agent → Validated remediation & reflected on process")
        
        # Reflection insights (if available)
        reflection = state.get('reflection')
        if reflection and state.get('remediation_applied'):
            lines.append("")
            lines.append("🤔 REFLECTION & INSIGHTS:")
            lines.append(f"   {reflection.get('summary', '')}")
            
            improvements = reflection.get('improvements', [])
            if improvements:
                lines.append("")
                lines.append("💡 IMPROVEMENTS IDENTIFIED:")
                for improvement in improvements:
                    lines.append(f"   • {improvement}")
            
            recommendations = reflection.get('recommendations', [])
            if recommendations:
                lines.append("")
                lines.append("📈 RECOMMENDATIONS:")
                for recommendation in recommendations:
                    lines.append(f"   • {recommendation}")
        
        # Compliance context
        if vulnerable_count > 0:
            lines.append("")
            lines.append("📋 COMPLIANCE FRAMEWORKS:")
            lines.append("   • CIS AWS Foundations: 2.1.5")
            lines.append("   • NIST 800-53: AC-3")
            lines.append("   • PCI DSS: 1.2.1")
            lines.append("   • GDPR: Article 32")
        
        lines.append("")
        lines.append("=" * 70)

        # Join with actual newlines
        return "\n".join(lines)

    def _format_aiops_response(self, state: Dict[str, Any]) -> str:
        """Format the AIOps network correlation demo results"""
        lines = []
        lines.append("=" * 70)
        lines.append("🤖 AIOPS DEMO - NETWORK ROOT CAUSE CORRELATION")
        lines.append("=" * 70)
        lines.append("")

        # Challenge statement
        lines.append("🎯 CUSTOMER CHALLENGE:")
        lines.append("   Multiple observability tools (APM, Network, Infrastructure)")
        lines.append("   Difficult to correlate if issue is L1-L7")
        lines.append("   Manual correlation takes too long")
        lines.append("")

        # Infrastructure summary
        lines.append("🏗️  INFRASTRUCTURE DEPLOYED:")
        if state.get('infrastructure_deployed'):
            lines.append(f"   ✅ OpenSearch: {state.get('opensearch_domain', 'N/A')}")
            lines.append(f"   ✅ Lambda: {state.get('lambda_function_name', 'N/A')}")
            lines.append(f"   ✅ API Gateway: {state.get('api_gateway_url', 'N/A')}")
            lines.append(f"   ✅ CodePipeline: {state.get('codepipeline_name', 'N/A')}")
        else:
            lines.append("   ❌ Infrastructure deployment failed")

        # Event sources
        lines.append("")
        lines.append("📊 OBSERVABILITY SOURCES ANALYZED:")
        apm_count = len(state.get('apm_events', []))
        network_count = len(state.get('network_events', []))
        infra_count = len(state.get('infra_events', []))
        lines.append(f"   • APM (L7): {apm_count} events from DataDog/NewRelic")
        lines.append(f"   • Network (L3): {network_count} events from Cisco")
        lines.append(f"   • Infrastructure (L2): {infra_count} events from Prometheus/CloudWatch")

        # Root cause analysis
        if state.get('events_analyzed'):
            lines.append("")
            lines.append("🔍 AI CORRELATION ANALYSIS:")
            root_cause = state.get('root_cause_event', {})
            lines.append(f"   • Root Cause Layer: {state.get('root_cause_layer', 'Unknown')}")
            lines.append(f"   • Issue: {root_cause.get('metric', 'Unknown')} - {root_cause.get('details', '')}")
            lines.append(f"   • Source: {state.get('root_cause_source', 'Unknown')}")
            lines.append(f"   • Severity: {state.get('incident_severity', 'UNKNOWN')}")
            lines.append(f"   • Risk Score: {int(state.get('risk_score', 0))}/100")

            affected_services = state.get('affected_services', [])
            if affected_services:
                lines.append(f"   • Affected Services: {', '.join(affected_services)}")

        # Correlation insight
        if state.get('correlated_events'):
            lines.append("")
            lines.append("🔗 EVENT CORRELATION:")
            lines.append("   L2 (Infra) → L3 (Network) → L7 (APM)")
            lines.append("   Network packet loss caused application errors")
            lines.append("   L7 symptoms were effects, not root cause")

        # Remediation
        if state.get('remediation_triggered'):
            lines.append("")
            lines.append("🔧 AUTOMATED NETWORK REMEDIATION:")
            lines.append(f"   • Method: CodePipeline/Terraform")
            lines.append(f"   • Action: Network path failover + QoS adjustment")
            lines.append(f"   • Status: {'✅ Verified' if state.get('remediation_verified') else '⏳ In Progress'}")

            if state.get('remediation_verified'):
                pre_risk = state.get('risk_score', 0)
                post_risk = state.get('post_remediation_risk_score', 0)
                risk_reduction = pre_risk - post_risk
                lines.append(f"   • Risk Score: {int(pre_risk)} → {int(post_risk)}/100")
                lines.append(f"   • Improvement: {int(risk_reduction)} point reduction")

        # Value delivered
        reflection = state.get('reflection', {})
        if reflection and reflection.get('value_delivered'):
            lines.append("")
            lines.append("💰 VALUE DELIVERED:")
            for value in reflection.get('value_delivered', [])[:4]:
                lines.append(f"   • {value}")

        # Multi-agent workflow
        lines.append("")
        lines.append("🤖 MULTI-AGENT WORKFLOW:")
        lines.append("   1. Infrastructure Agent → Deployed event correlation platform")
        lines.append("   2. Event Injection Agent → Simulated APM/Network/Infra events")
        lines.append("   3. AI Analysis Agent → Correlated L2→L3→L7 layers")
        lines.append("   4. Approval Gate Agent → Human-in-the-loop review")
        if state.get('remediation_triggered'):
            lines.append("   5. Remediation Agent → Executed network remediation")
            lines.append("   6. Verification Agent → Validated resolution")
            lines.append("   7. Reflection Agent → Generated insights")

        # Target accounts
        lines.append("")
        lines.append("☁️  AWS ACCOUNTS:")
        lines.append(f"   • Target Account (Infrastructure): {TARGET_AWS_ACCOUNT}")
        lines.append(f"   • Agent Account (Orchestration): {AGENT_AWS_ACCOUNT}")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)