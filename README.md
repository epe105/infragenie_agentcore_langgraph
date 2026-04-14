# InfraGenie - Multi-Agent Infrastructure Automation

InfraGenie is a multi-agent AI system that orchestrates infrastructure provisioning, security scanning, and remediation using Ansible Automation Platform and AWS services through MCP (Model Context Protocol) servers.

## 🎯 Overview

InfraGenie demonstrates the power of multi-agent orchestration by combining:
- **🤖 Main Orchestrator Agent**: InfraGenieAgentCore routes requests to specialized components
- **📋 Planner Component**: System prompt-based planner (creates plans, no execution)
- **⚙️ Workflow Components**: 7-agent infrastructure lifecycle and 5-agent security scan
- **👤 Two-Level Approval**: Strategic (plan approval) + Tactical (remediation approval)
- **🖥️ Professional Web UI**: Timeline-based Streamlit interface or Gradio alternative
- **🔧 MCP Integration**: Ansible AAP for provisioning, AWS services for cloud operations
- **🧠 LangGraph**: Multi-agent workflow orchestration
- **💡 AWS Bedrock**: Claude 3.5 Sonnet for intelligent decision-making

## ⚡ Quick Start

### Three Ways to Run Demos

#### 1. Web UI (Recommended for Customer Demos) 🌟

**Streamlit - Timeline-based view with all steps visible:**
```bash
# Quick launch (auto-activates venv)
./scripts/run-streamlit.sh

# Or manually
source .venv/bin/activate
streamlit run ui/streamlit_demo.py
```

**Gradio - Alternative web interface:**
```bash
# Quick launch
./scripts/run-gradio.sh

# Or manually
source .venv/bin/activate
python ui/gradio_demo.py
```

#### 2. Command Line (For Quick Testing)
```bash
source .venv/bin/activate
python scripts/run_demo_interactive.py --prompt "provision an ec2 vm and an s3 bucket"
```

#### 3. Interactive Menu (Terminal-Based)
```bash
source .venv/bin/activate
python scripts/run_demo_interactive.py
```

### Quick Reference

| Task | Command |
|------|---------|
| **Web UI (Streamlit)** | `./scripts/run-streamlit.sh` |
| **Web UI (Gradio)** | `./scripts/run-gradio.sh` |
| **CLI Demo** | `python scripts/run_demo_interactive.py` |
| **Infrastructure Demo** | `python scripts/run_demo_interactive.py --infrastructure` |
| **Security Demo** | `python scripts/run_demo_interactive.py --security` |
| **Custom Prompt** | `python scripts/run_demo_interactive.py --prompt '<prompt>'` |
| **Activate Environment** | `source .venv/bin/activate` |
| **Deploy Agent** | `agentcore deploy` |

## 📁 Project Structure

```
infragenie_agentcore_langgraph/
│
├── ui/                         # 🖥️ Web-based user interfaces
│   ├── streamlit_demo.py       # Streamlit UI (timeline view)
│   ├── gradio_demo.py          # Gradio UI (alternative)
│   └── README.md               # UI documentation
│
├── scripts/                    # 🔧 Executable scripts
│   ├── run_demo_interactive.py # CLI demo (terminal)
│   ├── run-streamlit.sh        # Launch Streamlit UI
│   └── run-gradio.sh           # Launch Gradio UI
│
├── src/                        # 🤖 Backend code (deployed to AgentCore)
│   ├── agentcore_main.py       # AgentCore entry point
│   ├── infragenie_langgraph_agent.py  # Main orchestrator
│   ├── planner_agent.py        # Planner component
│   ├── planner_prompt.py       # Planner system prompt
│   ├── infrastructure_lifecycle_demo.py  # 7-agent workflow
│   ├── security_demo.py        # 5-agent security workflow
│   ├── mcp_tools.py            # Ansible MCP integration
│   ├── aws_mcp_tools.py        # AWS MCP integration
│   ├── oauth_manager.py        # OAuth management
│   └── system_prompt.py        # Agent prompt
│
├── docs/                       # 📚 Documentation
│   ├── ARCHITECTURE.md         # System architecture
│   ├── CODE_WALKTHROUGH.md     # Code explanation
│   ├── DEMO_TALKING_POINTS.md  # Presentation guide
│   ├── FRONTEND_OPTIONS.md     # Complete UI comparison
│   ├── QUICK_START_UI.md       # 3-minute UI setup
│   └── PROJECT_STRUCTURE.md    # Organization guide
│
├── tests/                      # 🧪 Test files
│   ├── test_agentcore_integration.py
│   └── test_mcp_connection.py
│
├── .venv/                      # Virtual environment
├── requirements.txt            # All dependencies (core + UI)
├── README.md                   # This file
└── .bedrock_agentcore.yaml     # AgentCore configuration
```

### What Goes Where

- **`ui/`** - Web interfaces for customer demos (Streamlit, Gradio)
- **`scripts/`** - CLI tools, helper scripts, automation
- **`src/`** - Backend agent code (deployed to AWS AgentCore)
- **`docs/`** - Documentation, guides, tutorials
- **`tests/`** - Test files

See [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed organization guide.

## 🖥️ Web UI Features

### Streamlit UI (Recommended)

**Perfect for customer demos - shows complete workflow timeline:**

- ✅ **Timeline View** - All steps remain visible, scroll up to review
- ✅ **Professional Design** - Gradient styling, clear visual hierarchy
- ✅ **Interactive Approvals** - Click buttons instead of typing yes/no
- ✅ **Real-time Progress** - See workflow execute step-by-step
- ✅ **Mobile Responsive** - Works on phones, tablets, desktop

**Launch:**
```bash
./scripts/run-streamlit.sh
# Opens automatically at http://localhost:8501
```

**Timeline Example:**
```
Step 1: 📋 Execution Plan Created
  [Full plan details here]

Step 2: ✅ Plan Approved
  User approved the execution plan

Step 3: 🤖 Workflow Execution
  [Execution logs here]

Step 4: 🚨 Remediation Approval
  [Approval form - current action]

Step 5: ✅ Remediation Applied
  [Results here]
```

### Gradio UI (Alternative)

**Good for quick demos and ML audiences:**

- ✅ **Tab-based Interface** - Separate tabs for different sections
- ✅ **Public Sharing** - Easy to share with `--share` flag
- ✅ **Automatic API** - REST API generated automatically

**Launch:**
```bash
./scripts/run-gradio.sh
# Opens at http://localhost:7860
```

See [FRONTEND_OPTIONS.md](docs/FRONTEND_OPTIONS.md) for complete comparison and deployment options.

## 🎬 Two-Level Approval Flow

```
User Request (Web UI or CLI)
     ↓
┌────────────────────────────────────┐
│ LEVEL 1: Planning (Strategic)     │
│                                    │
│ Planner Agent generates plan       │
│ Shows: steps, time, risks          │
│   ↓                                │
│ 👤 APPROVAL GATE #1                │
│ [✅ Approve] [❌ Deny]             │
└────────────────────────────────────┘
     ↓ (if approved)
┌────────────────────────────────────┐
│ LEVEL 2: Execution (Tactical)     │
│                                    │
│ 7 Agents execute workflow:        │
│ 🚀 Provisioning → 💾 Storage →    │
│ 🔍 Observability → 🛡️ Security →  │
│ 📊 Analysis                        │
│   ↓                                │
│ 👤 APPROVAL GATE #2                │
│ [✅ Approve] [❌ Deny]             │
└────────────────────────────────────┘
     ↓ (if approved)
🔧 Remediation → 🔍 Reflection
     ↓
✅ Final Summary with Insights
```

## 🤖 Architecture: Main Orchestrator + Components

### InfraGenieAgentCore (Main Orchestrator)

The main agent that orchestrates all workflows:
- **Keyword Detection & Routing**: Routes user requests to appropriate components
- **Tool Management**: Lazy loads Ansible MCP and AWS MCP tools
- **Response Formatting**: Formats all outputs for user display

### Components Orchestrated by Main Agent

#### 1. Planner Component (PlannerAgent)
- Creates execution plans (no execution)
- Uses "deep agent pattern" (tool defined in prompt)
- Fast response (~10 seconds, no MCP tools needed)

#### 2. Infrastructure Lifecycle Workflow (7 Specialized Agents)

1. **🚀 Provisioning Agent** - Creates EC2 instance via Ansible AAP
2. **💾 Storage Agent** - Creates S3 bucket for backups
3. **🔍 Observability Agent** - Detects security issues (public bucket)
4. **🛡️ Security Agent** - Validates findings against compliance frameworks
5. **📊 Analysis Agent** - Calculates risk scores (out of 100)
6. **🔧 Remediation Agent** - Applies security fixes
7. **🔍 Reflection Agent** - Validates remediation and reflects on process

#### 3. Security Scan Workflow (5 Specialized Agents)

1. **🔍 Observability Agent** - Scans all S3 buckets
2. **🛡️ Security Agent** - Validates findings
3. **📊 Analysis Agent** - Calculates risk scores
4. **🔧 Remediation Agent** - Applies security fixes
5. **🔍 Reflection Agent** - Validates and reflects

## 🚀 Setup & Installation

### Prerequisites

1. **Python 3.9+** installed
2. **AgentCore CLI** installed (`pip install agentcore`)
3. **AWS credentials** configured
4. **Ansible Automation Platform** (AAP) with job templates configured

### Initial Setup

**1. Activate virtual environment:**
```bash
source .venv/bin/activate
```
💡 You'll see `(.venv)` in your prompt when activated.

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```
This installs everything: core dependencies + web UI frameworks (Streamlit, Gradio).

**3. Configure environment:**
```bash
# Copy example and edit with your credentials
cp .env.example .env
nano .env  # or use your preferred editor
```

Add your credentials:
- AAP OAuth credentials
- AWS credentials (if not using AWS CLI profile)
- AWS Account IDs: `TARGET_AWS_ACCOUNT` and `AGENT_AWS_ACCOUNT` (for multi-account demos)

**4. Deploy agent to AgentCore:**
```bash
agentcore deploy
```
Wait for deployment to complete (~1-2 minutes).

### Run a Demo

**Web UI (Recommended for customers):**
```bash
./scripts/run-streamlit.sh
# Or manually: streamlit run ui/streamlit_demo.py
```

**Command Line (Quick testing):**
```bash
source .venv/bin/activate
python scripts/run_demo_interactive.py --prompt "provision an ec2 vm and an s3 bucket"
```

## 📝 How It Works

### Natural Language Interface

**Administrators can use natural language prompts:**

```bash
python scripts/run_demo_interactive.py --prompt "provision an ec2 vm and an s3 bucket"
```

The agent intelligently detects what you want:
- ✅ "provision an ec2 vm and an s3 bucket" → Infrastructure lifecycle
- ✅ "create a vm and s3 storage" → Infrastructure lifecycle
- ✅ "deploy ec2 instance and bucket" → Infrastructure lifecycle
- ✅ "scan my s3 buckets for security issues" → Security scan

**Smart Detection Logic:**
- Looks for **action words**: provision, create, deploy, setup
- Looks for **compute resources**: ec2, vm, instance
- Looks for **storage resources**: s3, bucket, storage
- Combines them to trigger the right workflow

### Workflow Execution

1. **Planning Phase**: AI creates detailed execution plan
2. **Plan Approval**: User reviews and approves/denies
3. **Execution Phase**: Multi-agent system executes workflow
4. **Remediation Approval**: User approves/denies security fixes
5. **Reflection Phase**: System validates and reflects on results

**Resource cleanup is handled within the demo itself** - no separate cleanup needed!

## 🔑 The "Deep Agent Pattern"

InfraGenie's planner demonstrates a unique pattern where the tool is defined entirely in the system prompt!

### Traditional Approach (100+ lines of code):
```python
def create_plan(request):
    plan = {"steps": []}
    if "ec2" in request:
        plan["steps"].append({"agent": "provisioning", ...})
    if "s3" in request:
        plan["steps"].append({"agent": "storage", ...})
    # ... 100 more lines of if/else logic
    return plan
```

### Deep Agent Pattern (10 lines of code):
```python
# System prompt defines tool behavior in planner_prompt.py
# LLM generates plans dynamically based on prompt

async def create_plan(user_request):
    response = await llm.ainvoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=user_request)
    ])
    return extract_plan(response.content)
```

**Benefits:**
- ✅ No planning logic to maintain
- ✅ LLM adapts to any request
- ✅ Update behavior by editing prompt
- ✅ Fast (no MCP loading needed)
- ✅ Easy to extend

## 🔒 Security & Compliance

InfraGenie validates against multiple compliance frameworks:

- **CIS AWS Foundations Benchmark 2.1.5**: S3 bucket public access
- **NIST 800-53 AC-3**: Access Enforcement
- **PCI DSS 1.2.1**: Restrict public access to cardholder data
- **GDPR Article 32**: Security of processing

## 🔧 Troubleshooting

### "Command not found" or Import Errors

**Problem:** Forgot to activate virtual environment

**Solution:**
```bash
source .venv/bin/activate
```

You should see `(.venv)` at the start of your prompt. If you don't see it, the environment isn't activated.

### Web UI Won't Start

**Problem:** Port already in use or dependencies missing

**Solution:**
```bash
# Check if dependencies are installed
pip install -r requirements.txt

# Use different port for Streamlit
streamlit run ui/streamlit_demo.py --server.port 8502

# Or for Gradio, edit ui/gradio_demo.py and change server_port
```

### AWS Credentials Expired

**Problem:** `The security token included in the request is expired`

**Solution:**
```bash
aws sso login
# or refresh your credentials
```

### Demo won't start
- Check `.env` file has all required credentials
- Verify MCP servers are accessible:
  ```bash
  curl https://your-ansible-mcp-server.com/mcp
  ```
- Ensure virtual environment is activated: `source .venv/bin/activate`
- Refresh AWS credentials if expired

### Script won't run

**Problem:** Running from wrong directory or venv not activated

**Solution:**
```bash
# Make sure you're in the project root
cd infragenie_agentcore_langgraph

# Activate venv
source .venv/bin/activate

# Run the demo
./scripts/run-streamlit.sh
```

### Need to clean up resources manually?
- Use AWS Console or AWS CLI to delete resources if needed
- EC2 instances: Use AAP or AWS Console
- S3 buckets: `aws s3 rb s3://infragenie-backups-XXXX --force`

### Agent Not Responding
```bash
agentcore status  # Check agent health
aws logs tail /aws/bedrock-agentcore/runtimes/... --follow  # Check logs
```

## 📚 Documentation

### Getting Started
- [QUICK_START_UI.md](docs/QUICK_START_UI.md) - 3-minute web UI setup guide
- [FRONTEND_OPTIONS.md](docs/FRONTEND_OPTIONS.md) - Complete UI comparison & deployment

### Architecture & Development
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture, planner pattern
- [CODE_WALKTHROUGH.md](docs/CODE_WALKTHROUGH.md) - Code explanation, deep agent pattern
- [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) - File organization guide

### Demos & Presentations
- [DEMO_TALKING_POINTS.md](docs/DEMO_TALKING_POINTS.md) - Presentation guide
- [ui/README.md](ui/README.md) - UI-specific documentation

## 📋 Command Cheat Sheet

### Web UI Commands

```bash
# Launch Streamlit (recommended for demos)
./scripts/run-streamlit.sh

# Launch Gradio (alternative)
./scripts/run-gradio.sh

# Manual launch
source .venv/bin/activate
streamlit run ui/streamlit_demo.py
python ui/gradio_demo.py
```

### CLI Commands

```bash
# 1. Activate venv
source .venv/bin/activate

# 2. Run demos
python scripts/run_demo_interactive.py                    # Interactive menu
python scripts/run_demo_interactive.py --infrastructure   # Infrastructure demo
python scripts/run_demo_interactive.py --security         # Security demo
python scripts/run_demo_interactive.py --prompt "provision an ec2 vm and an s3 bucket"

# 3. Agent management
agentcore deploy     # Deploy agent
agentcore status     # Check status

# 4. Deactivate
deactivate
```

### Development Commands

```bash
# Run tests
python tests/test_mcp_connection.py
python tests/test_agentcore_integration.py

# Deploy changes
agentcore deploy

# View logs
aws logs tail /aws/bedrock-agentcore/runtimes/infragenie_langgraph_agent-... --follow
```

## 🎯 Demo Value

InfraGenie demonstrates five cutting-edge agentic patterns:

1. **🖥️ Professional Web UI**
   - Timeline-based view showing complete workflow
   - Interactive approval buttons
   - Scroll up to review previous steps
   - Production-ready interface for customers

2. **📋 System Prompt-Based Planner** (Deep Agent Pattern)
   - Tool defined in prompt, not code
   - LLM generates plans dynamically
   - Fast execution (~10 seconds)

3. **👤 Two-Level Human Approval**
   - Strategic approval: "Execute this plan?"
   - Tactical approval: "Apply this fix?"
   - Granular control over automation

4. **💬 Natural Language Interface**
   - Administrators use conversational language
   - "provision an ec2 vm and an s3 bucket"
   - Agent intelligently routes to workflows
   - No need to remember exact commands

5. **🤖 Multi-Agent Orchestration**
   - 7 specialized agents collaborating
   - Each agent has specific expertise
   - Real infrastructure automation

**Perfect for demonstrating how LLMs can orchestrate real infrastructure with human oversight, natural language control, and professional UI!**

## 📝 Notes

- **Multiple interfaces**: Web UI for demos, CLI for quick testing
- **Demo creates real resources** in AWS (costs money)
- **Two approval gates** prevent unwanted changes
- **Planner runs fast** (~10 seconds) - no MCP loading needed
- **Execution takes 3-10 minutes** - real infrastructure provisioning
- **Refresh AWS credentials** if you see token expiration errors
- **All dependencies in one file** - `requirements.txt` includes core + UI

## 🛠️ Development

### Running Tests

```bash
source .venv/bin/activate

# Test MCP connection
python tests/test_mcp_connection.py

# Test AgentCore integration
python tests/test_agentcore_integration.py
```

### Deploy Changes

```bash
# After modifying src/ files
agentcore deploy

# Check deployment
agentcore status

# After modifying UI files, just refresh browser
# Streamlit auto-reloads on file changes
```

### Adding New Features

- **New UI component**: Add to `ui/` directory
- **New backend logic**: Add to `src/` directory
- **New automation script**: Add to `scripts/` directory
- **New documentation**: Add to `docs/` directory

See [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed guidelines.

## 🚀 Deployment Options

### Local (Your Laptop)
```bash
./scripts/run-streamlit.sh
# Share screen during presentations
```

### Cloud VM (AWS EC2)
```bash
streamlit run ui/streamlit_demo.py --server.address 0.0.0.0 --server.port 80
# Access via: http://your-ec2-ip
```

### Streamlit Cloud (Free Hosting)
```bash
# 1. Push to GitHub
git add ui/ requirements.txt
git commit -m "Add web UI"
git push

# 2. Deploy at streamlit.io/cloud
# Get permanent URL: https://your-app.streamlit.app
```

See [FRONTEND_OPTIONS.md](docs/FRONTEND_OPTIONS.md) for complete deployment guide including Docker, ngrok, and custom domains.

## 🤝 Contributing

1. Follow the project structure - put files in the right directories
2. Update documentation when adding features
3. Test thoroughly before committing
4. Use helper scripts for consistency
5. Keep the UI and backend code separated

## 📞 Questions?

- **Quick start**: See [QUICK_START_UI.md](docs/QUICK_START_UI.md)
- **UI setup**: See [FRONTEND_OPTIONS.md](docs/FRONTEND_OPTIONS.md)
- **Architecture**: See [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **File organization**: See [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- **Demos**: See [DEMO_TALKING_POINTS.md](docs/DEMO_TALKING_POINTS.md)
