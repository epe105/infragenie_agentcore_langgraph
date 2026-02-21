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
from mcp_tools import get_mcp_tools, mcp_manager
from aws_mcp_tools import get_aws_mcp_tools, aws_mcp_manager


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
    
    def _initialize_bedrock_llm(self):
        """Initialize AWS Bedrock LLM"""
        # Use Claude 3.5 Sonnet via inference profile (supported for on-demand)
        return ChatBedrock(
            model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            model_kwargs={
                "temperature": 0.1,
                "max_tokens": 4000
            }
        )
    
    async def initialize(self):
        """Initialize the agent with MCP tools and build the graph"""
        if self.initialized:
            return
        
        try:
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
    
    async def process_message(self, message: str) -> str:
        """Process a user message and return the agent's response"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Refresh tokens if needed
            await mcp_manager.refresh_token_if_needed()
            await aws_mcp_manager.refresh_token_if_needed()
            
            # Check if this is an infrastructure lifecycle request
            if self._is_infrastructure_lifecycle_request(message):
                return await self._run_infrastructure_lifecycle(message)
            
            # Check if this is a security scan request
            if self._is_security_scan_request(message):
                return await self._run_security_scan(message)
            
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
            "infrastructure demo",
            "full stack demo",
            "end to end infrastructure",
            "provision configure backup"
        ]
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
    
    async def _run_infrastructure_lifecycle(self, message: str) -> str:
        """Run the full infrastructure lifecycle workflow"""
        from infrastructure_lifecycle_demo import create_infrastructure_lifecycle_workflow_async
        
        print("\n🏗️  Initiating Infrastructure Lifecycle Demo...")
        
        # Create the infrastructure lifecycle workflow
        lifecycle_graph = create_infrastructure_lifecycle_workflow_async()
        
        # Initial state
        initial_state = {
            "instance_id": "",
            "instance_ip": "",
            "instance_name": "",
            "bucket_name": "",
            "bucket_is_public": False,
            "bucket_secured": False,
            "ec2_provisioned": False,
            "s3_created": False,
            "security_issue_found": False,
            "findings_validated": False,
            "risk_calculated": False,
            "security_remediated": False,
            "validation_passed": False,
            "logs": [],
            "reflection": {}
        }
        
        # Run the workflow asynchronously
        final_state = await lifecycle_graph.ainvoke(initial_state)
        
        # Format the response
        response = self._format_infrastructure_lifecycle_response(final_state)
        return response
    
    async def _run_security_scan(self, message: str) -> str:
        """Run the multi-agent security scan workflow"""
        from security_demo import create_security_workflow_scan_all_async
        
        print("\n🔒 Initiating Multi-Agent Security Scan...")
        
        # Create the security workflow
        security_graph = create_security_workflow_scan_all_async()
        
        # Initial state
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
        
        # Run the workflow asynchronously
        final_state = await security_graph.ainvoke(initial_state)
        
        # Format the response
        response = self._format_security_response(final_state)
        return response
    
    async def _run_ansible_vm_provisioning(self, message: str) -> str:
        """Run Ansible VM provisioning via MCP"""
        print("\n🚀 Initiating Ansible VM Provisioning...")
        
        try:
            # Get Ansible MCP tools
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