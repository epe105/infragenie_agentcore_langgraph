# InfraGenie Architecture

## Overview

InfraGenie is a multi-agent infrastructure automation system deployed on AWS AgentCore. It orchestrates infrastructure provisioning, security scanning, and remediation using Ansible Automation Platform and AWS services through MCP (Model Context Protocol) servers.

## Deployment Model

InfraGenie runs entirely on AWS AgentCore:
- **No local execution** - All demos call the deployed agent
- **Production-ready** - Same code for demos and production
- **LLM-powered** - Claude 3.5 Sonnet via AWS Bedrock
- **Tool orchestration** - MCP servers for Ansible and AWS

## System Architecture

```
User (Local Machine)
    ↓
scripts/run_demo_interactive.py
    ↓
agentcore invoke (CLI)
    ↓
┌─────────────────────────────────────────────────────────────────┐
│              AWS AgentCore Runtime (Cloud)                      │
│                                                                 │
│  src/agentcore_main.py (Entry Point)                          │
│         ↓                                                       │
│  ┌───────────────────────────────────────────────────────┐    │
│  │   InfraGenieAgentCore (MAIN ORCHESTRATOR)             │    │
│  │                                                         │    │
│  │   Responsibilities:                                     │    │
│  │   • Receives all user messages                         │    │
│  │   • Keyword detection & routing                        │    │
│  │   • Manages all components                             │    │
│  │   • Formats responses                                  │    │
│  │                                                         │    │
│  │   LLM: Claude 3.5 Sonnet (Bedrock)                    │    │
│  │   MCP Tools: Ansible AAP + AWS (Lazy Loaded)          │    │
│  │                                                         │    │
│  │   ┌─────────────────────────────────────────────┐     │    │
│  │   │ Component: PlannerAgent                     │     │    │
│  │   │ • Creates execution plans                   │     │    │
│  │   │ • System prompt-based (no MCP tools)        │     │    │
│  │   │ • Fast response (~10 seconds)               │     │    │
│  │   └─────────────────────────────────────────────┘     │    │
│  │                                                         │    │
│  │   ┌─────────────────────────────────────────────┐     │    │
│  │   │ Workflow: Infrastructure Lifecycle          │     │    │
│  │   │ • 7 specialized execution agents            │     │    │
│  │   │ • Provisions + Secures infrastructure       │     │    │
│  │   │ • LangGraph orchestration                   │     │    │
│  │   └─────────────────────────────────────────────┘     │    │
│  │                                                         │    │
│  │   ┌─────────────────────────────────────────────┐     │    │
│  │   │ Workflow: Security Scan                     │     │    │
│  │   │ • 5 specialized execution agents            │     │    │
│  │   │ • Scans + Remediates vulnerabilities        │     │    │
│  │   │ • LangGraph orchestration                   │     │    │
│  │   └─────────────────────────────────────────────┘     │    │
│  │                                                         │    │
│  │   ┌─────────────────────────────────────────────┐     │    │
│  │   │ Fallback: General LLM Query                 │     │    │
│  │   │ • Uses LangGraph with MCP tools             │     │    │
│  │   │ • Natural language interface                │     │    │
│  │   └─────────────────────────────────────────────┘     │    │
│  └───────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
    ↓                    ↓
Ansible AAP         AWS Services
(Job Templates)     (EC2, S3)
```

## Two-Level Approval Flow

```
User Request
    ↓
┌──────────────────────────────────┐
│ LEVEL 1: Planning (Strategic)   │
│                                  │
│ Planner Agent generates plan     │
│ Shows: steps, time, risks        │
│   ↓                              │
│ 👤 APPROVAL GATE #1              │
│ "Execute this plan?"             │
└──────────────────────────────────┘
    ↓ (if approved)
┌──────────────────────────────────┐
│ LEVEL 2: Execution (Tactical)   │
│                                  │
│ 7 Agents execute workflow        │
│ Detects security issues          │
│   ↓                              │
│ 👤 APPROVAL GATE #2              │
│ "Apply remediation?"             │
└──────────────────────────────────┘
    ↓ (if approved)
Final Summary with Insights
```


## Project Structure

```
infragenie_agentcore_langgraph/
├── scripts/                    # Executable scripts (local)
│   └── run_demo_interactive.py # ← THE ONLY SCRIPT YOU RUN
│                               # Interactive demo with 2-level approval
│                               # Supports --prompt for natural language
├── src/                        # Source code (deployed to AgentCore)
│   ├── agentcore_main.py      # AgentCore entry point
│   ├── infragenie_langgraph_agent.py  # Agent with LLM & routing
│   ├── planner_agent.py       # System prompt-based planner
│   ├── planner_prompt.py      # Planner system prompt (defines tool!)
│   ├── infrastructure_lifecycle_demo.py  # 7-agent workflow
│   ├── security_demo.py       # 5-agent workflow
│   ├── mcp_tools.py           # Ansible MCP integration
│   ├── aws_mcp_tools.py       # AWS MCP integration
│   ├── oauth_manager.py       # OAuth token management
│   └── system_prompt.py       # Agent system prompt
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md        # System architecture (this file)
│   ├── CODE_WALKTHROUGH.md    # Code explanation
│   └── DEMO_TALKING_POINTS.md # Presentation guide
└── README.md                   # Main documentation
```

## Component Details

### 1. Entry Point (`src/agentcore_main.py`)

- AWS AgentCore entry point
- Receives user messages via API
- Creates/retrieves main agent instance
- Returns formatted responses

### 2. Main Orchestrator Agent (`src/infragenie_langgraph_agent.py`)

**Class: InfraGenieAgentCore**

This is the **main orchestrator** that manages all components and workflows.

**Responsibilities:**
- **Message Routing**: Receives all user messages and routes to appropriate components
- **LLM Management**: Instantiates Claude 3.5 Sonnet (Bedrock)
- **Tool Management**: Lazy loads Ansible MCP and AWS MCP tools
- **Keyword Detection**: Intelligent detection supporting natural language
- **Component Orchestration**: Manages PlannerAgent and workflow components
- **Response Formatting**: Formats all outputs for user display

**Key Methods:**
- `__init__()` - Creates LLM, initializes PlannerAgent component
- `initialize()` - Lazy loads MCP tools, builds LangGraph
- `process_message()` - **Main routing logic** - routes to components
- `_is_planner_request()` - Detects plan creation keywords
- `_is_infrastructure_lifecycle_request()` - Detects execution keywords (natural language)
- `create_infrastructure_plan()` - Routes to PlannerAgent component
- `_run_infrastructure_lifecycle()` - Routes to 7-agent workflow component
- `_run_security_scan()` - Routes to 5-agent workflow component

**Routing Flow:**
```python
async def process_message(self, message: str) -> str:
    # Check if planner request (no MCP tools needed)
    if self._is_planner_request(message):
        return await self.create_infrastructure_plan(message)  # → PlannerAgent

    # Initialize MCP tools if needed
    if not self.initialized:
        await self.initialize()

    # Route to infrastructure workflow?
    if self._is_infrastructure_lifecycle_request(message):
        return await self._run_infrastructure_lifecycle(message)  # → 7 agents

    # Route to security workflow?
    if self._is_security_scan_request(message):
        return await self._run_security_scan(message)  # → 5 agents

    # Fallback: general LLM query
    return await self.graph.ainvoke(initial_state)
```

### 3. Planner Component (`src/planner_agent.py`)

**Class: PlannerAgent**

A **component** (not standalone agent) used by InfraGenieAgentCore for planning.

**The "Deep Agent Pattern" - System Prompt-Based Tool**

The planner demonstrates a unique pattern where the tool is defined entirely in the system prompt, not in code!

**How it works:**
1. System prompt (`planner_prompt.py`) defines a "tool" called `create_infrastructure_plan`
2. LLM reads the prompt and understands how to create plans
3. When asked, LLM generates structured JSON plans
4. Code just parses and validates - no planning logic!

**Key Features:**
- **No Planning Code**: Tool behavior defined in prompt
- **Dynamic**: LLM adapts plans to any request
- **Fast**: No MCP tools needed, just LLM
- **Flexible**: Update behavior by editing prompt

**Planner Keywords:**
- "create a plan"
- "make a plan"
- "plan for"
- "show me a plan"

**Output:**
- Task summary and plain language explanation
- 8 execution steps with tool attribution
- Risk assessment and time estimates
- Resources to create
- Cleanup instructions

### 4. Infrastructure Lifecycle Workflow (`src/infrastructure_lifecycle_demo.py`)

**7-Agent Workflow:**

1. **🚀 Provisioning Agent**
   - Looks up AAP job template "AWS - Create VM"
   - Launches job via Ansible MCP
   - Logs: "🚀 [PROVISIONING AGENT] Starting EC2 provisioning..."

2. **💾 Storage Agent**
   - Creates S3 bucket via AWS MCP
   - Intentionally removes public access block (for demo)
   - Logs: "💾 [STORAGE AGENT] Creating S3 bucket..."

3. **🔍 Observability Agent**
   - Scans bucket for public access
   - Detects security issue
   - Logs: "🔍 [OBSERVABILITY AGENT] Scanning for security issues..."

4. **🛡️ Security Agent**
   - Validates findings
   - Adds compliance context (CIS, NIST, PCI DSS, GDPR)
   - Logs: "🛡️ [SECURITY AGENT] Validating findings..."

5. **📊 Analysis Agent**
   - Calculates risk score (0-100)
   - Base risk + compliance violations
   - Logs: "📊 [ANALYSIS AGENT] Calculating risk scores..."

6. **🔧 Remediation Agent**
   - Applies public access block
   - Secures bucket
   - Logs: "🔧 [REMEDIATION AGENT] Applying security fixes..."

7. **🔍 Reflection Agent**
   - Validates all components
   - Generates insights and recommendations
   - Logs: "🔍 [REFLECTION AGENT] Validating infrastructure..."

**State Management:**
- Uses TypedDict for type safety
- Passes state between agents
- Collects logs for execution visibility
- Generates reflection for insights

### 5. Security Scan Workflow (`src/security_demo.py`)

**5-Agent Workflow:**

1. **🔍 Observability Agent** - Scans all S3 buckets
2. **🛡️ Security Agent** - Validates findings
3. **📊 Analysis Agent** - Calculates risk scores
4. **🔧 Remediation Agent** - Applies fixes
5. **🔍 Reflection Agent** - Validates and reflects


### 6. MCP Tool Integration (Lazy Loading)

**Lazy Loading Pattern:**
- MCP tools are NOT loaded at module import time
- Imported only when needed (execution workflows)
- Planner works fast without waiting for MCP
- Avoids 30-second AgentCore initialization timeout

**Ansible MCP (`src/mcp_tools.py`):**
- OAuth authentication
- HTTP streaming client
- Tools: list_job_templates, run_job, job_status, job_logs
- Wraps AAP API calls

**AWS MCP (`src/aws_mcp_tools.py`):**
- AWS CLI wrapper
- Tools: call_aws (executes any AWS CLI command)
- Used for S3 operations

**OAuth Manager (`src/oauth_manager.py`):**
- Client credentials flow
- Token caching and refresh
- Used by Ansible MCP

## Execution Flow

### Demo Execution (Main Orchestrator Flow)

```
1. User runs: python scripts/run_demo_interactive.py
   ↓
2. Script calls: agentcore invoke '{"prompt": "provision an ec2 vm and an s3 bucket"}'
   ↓
3. AgentCore invokes: src/agentcore_main.py
   ↓
4. Entry point calls: InfraGenieAgentCore.process_message()  ← MAIN ORCHESTRATOR
   ↓
5. Main orchestrator: Keyword detection
   - _is_planner_request()? NO
   - _is_infrastructure_lifecycle_request()? YES
   ↓
6. Main orchestrator routes to: _run_infrastructure_lifecycle()
   ↓
7. Workflow component executes: 7-agent workflow (LangGraph)
   ↓
8. Each workflow agent:
   - Adds log entry
   - Calls MCP tools
   - Updates state
   ↓
9. Main orchestrator: Formats response
   ↓
10. Returns to user: Execution log + Summary
```

### Planner Execution (Main Orchestrator Flow)

```
1. User: "Create a plan for provision ec2 and s3"
   ↓
2. Script calls: agentcore invoke '{"prompt": "create a plan..."}'
   ↓
3. Entry point calls: InfraGenieAgentCore.process_message()  ← MAIN ORCHESTRATOR
   ↓
4. Main orchestrator: Keyword detection
   - _is_planner_request()? YES
   ↓
5. Main orchestrator routes to: create_infrastructure_plan()
   ↓
6. Main orchestrator calls: self.planner.create_plan()  ← Planner component
   ↓
7. PlannerAgent component: Generates plan using LLM + system prompt
   ↓
8. Main orchestrator: Validates and formats plan
   ↓
9. Returns to user: Formatted plan
```

### Keyword Detection

The agent uses intelligent keyword matching to route requests:

**Planner Keywords (Fastest - No MCP):**
- "create a plan"
- "make a plan"
- "plan for"
- "show me a plan"

**Infrastructure Lifecycle Detection (Smart Routing):**

The agent uses a **flexible, natural language-friendly detection** that looks for combinations:

1. **Action words**: provision, create, deploy, setup
2. **Compute resources**: ec2, vm, instance
3. **Storage resources**: s3, bucket, storage

**Examples that work:**
- ✅ "provision an ec2 vm and an s3 bucket"
- ✅ "create a vm and s3 storage"
- ✅ "deploy ec2 instance and bucket"
- ✅ "setup vm and s3"

**Detection Logic:**
```python
has_provision = any(word in message for word in ["provision", "create", "deploy", "setup"])
has_compute = any(word in message for word in ["ec2", "vm", "instance"])
has_storage = any(word in message for word in ["s3", "bucket", "storage"])

if has_provision and has_compute and has_storage:
    return True  # Trigger infrastructure lifecycle
```

**Security Scan Keywords:**
- "security scan"
- "scan buckets"
- "vulnerable buckets"

**If no keyword matches:**
- Uses LLM for general queries
- Can call tools dynamically
- Natural language interface


## Key Design Decisions

### 1. AgentCore-Only Execution

**Why:** Simplifies deployment and demonstrates production behavior
- No local dependencies needed (just Python + AgentCore CLI)
- Same code for demos and production
- Shows real AgentCore capabilities

### 2. Deterministic Workflows

**Why:** Infrastructure operations should be predictable
- Fixed sequence of agents
- No LLM reasoning within workflows
- Conditional routing based on state flags
- Faster execution, lower cost

### 3. Keyword Detection

**Why:** Reliable routing to specialized workflows
- Simple string matching
- No LLM overhead for routing
- Predictable behavior
- Falls back to LLM for general queries

### 4. Execution Logs

**Why:** Visibility into agent progress
- Each agent adds log entry
- Logs included in response
- Shows multi-agent orchestration
- Helps with debugging

### 5. System Prompt-Based Planner (Deep Agent Pattern)

**Why:** Tool behavior defined in prompt, not code
- LLM generates plans dynamically
- No planning logic to maintain
- Update behavior by editing prompt
- Demonstrates advanced agentic pattern
- Fast execution (no MCP loading needed)

### 6. Two-Level Approval

**Why:** Strategic and tactical decision points
- **Level 1**: Review plan before execution (save time/money)
- **Level 2**: Approve specific remediations (granular control)
- User understands what will happen upfront
- Can abort at multiple points

### 7. Lazy Loading

**Why:** Avoid initialization timeouts
- Planner runs without MCP tools
- Tools loaded only when executing workflows
- Faster response for planning requests
- Stays under 30-second AgentCore timeout

### 8. Reflection Pattern

**Why:** Intelligent insights and recommendations
- Analyzes workflow outcome
- Generates context-aware summary
- Provides actionable recommendations
- Educational value for demos

## Technology Stack

- **AWS AgentCore** - Deployment platform
- **LangGraph** - Multi-agent orchestration
- **AWS Bedrock** - LLM (Claude 3.5 Sonnet)
- **MCP** - Tool integration protocol
- **Ansible AAP** - Infrastructure automation
- **AWS Services** - EC2, S3

## Deployment

```bash
# Deploy to AgentCore
agentcore deploy

# What gets deployed:
# - All files in src/
# - Dependencies from requirements.txt
# - Configuration from .bedrock_agentcore.yaml
```

## Monitoring

- **CloudWatch Logs** - Agent execution logs
- **X-Ray** - Distributed tracing
- **GenAI Observability** - LLM metrics
- **AgentCore Dashboard** - Agent status

## Security

- **OAuth** - Ansible MCP authentication
- **IAM Roles** - AWS permissions
- **Environment Variables** - Secrets management
- **AgentCore** - Managed runtime security
