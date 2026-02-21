# InfraGenie Code Walkthrough

A step-by-step guide to understanding the InfraGenie codebase.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Entry Point](#entry-point)
3. [Agent Initialization](#agent-initialization)
4. [Message Processing](#message-processing)
5. [Workflow Execution](#workflow-execution)
6. [Tool Integration](#tool-integration)

---

## Project Structure

```
infragenie_agentcore_langgraph/
├── scripts/
│   ├── run_demo.py          # Calls deployed agent
│   └── cleanup_demo.py      # Resource cleanup
├── src/                      # Deployed to AgentCore
│   ├── agentcore_main.py    # Entry point
│   ├── infragenie_langgraph_agent.py  # Agent core
│   ├── infrastructure_lifecycle_demo.py  # 7-agent workflow
│   ├── security_demo.py     # 5-agent workflow
│   ├── mcp_tools.py         # Ansible MCP
│   ├── aws_mcp_tools.py     # AWS MCP
│   ├── oauth_manager.py     # OAuth
│   └── system_prompt.py     # Prompt
└── docs/                     # Documentation
```

**What you run:** `scripts/run_demo.py`  
**What gets deployed:** Everything in `src/`

---

## Entry Point

### User Runs Demo

```bash
python scripts/run_demo.py
```

This script:
1. Shows interactive menu
2. Calls `agentcore invoke` with user's choice
3. Displays formatted response

### AgentCore Entry Point (`src/agentcore_main.py`)

```python
from bedrock_agentcore import BedrockAgentCoreApp
from infragenie_langgraph_agent import InfraGenieAgentCore

app = BedrockAgentCoreApp()
agent_instance = None

def get_agent():
    global agent_instance
    if agent_instance is None:
        agent_instance = InfraGenieAgentCore()  # ← Agent created
    return agent_instance

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt")
    agent = get_agent()
    result = asyncio.run(agent.process_message(user_message))
    return {"result": result}
```

**Flow:**
1. AgentCore receives API call
2. `invoke()` function is called
3. Agent instance created (first time) or retrieved
4. Message processed
5. Result returned


---

## Agent Initialization

### Phase 1: Constructor (`src/infragenie_langgraph_agent.py`)

```python
class InfraGenieAgentCore:
    def __init__(self):
        self.llm = self._initialize_bedrock_llm()  # ← LLM ready
        self.tools: List[BaseTool] = []            # ← Empty
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
- ✅ LLM instantiated (Claude 3.5 Sonnet)
- ❌ No tools loaded
- ❌ No graph built

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

---

## Message Processing

### Main Flow (`process_message()`)

```python
async def process_message(self, message: str) -> str:
    # 1. Ensure initialized
    if not self.initialized:
        await self.initialize()
    
    # 2. Refresh OAuth tokens
    await mcp_manager.refresh_token_if_needed()
    await aws_mcp_manager.refresh_token_if_needed()
    
    # 3. Check for workflow keywords
    if self._is_infrastructure_lifecycle_request(message):
        return await self._run_infrastructure_lifecycle(message)
    
    if self._is_security_scan_request(message):
        return await self._run_security_scan(message)
    
    # 4. Use LLM for general queries
    initial_state = {
        "messages": [HumanMessage(content=message)],
        "tools_available": len(self.tools) > 0
    }
    result = await self.graph.ainvoke(initial_state)
    return result["messages"][-1].content
```


### Keyword Detection

```python
def _is_infrastructure_lifecycle_request(self, message: str) -> bool:
    keywords = [
        "infrastructure lifecycle",
        "full lifecycle",
        "provision and secure",
        "infrastructure demo"
    ]
    return any(keyword in message.lower() for keyword in keywords)
```

**Why keyword detection?**
- Fast routing (no LLM needed)
- Predictable behavior
- Lower cost
- Falls back to LLM if no match

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

### User: "Run the infrastructure lifecycle demo"

```
1. scripts/run_demo.py
   ↓ calls agentcore invoke
   
2. src/agentcore_main.py
   ↓ invoke() function
   
3. InfraGenieAgentCore.process_message()
   ↓ keyword detection
   
4. _run_infrastructure_lifecycle()
   ↓ creates workflow
   
5. Workflow executes 7 agents:
   🚀 Provisioning → logs + AAP call
   💾 Storage → logs + S3 create
   🔍 Observability → logs + S3 scan
   🛡️ Security → logs + compliance
   📊 Analysis → logs + risk calc
   🔧 Remediation → logs + S3 fix
   🔍 Reflection → logs + insights
   
6. _format_infrastructure_lifecycle_response()
   ↓ includes execution logs
   
7. Response returned to user:
   📋 EXECUTION LOG:
      🚀 [PROVISIONING AGENT] Starting...
      💾 [STORAGE AGENT] Creating...
      ...
   📊 INFRASTRUCTURE SUMMARY:
      ...
```

---

## Key Takeaways

1. **AgentCore-only** - All execution happens in deployed agent
2. **LLM for routing** - Keyword detection, falls back to LLM
3. **Deterministic workflows** - Fixed agent sequence, no LLM in workflow
4. **Execution logs** - Each agent adds log entry for visibility
5. **MCP tools** - OAuth-protected Ansible, AWS CLI wrapper
6. **State management** - TypedDict passed between agents
7. **Reflection** - Generates insights from workflow outcome

---

## Next Steps

1. Read `src/agentcore_main.py` - Entry point
2. Read `src/infragenie_langgraph_agent.py` - Agent core
3. Read `src/infrastructure_lifecycle_demo.py` - Workflow
4. Run demo: `python scripts/run_demo.py`
5. Check logs in CloudWatch
