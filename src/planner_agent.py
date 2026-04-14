"""
Planner Agent Implementation for InfraGenie

This module demonstrates how to use the system prompt-based planner tool
to create execution plans before running workflows.

Key Concept: The "planner tool" doesn't exist in code - it's purely defined
in the system prompt. The LLM generates structured plans, and we parse them.
"""

from __future__ import annotations
import json
import re
from typing import Optional, Dict, List, Any, TYPE_CHECKING
from langchain_core.messages import HumanMessage, SystemMessage
from planner_prompt import INFRAGENIE_WITH_PLANNER

if TYPE_CHECKING:
    from langchain_aws import ChatBedrock


class PlannerAgent:
    """
    Agent that uses system prompt-based planning to guide workflow execution.

    This is the "deep agent pattern" - the planner is entirely defined in the
    system prompt, with no code implementation needed.
    """

    def __init__(self, llm: ChatBedrock):
        """
        Initialize planner agent

        Args:
            llm: The LLM to use for planning (Claude via Bedrock)
        """
        self.llm = llm

    async def create_plan(self, user_request: str) -> Optional[Dict[str, Any]]:
        """
        Ask the LLM to create an infrastructure plan using the system prompt tool

        Args:
            user_request: The user's infrastructure request

        Returns:
            Parsed plan dictionary, or None if no plan was generated
        """
        print("\n🤔 [PLANNER AGENT] Analyzing request and creating plan...")

        # Create messages with planner system prompt
        messages = [
            SystemMessage(content=INFRAGENIE_WITH_PLANNER),
            HumanMessage(content=f"""
Please create an infrastructure plan for the following request:

"{user_request}"

Use the create_infrastructure_plan tool to generate a detailed plan.
""")
        ]

        # Get LLM response
        response = await self.llm.ainvoke(messages)
        response_text = response.content

        # Parse the plan from the response
        plan = self._extract_plan(response_text)

        if plan:
            print("   ✅ Plan created successfully")
            self._print_plan_summary(plan)
        else:
            print("   ℹ️  No plan generated - this may be a simple query")

        return plan

    def _extract_plan(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured plan from LLM response

        The LLM outputs plans in <infrastructure_plan> XML tags as defined
        in the system prompt.

        Args:
            response: Raw LLM response text

        Returns:
            Parsed plan dictionary, or None if no plan found
        """
        # Look for <infrastructure_plan> block
        match = re.search(
            r'<infrastructure_plan>\s*(\{.*?\})\s*</infrastructure_plan>',
            response,
            re.DOTALL
        )

        if match:
            try:
                plan_json = match.group(1)
                plan = json.loads(plan_json)
                return plan
            except json.JSONDecodeError as e:
                print(f"   ⚠️  Failed to parse plan JSON: {e}")
                return None

        return None

    def _print_plan_summary(self, plan: Dict[str, Any]):
        """Print a human-readable summary of the plan"""
        print(f"\n   📋 PLAN SUMMARY:")
        print(f"   {plan.get('task_summary', 'N/A')}")
        print(f"\n   ⏱️  Estimated Time: {plan.get('estimated_total_time', 'Unknown')}")
        print(f"   🎯 Risk Level: {plan.get('risk_assessment', {}).get('level', 'Unknown').upper()}")
        print(f"   ✋ Approval Required: {'Yes' if plan.get('approval_required') else 'No'}")

        steps = plan.get('steps', [])
        if steps:
            print(f"\n   📝 EXECUTION STEPS ({len(steps)}):")
            for step in steps:
                agent = step.get('agent', 'unknown')
                action = step.get('action', 'N/A')
                print(f"      {step['step_number']}. [{agent.upper()}] {action}")

        resources = plan.get('resources_created', [])
        if resources:
            print(f"\n   🏗️  Resources to Create: {', '.join(resources)}")

        print()

    def validate_plan(self, plan: Dict[str, Any]) -> bool:
        """
        Validate that a plan has all required fields

        Args:
            plan: The plan dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['task_summary', 'steps', 'risk_assessment']

        for field in required_fields:
            if field not in plan:
                print(f"   ⚠️  Plan missing required field: {field}")
                return False

        # Validate steps
        steps = plan.get('steps', [])
        if not steps:
            print("   ⚠️  Plan has no steps")
            return False

        for step in steps:
            required_step_fields = ['step_number', 'agent', 'action', 'tool']
            for field in required_step_fields:
                if field not in step:
                    print(f"   ⚠️  Step {step.get('step_number', '?')} missing: {field}")
                    return False

        return True

    async def explain_plan(self, plan: Dict[str, Any]) -> str:
        """
        Ask the LLM to explain the plan in plain language

        Args:
            plan: The plan to explain

        Returns:
            Human-readable explanation
        """
        messages = [
            SystemMessage(content="You are a helpful assistant that explains infrastructure plans."),
            HumanMessage(content=f"""
Please explain this infrastructure plan in plain language for a non-technical user:

{json.dumps(plan, indent=2)}

Be concise but cover:
1. What will happen
2. What resources will be created
3. Any risks or things to be aware of
4. How long it will take
""")
        ]

        response = await self.llm.ainvoke(messages)
        return response.content


# ============================================================================
# Integration with Existing Workflows
# ============================================================================

async def execute_plan(plan: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a plan by routing to appropriate agents based on plan steps

    This function bridges the gap between the plan (generated by LLM in system prompt)
    and the actual workflow execution.

    Args:
        plan: The execution plan from the planner agent
        state: The workflow state

    Returns:
        Updated state after execution
    """
    print("\n🚀 [EXECUTOR] Executing plan...")

    from infrastructure_lifecycle_demo import (
        provisioning_agent,
        storage_agent,
        observability_agent,
        security_agent,
        analysis_agent,
        remediation_agent,
        reflection_agent
    )

    # Map agent names to functions
    agent_map = {
        'provisioning': provisioning_agent,
        'storage': storage_agent,
        'observability': observability_agent,
        'security': security_agent,
        'analysis': analysis_agent,
        'remediation': remediation_agent,
        'reflection': reflection_agent
    }

    # Execute steps in order
    steps = plan.get('steps', [])
    for step in sorted(steps, key=lambda s: s['step_number']):
        agent_name = step.get('agent')
        agent_func = agent_map.get(agent_name)

        if agent_func:
            print(f"\n   Step {step['step_number']}: Executing {agent_name} agent...")
            state = await agent_func(state)
        else:
            print(f"   ⚠️  Unknown agent: {agent_name}")

    return state


# ============================================================================
# Example Usage
# ============================================================================

async def demo_planner():
    """
    Demonstration of how to use the planner agent

    This shows the full flow:
    1. User makes a request
    2. Planner creates a plan
    3. System validates the plan
    4. System explains the plan to user
    5. Upon approval, executes the plan
    """
    import os
    try:
        from langchain_aws import ChatBedrock
    except ImportError:
        print("❌ This demo requires langchain_aws to be installed")
        return

    # Initialize LLM
    llm = ChatBedrock(
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        model_kwargs={
            "temperature": 0.1,
            "max_tokens": 8000
        }
    )

    # Create planner agent
    planner = PlannerAgent(llm)

    # Simulate user request
    user_request = "Run the full infrastructure lifecycle demo"

    # Step 1: Create plan
    plan = await planner.create_plan(user_request)

    if not plan:
        print("No plan created - may be a simple query")
        return

    # Step 2: Validate plan
    if not planner.validate_plan(plan):
        print("❌ Plan validation failed")
        return

    # Step 3: Explain plan to user
    explanation = await planner.explain_plan(plan)
    print("\n📖 PLAN EXPLANATION FOR USER:")
    print(explanation)

    # Step 4: Check if approval needed
    if plan.get('approval_required'):
        print("\n✋ This plan requires approval before execution")
        # In a real system, you'd prompt the user here
        user_approves = True  # Simulated approval

        if not user_approves:
            print("❌ User declined - aborting execution")
            return

    # Step 5: Execute plan
    initial_state = {
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

    final_state = await execute_plan(plan, initial_state)

    print("\n✅ Plan execution complete!")
    print(f"   EC2 Instance: {final_state.get('instance_id', 'N/A')}")
    print(f"   S3 Bucket: {final_state.get('bucket_name', 'N/A')}")
    print(f"   Validation: {'✅ Passed' if final_state.get('validation_passed') else '❌ Failed'}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_planner())
