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
scripts/run_demo.py
    ↓
agentcore invoke (CLI)
    ↓
┌─────────────────────────────────────────────────────────┐
│         AWS AgentCore Runtime (Cloud)                   │
│                                                          │
│  src/agentcore_main.py (Entry Point)                   │
│         ↓                                                │
│  InfraGenieAgentCore                                    │
│  ├── LLM: Claude 3.5 Sonnet (Bedrock)                  │
│  ├── Keyword Detection                                  │
│  └── Workflow Routing                                   │
│         ↓                                                │
│  LangGraph Workflows                                    │
│  ├── Infrastructure Lifecycle (7 agents)                │
│  └── Security Scan (5 agents)                           │
│         ↓                                                │
│  MCP Tool Integration                                   │
│  ├── Ansible MCP (OAuth)                                │
│  └── AWS MCP                                            │
└─────────────────────────────────────────────────────────┘
    ↓                    ↓
Ansible AAP         AWS Services
(Job Templates)     (EC2, S3)
```


## Project Structure

```
infragenie_agentcore_langgraph/
├── scripts/                    # Executable scripts (local)
│   ├── run_demo.py            # Calls deployed agent
│   └── cleanup_demo.py        # Resource cleanup
├── src/                        # Source code (deployed to AgentCore)
│   ├── agentcore_main.py      # AgentCore entry point
│   ├── infragenie_langgraph_agent.py  # Agent with LLM
│   ├── infrastructure_lifecycle_demo.py  # 7-agent workflow
│   ├── security_demo.py       # 5-agent workflow
│   ├── mcp_tools.py           # Ansible MCP integration
│   ├── aws_mcp_tools.py       # AWS MCP integration
│   ├── oauth_manager.py       # OAuth token management
│   └── system_prompt.py       # Agent system prompt
├── docs/                       # Documentation
└── README.md                   # Main documentation
```

## Component Details

### 1. Entry Point (`src/agentcore_main.py`)

- AWS AgentCore entry point
- Receives user messages via API
- Creates/retrieves agent instance
- Returns formatted responses

### 2. Agent Core (`src/infragenie_langgraph_agent.py`)

**Responsibilities:**
- LLM instantiation (Claude 3.5 Sonnet)
- Tool loading (Ansible + AWS MCP)
- Keyword detection for workflow routing
- Message processing and response formatting

**Key Methods:**
- `__init__()` - Instantiates LLM
- `initialize()` - Loads tools, builds graph
- `process_message()` - Routes to workflows or LLM
- `_is_infrastructure_lifecycle_request()` - Keyword detection
- `_run_infrastructure_lifecycle()` - Executes 7-agent workflow
- `_run_security_scan()` - Executes 5-agent workflow


### 3. Infrastructure Lifecycle Workflow (`src/infrastructure_lifecycle_demo.py`)

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

### 4. Security Scan Workflow (`src/security_demo.py`)

**5-Agent Workflow:**

1. **🔍 Observability Agent** - Scans all S3 buckets
2. **🛡️ Security Agent** - Validates findings
3. **📊 Analysis Agent** - Calculates risk scores
4. **🔧 Remediation Agent** - Applies fixes
5. **🔍 Reflection Agent** - Validates and reflects


### 5. MCP Tool Integration

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

### Demo Execution

```
1. User runs: python scripts/run_demo.py
   ↓
2. Script calls: agentcore invoke '{"prompt": "infrastructure lifecycle"}'
   ↓
3. AgentCore invokes: src/agentcore_main.py
   ↓
4. Entry point calls: InfraGenieAgentCore.process_message()
   ↓
5. Agent detects keyword: "infrastructure lifecycle"
   ↓
6. Routes to: _run_infrastructure_lifecycle()
   ↓
7. Executes: 7-agent workflow
   ↓
8. Each agent:
   - Adds log entry
   - Calls MCP tools
   - Updates state
   ↓
9. Returns: Formatted response with logs
   ↓
10. User sees: Execution log + Summary
```

### Keyword Detection

The agent uses keyword matching to route requests:

**Infrastructure Lifecycle Keywords:**
- "infrastructure lifecycle"
- "full lifecycle"
- "provision and secure"
- "infrastructure demo"

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

### 5. Reflection Pattern

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
