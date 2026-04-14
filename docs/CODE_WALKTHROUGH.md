# InfraGenie Code Walkthrough

A step-by-step guide to understanding the InfraGenie codebase.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Entry Point](#entry-point)
3. [Agent Initialization](#agent-initialization)
4. [Message Processing & Routing](#message-processing--routing)
5. [Planner Agent (System Prompt-Based)](#planner-agent-system-prompt-based)
6. [Workflow Execution](#workflow-execution)
7. [Tool Integration](#tool-integration)

---

## Project Structure

```
infragenie_agentcore_langgraph/
├── scripts/
│   └── run_demo_interactive.py  # ← THE ONLY SCRIPT YOU RUN
│                                # Interactive demo (2-level approval)
├── src/                      # Deployed to AgentCore
│   ├── agentcore_main.py    # Entry point
│   ├── infragenie_langgraph_agent.py  # Agent core & routing
│   ├── planner_agent.py     # System prompt-based planner
│   ├── planner_prompt.py    # Planner system prompt (defines tool!)
│   ├── infrastructure_lifecycle_demo.py  # 7-agent workflow
│   ├── security_demo.py     # 5-agent workflow
│   ├── mcp_tools.py         # Ansible MCP (lazy loaded)
│   ├── aws_mcp_tools.py     # AWS MCP (lazy loaded)
│   ├── oauth_manager.py     # OAuth
│   └── system_prompt.py     # Agent prompt
└── docs/                     # Documentation
    ├── ARCHITECTURE.md       # System architecture
    ├── CODE_WALKTHROUGH.md   # This file
    └── DEMO_TALKING_POINTS.md # Presentation guide
```

**What you run:** `scripts/run_demo_interactive.py` (the only script!)
**What gets deployed:** Everything in `src/`

---

## Entry Point

### User Runs Demo

```bash
python scripts/run_demo_interactive.py
```

This script:
1. Shows interactive menu (or accepts command-line options)
2. Calls `agentcore invoke` with user's choice
3. Handles two-level approval (plan approval + remediation approval)
4. Displays formatted response

### AgentCore Entry Point (`src/agentcore_main.py`)

```python
from bedrock_agentcore import BedrockAgentCoreApp
from infragenie_langgraph_agent import InfraGenieAgentCore

app = BedrockAgentCoreApp()
agent_instance = None

def get_agent():
    """Get or create the MAIN ORCHESTRATOR AGENT"""
    global agent_instance
    if agent_instance is None:
        agent_instance = InfraGenieAgentCore()  # ← Main orchestrator created
    return agent_instance

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt")
    agent = get_agent()  # ← Get main orchestrator
    result = asyncio.run(agent.process_message(user_message))  # ← Routes everything
    return {"result": result}
```

**Flow:**
1. AgentCore receives API call
2. `invoke()` function is called
3. **Main orchestrator** instance created (first time) or retrieved
4. Main orchestrator processes message and routes to components
5. Result returned


---

## Agent Initialization

### Phase 1: Constructor (`src/infragenie_langgraph_agent.py`)

```python
class InfraGenieAgentCore:
    """
    MAIN ORCHESTRATOR AGENT

    Routes all user messages to appropriate components:
    - PlannerAgent component (for planning)
    - Infrastructure Lifecycle workflow (7 agents)
    - Security Scan workflow (5 agents)
    - General LLM query (fallback)
    """

    def __init__(self):
        self.llm = self._initialize_bedrock_llm()  # ← LLM ready
        self.planner = PlannerAgent(self.llm)      # ← Planner component ready
        self.tools: List[BaseTool] = []            # ← Empty (lazy loaded)
        self.graph = None                          # ← Not built
        self.initialized = False                   # ← Not ready

    def _initialize_bedrock_llm(self):
        return ChatBedrock(
            model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            model_kwargs={
                "temperature": 0.1,
                "max_tokens": 4000
            }
        )
```

**After Phase 1:**
- ✅ Main orchestrator instantiated
- ✅ LLM ready (Claude 3.5 Sonnet)
- ✅ Planner component instantiated
- ❌ MCP tools not loaded yet
- ❌ LangGraph not built yet

### Phase 2: Async Initialization

```python
async def initialize(self):
    if self.initialized:
        return
    
    # 1. Load Ansible MCP tools
    ansible_tools = await get_mcp_tools()
    
    # 2. Load AWS MCP tools
    aws_tools = await get_aws_mcp_tools()
    
    # 3. Combine tools
    self.tools = ansible_tools + aws_tools
    
    # 4. Bind tools to LLM
    self.llm_with_tools = self.llm.bind_tools(self.tools)
    
    # 5. Build graph
    self._build_graph()
    self.initialized = True
```

**After Phase 2:**
- ✅ LLM ready
- ✅ Tools loaded (~20-30 tools)
- ✅ Graph built
- ✅ Ready to process messages

**Note:** Phase 2 takes 20-30 seconds, so we use lazy loading!

---

## Message Processing & Routing

### Main Orchestrator Flow (`process_message()`)

**This is the core routing logic of InfraGenieAgentCore (main orchestrator)**

**Key Innovation: Planner checks BEFORE initialization!**

```python
class InfraGenieAgentCore:
    async def process_message(self, message: str) -> str:
        """
        MAIN ROUTING LOGIC

        Routes user messages to appropriate components:
        1. PlannerAgent component (fast, no MCP tools)
        2. Infrastructure Lifecycle workflow (7 agents)
        3. Security Scan workflow (5 agents)
        4. General LLM query (fallback)
        """

        # 1. Route to PLANNER COMPONENT? (before loading MCP tools!)
        if self._is_planner_request(message):
            return await self.create_infrastructure_plan(message)
            # ← Calls self.planner.create_plan() - component, not workflow

        # 2. For workflow components, ensure MCP tools initialized
        if not self.initialized:
            await self.initialize()  # ← Load MCP tools (slow, 20-30s)

        # 3. Refresh OAuth tokens for MCP servers
        from mcp_tools import mcp_manager  # ← Lazy import
        from aws_mcp_tools import aws_mcp_manager
        await mcp_manager.refresh_token_if_needed()
        await aws_mcp_manager.refresh_token_if_needed()

        # 4. Route to INFRASTRUCTURE LIFECYCLE WORKFLOW?
        if self._is_infrastructure_lifecycle_request(message):
            return await self._run_infrastructure_lifecycle(message)
            # ← Calls workflow component with 7 agents

        # 5. Route to SECURITY SCAN WORKFLOW?
        if self._is_security_scan_request(message):
            return await self._run_security_scan(message)
            # ← Calls workflow component with 5 agents

        # 6. FALLBACK: Use LLM for general queries
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "tools_available": len(self.tools) > 0
        }
        result = await self.graph.ainvoke(initial_state)
        return result["messages"][-1].content
```

### Keyword Detection

**Planner Keywords (Checked FIRST):**
```python
def _is_planner_request(self, message: str) -> bool:
    keywords = ["create a plan", "make a plan", "plan for", "show me a plan"]
    return any(keyword in message.lower() for keyword in keywords)
```

**Natural Language Infrastructure Detection (NEW!):**

Instead of exact phrase matching, the agent now uses **flexible, component-based detection**:

```python
def _is_infrastructure_lifecycle_request(self, message: str) -> bool:
    message_lower = message.lower()

    # Specific keywords (exact matches)
    lifecycle_keywords = [
        "infrastructure lifecycle",
        "full lifecycle",
        "provision ec2 and s3",
        "infrastructure demo"
    ]

    # Smart detection - look for combinations
    has_compute = any(word in message_lower for word in ["ec2", "vm", "instance"])
    has_storage = any(word in message_lower for word in ["s3", "bucket", "storage"])
    has_provision = any(word in message_lower for word in ["provision", "create", "deploy", "setup"])

    # Match if has provision + compute + storage, OR matches a specific keyword
    if has_provision and has_compute and has_storage:
        return True

    return any(keyword in message_lower for keyword in lifecycle_keywords)
```

**This enables natural administrator language:**
- ✅ "provision an ec2 vm and an s3 bucket"
- ✅ "create a vm and s3 storage"
- ✅ "deploy ec2 instance and bucket"
- ✅ "setup vm and s3"

**Why this approach?**
- ✅ Flexible - works with natural variations
- ✅ Fast - no LLM needed for routing
- ✅ Predictable - keyword-based logic
- ✅ User-friendly - administrators can speak naturally
- ✅ Lower cost - avoids LLM calls for routing

---

## Planner Component (System Prompt-Based)

**PlannerAgent is a COMPONENT used by InfraGenieAgentCore (main orchestrator)**

### The "Deep Agent Pattern"

**Key Concept:** The planner tool is defined entirely in the system prompt, NOT in code!

**Usage by Main Orchestrator:**
```python
class InfraGenieAgentCore:
    def __init__(self):
        self.planner = PlannerAgent(self.llm)  # ← Component instantiated

    async def create_infrastructure_plan(self, message: str):
        # Main orchestrator delegates to planner component
        plan = await self.planner.create_plan(message)  # ← Use component
        # ... validate and format ...
        return formatted_plan
```

### Step 1: System Prompt Defines Tool (`src/planner_prompt.py`)

```python
PLANNER_SYSTEM_PROMPT = """
## Tool: create_infrastructure_plan

When you receive infrastructure requests, create a plan:

<infrastructure_plan>
{
  "task_summary": "...",
  "steps": [
    {
      "step_number": 1,
      "agent": "provisioning",
      "action": "Create EC2 via Ansible AAP",
      "tool": "ansible_mcp",
      "dependencies": [],
      "estimated_duration": "3-5 minutes"
    }
  ],
  "risk_assessment": {
    "level": "low|medium|high",
    "factors": [...],
    "mitigation": "..."
  },
  "estimated_total_time": "...",
  "resources_created": [...],
  "cleanup_steps": [...]
}
</infrastructure_plan>
"""
```

**There is NO `create_infrastructure_plan()` function in Python!**
The tool exists only in the prompt.

### Step 2: LLM Generates Plans

```python
class PlannerAgent:
    async def create_plan(self, user_request: str):
        # Just invoke LLM with system prompt
        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=user_request)
        ]
        response = await self.llm.ainvoke(messages)

        # LLM generates structured JSON in XML tags
        return self._extract_plan(response.content)
```

### Step 3: Parse and Format

```python
    def _extract_plan(self, response: str):
        # Find <infrastructure_plan> tags
        match = re.search(r'<infrastructure_plan>(.*?)</infrastructure_plan>',
                         response, re.DOTALL)
        if match:
            return json.loads(match.group(1))
```

### Step 4: Validate Plan

```python
    def validate_plan(self, plan: Dict):
        required = ['task_summary', 'steps', 'risk_assessment']
        for field in required:
            if field not in plan:
                return False
        return True
```

### Step 5: Explain in Plain Language

```python
    async def explain_plan(self, plan: Dict) -> str:
        # Ask LLM to explain the plan
        messages = [
            SystemMessage(content="Explain this plan:"),
            HumanMessage(content=json.dumps(plan))
        ]
        response = await self.llm.ainvoke(messages)
        return response.content
```

### Why This is Powerful

**Traditional Approach (100+ lines):**
```python
def create_plan(request):
    plan = {"steps": []}
    if "ec2" in request:
        plan["steps"].append({"agent": "provisioning"})
    if "s3" in request:
        plan["steps"].append({"agent": "storage"})
    # ... 100 more lines of hard-coded logic
```

**Deep Agent Pattern (10 lines):**
```python
def create_plan(request):
    # LLM figures it out based on system prompt!
    response = await llm.ainvoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=request)
    ])
    return extract_plan(response.content)
```

**Benefits:**
- ✅ No planning logic to maintain
- ✅ LLM adapts to any request
- ✅ Update behavior by editing prompt
- ✅ Fast (no MCP tools needed)
- ✅ Easy to extend (add new fields to prompt)

---

## Workflow Execution

### Infrastructure Lifecycle (`src/infrastructure_lifecycle_demo.py`)

#### State Definition

```python
class InfraState(TypedDict):
    # EC2 Instance
    instance_id: str
    instance_ip: str
    instance_name: str
    
    # S3 Bucket
    bucket_name: str
    bucket_is_public: bool
    bucket_secured: bool
    
    # Security Analysis
    security_findings: List[str]
    compliance_violations: List[str]
    risk_score: float
    
    # Workflow Status
    ec2_provisioned: bool
    s3_created: bool
    security_issue_found: bool
    findings_validated: bool
    risk_calculated: bool
    security_remediated: bool
    validation_passed: bool
    
    # Logs and Reflection
    logs: Annotated[List[str], add_messages]
    reflection: dict
```

#### Agent Example: Provisioning Agent

```python
async def provisioning_agent(state: InfraState) -> InfraState:
    print("\n🚀 [PROVISIONING AGENT] Provisioning EC2...")
    
    logs = state.get("logs", [])
    logs.append("🚀 [PROVISIONING AGENT] Starting EC2 provisioning...")
    
    # Get Ansible MCP tools
    tools = await get_ansible_mcp_tools()
    run_job = next((t for t in tools if "run_job" in t.name.lower()), None)
    
    # Look up job template
    templates_result = await list_job_templates._arun()
    template_id = extract_template_id(templates_result, "AWS - Create VM")
    
    # Launch job
    result = await run_job._arun(
        template_id=template_id,
        extra_vars={"vm_name": instance_name, ...}
    )
    
    state["ec2_provisioned"] = True
    logs.append(f"✅ AAP Job launched for instance '{instance_name}'")
    state["logs"] = logs
    return state
```

**Key Points:**
- Each agent is an async function
- Takes state, returns updated state
- Adds log entries for visibility
- Calls MCP tools directly (no LLM)


#### Graph Construction

```python
def create_infrastructure_lifecycle_workflow_async() -> StateGraph:
    workflow = StateGraph(InfraState)
    
    # Add nodes (agents)
    workflow.add_node("provision", provisioning_agent)
    workflow.add_node("storage", storage_agent)
    workflow.add_node("observability", observability_agent)
    workflow.add_node("security_validate", security_validation_agent)
    workflow.add_node("analysis", analysis_agent)
    workflow.add_node("remediate", security_remediation_agent)
    workflow.add_node("reflect", validation_agent)
    
    # Define edges (flow)
    workflow.set_entry_point("provision")
    workflow.add_edge("provision", "storage")
    
    workflow.add_conditional_edges(
        "storage",
        should_scan_security,  # Python function
        {
            "scan": "observability",
            "end": END
        }
    )
    
    # ... more edges ...
    
    return workflow.compile()
```

**Conditional Routing:**

```python
def should_scan_security(state: InfraState) -> str:
    if state["s3_created"]:
        return "scan"
    return "end"
```

Simple Python logic - no LLM needed!

---

## Tool Integration

### Ansible MCP (`src/mcp_tools.py`)

```python
class MCPToolWrapper(BaseTool):
    mcp_tool_name: str
    token_manager: OAuthTokenManager
    
    async def _arun(self, **kwargs) -> str:
        # 1. Get OAuth token
        token = self.token_manager.get_token()
        
        # 2. Initialize MCP session
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", mcp_server_url,
                json={"method": "initialize", ...},
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                session_id = response.headers.get('mcp-session-id')
        
        # 3. Call tool
        async with client.stream(
            "POST", mcp_server_url,
            json={
                "method": "tools/call",
                "params": {
                    "name": self.mcp_tool_name,
                    "arguments": kwargs
                }
            },
            headers={"mcp-session-id": session_id}
        ) as response:
            result = await parse_response(response)
        
        return result
```

**Available Tools:**
- `list_job_templates` - List AAP templates
- `run_job` - Execute job template
- `job_status` - Check job status
- `job_logs` - Get job logs

### AWS MCP (`src/aws_mcp_tools.py`)

```python
class AWSMCPToolWrapper(BaseTool):
    async def _arun(self, cli_command: str) -> str:
        # Wraps AWS CLI commands
        result = await call_mcp_server(
            tool_name="call_aws",
            arguments={"cli_command": cli_command}
        )
        return result
```

**Example Usage:**
```python
# Create S3 bucket
await call_aws._arun(
    cli_command="aws s3api create-bucket --bucket my-bucket"
)

# Check public access
await call_aws._arun(
    cli_command="aws s3api get-public-access-block --bucket my-bucket"
)
```

---

## Complete Example Flow

### User: "provision an ec2 vm and an s3 bucket"

```
1. scripts/run_demo_interactive.py
   ↓ calls agentcore invoke

2. src/agentcore_main.py
   ↓ invoke() function

3. InfraGenieAgentCore.process_message()  ← MAIN ORCHESTRATOR
   ↓
   ↓ keyword detection:
   ↓ - _is_planner_request()? NO
   ↓ - _is_infrastructure_lifecycle_request()? YES
   ↓

4. Main orchestrator routes to: _run_infrastructure_lifecycle()
   ↓
   ↓ creates workflow graphs
   ↓

5. Workflow component executes 7 agents:
   🚀 Provisioning Agent → logs + Ansible AAP call
   💾 Storage Agent → logs + S3 create
   🔍 Observability Agent → logs + S3 scan
   🛡️ Security Agent → logs + compliance validation
   📊 Analysis Agent → logs + risk calculation
   🔧 Remediation Agent → logs + S3 fix
   🔍 Reflection Agent → logs + insights

6. Main orchestrator: _format_infrastructure_lifecycle_response()
   ↓
   ↓ formats logs and results
   ↓

7. Response returned to user:
   📋 EXECUTION LOG:
      🚀 [PROVISIONING AGENT] Starting...
      💾 [STORAGE AGENT] Creating...
      ...
   📊 INFRASTRUCTURE SUMMARY:
      ...
```

### User: "Create a plan for provision ec2 and s3"

```
1. scripts/run_demo_interactive.py
   ↓ calls agentcore invoke

2. src/agentcore_main.py
   ↓ invoke() function

3. InfraGenieAgentCore.process_message()  ← MAIN ORCHESTRATOR
   ↓
   ↓ keyword detection:
   ↓ - _is_planner_request()? YES
   ↓

4. Main orchestrator routes to: create_infrastructure_plan()
   ↓
   ↓ calls self.planner.create_plan(message)  ← Planner component
   ↓

5. PlannerAgent component:
   - Sends message to LLM with planner system prompt
   - LLM generates structured plan (JSON)
   - Returns plan

6. Main orchestrator: Validates and formats plan
   ↓

7. Response returned to user:
   📋 INFRASTRUCTURE PLAN
      Steps: 1-8
      Risk: MEDIUM
      Time: 10-15 minutes
      ...
```

---

## Key Takeaways

1. **Main Orchestrator** - InfraGenieAgentCore routes all requests to components
2. **Component Architecture** - Planner is a component, workflows are components
3. **AgentCore-only** - All execution happens in deployed agent
4. **Intelligent routing** - Keyword detection (natural language support), falls back to LLM
5. **Deterministic workflows** - Fixed agent sequence, no LLM in workflow
6. **Execution logs** - Each workflow agent adds log entry for visibility
7. **MCP tools** - OAuth-protected Ansible, AWS CLI wrapper
8. **State management** - TypedDict passed between workflow agents
9. **Reflection** - Workflow generates insights from execution outcome

---

## Next Steps

1. **Run the demo:** `python scripts/run_demo_interactive.py`
2. Read `src/agentcore_main.py` - Entry point
3. Read `src/infragenie_langgraph_agent.py` - **Main orchestrator** (routing logic)
4. Read `src/planner_agent.py` - Planner component
5. Read `src/infrastructure_lifecycle_demo.py` - Workflow component (7 agents)
6. Check logs in CloudWatch
