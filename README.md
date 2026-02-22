# InfraGenie - Multi-Agent Infrastructure Automation

InfraGenie is a multi-agent AI system that orchestrates infrastructure provisioning, security scanning, and remediation using Ansible Automation Platform and AWS services through MCP (Model Context Protocol) servers.

## 🎯 Overview

InfraGenie demonstrates the power of multi-agent orchestration by combining:
- **Ansible MCP Server**: Infrastructure provisioning via Ansible Automation Platform (AAP)
- **AWS MCP Server**: Cloud resource management and security operations
- **LangGraph**: Multi-agent workflow orchestration
- **AWS Bedrock**: Claude 3.5 Sonnet for intelligent decision-making

## ⚡ Quick Start

### Activate Virtual Environment

**Always run this first:**
```bash
source .venv/bin/activate
```

You'll see `(.venv)` in your prompt when activated.

**To deactivate later:**
```bash
deactivate
```

### Quick Reference

| Task | Command |
|------|---------|
| **Activate environment** | `source .venv/bin/activate` |
| **Run demo (interactive)** | `python scripts/run_demo.py` |
| **Run infrastructure demo** | `python scripts/run_demo.py --infrastructure` |
| **Run security demo** | `python scripts/run_demo.py --security` |
| **Clean up (interactive)** | `python scripts/cleanup_demo.py` |
| **Clean up everything** | `python scripts/cleanup_demo.py --all` |
| **Clean up EC2 only** | `python scripts/cleanup_demo.py --ec2` |
| **Clean up S3 only** | `python scripts/cleanup_demo.py --s3` |
| **List resources** | `python scripts/cleanup_demo.py --list` |
| **Get help** | `python scripts/run_demo.py --help` |
| **Deactivate environment** | `deactivate` |

## 📁 Project Structure

```
infragenie_agentcore_langgraph/
├── scripts/                    # Executable scripts
│   ├── run_demo.py            # Main demo runner
│   └── cleanup_demo.py        # Resource cleanup
├── src/                        # Source code (deployed to AgentCore)
│   ├── agentcore_main.py      # AgentCore entry point
│   ├── infragenie_langgraph_agent.py  # Agent with LLM
│   ├── infrastructure_lifecycle_demo.py  # 7-agent workflow
│   ├── security_demo.py       # 5-agent workflow
│   ├── mcp_tools.py           # Ansible MCP integration
│   ├── aws_mcp_tools.py       # AWS MCP integration
│   ├── oauth_manager.py       # OAuth management
│   └── system_prompt.py       # Agent prompt
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md
│   ├── CODE_WALKTHROUGH.md
│   ├── DEMO_TALKING_POINTS.md
│   └── DEPLOY.md
├── README.md                   # This file
├── USAGE.md                    # Quick reference
└── requirements.txt            # Python dependencies
```

### What Goes Where

- **scripts/** - What you run (demos, cleanup)
- **src/** - What gets deployed to AgentCore
- **docs/** - Documentation and guides

```
┌─────────────────────────────────────────────────────────────┐
│                  LangGraph Multi-Agent Workflow              │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Provision │→ │ Storage  │→ │Observ-   │→ │ Security │   │
│  │  Agent   │  │  Agent   │  │ability   │  │  Agent   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │             │          │
│       ▼             ▼              ▼             ▼          │
│  Ansible MCP   AWS MCP        AWS MCP       AWS MCP        │
│       │             │              │             │          │
│       ▼             ▼              ▼             ▼          │
│      AAP        S3 API        S3 API        S3 API         │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ Analysis │→ │Remediate │→ │Reflection│                 │
│  │  Agent   │  │  Agent   │  │  Agent   │                 │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                 │
│       │             │              │                        │
│       ▼             ▼              ▼                        │
│   AWS MCP       AWS MCP        Both MCPs                   │
└─────────────────────────────────────────────────────────────┘
```

## 🤖 Multi-Agent Workflow

### Infrastructure Lifecycle Demo (7 Agents)

1. **🚀 Provisioning Agent** - Creates EC2 instance via Ansible AAP
2. **💾 Storage Agent** - Creates S3 bucket for backups
3. **🔍 Observability Agent** - Detects security issues (public bucket)
4. **🛡️ Security Agent** - Validates findings against compliance frameworks
5. **📊 Analysis Agent** - Calculates risk scores (out of 100)
6. **🔧 Remediation Agent** - Applies security fixes
7. **🔍 Reflection Agent** - Validates remediation and reflects on process

### Security Scan Demo (5 Agents)

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

**3. Configure environment:**
```bash
# Copy example and edit with your credentials
cp .env.example .env
nano .env  # or use your preferred editor
```

Add your credentials:
- AAP OAuth credentials
- AWS credentials (if not using AWS CLI profile)

**4. Deploy agent to AgentCore:**
```bash
agentcore deploy
```
Wait for deployment to complete (~1-2 minutes).

### Run Demos

**Always activate the virtual environment first:**
```bash
source .venv/bin/activate
```

Then run demos:
```bash
# Interactive menu (recommended)
python scripts/run_demo.py

# Or use command line
python scripts/run_demo.py --infrastructure  # Infrastructure lifecycle demo
python scripts/run_demo.py --security        # Security scan demo
python scripts/run_demo.py --query "List my Ansible inventories"
```

### Clean Up Resources

```bash
# Interactive cleanup
python scripts/cleanup_demo.py

# Or use command line
python scripts/cleanup_demo.py --all   # Clean everything
python scripts/cleanup_demo.py --ec2   # EC2 only
python scripts/cleanup_demo.py --s3    # S3 only
python scripts/cleanup_demo.py --list  # List resources
```

## 📝 How It Works

**run_demo.py** calls your deployed AgentCore agent:
- No local dependencies needed (just Python + AgentCore CLI)
- Uses `agentcore invoke` to call your production agent
- Shows real AgentCore behavior with LLM orchestration

**cleanup_demo.py** cleans up demo resources:
- Deletes EC2 instances via AAP job template
- Removes S3 buckets created by demos
- Interactive or command-line usage

## 📊 Demo Output

### Infrastructure Lifecycle Demo

```
🏗️  INFRASTRUCTURE LIFECYCLE DEMO
======================================================================

🚀 [PROVISIONING AGENT] Provisioning EC2 instance via Ansible AAP...
   ✅ EC2 provisioning initiated via AAP

💾 [STORAGE AGENT] Creating S3 bucket...
   ✅ Bucket created successfully
   🔓 Removing public access block (for demo)...

🔍 [OBSERVABILITY AGENT] Scanning for security issues...
   ⚠️  DETECTED: Bucket has no public access block

🛡️  [SECURITY AGENT] Validating findings...
   📋 COMPLIANCE VIOLATIONS:
      • CIS AWS Foundations Benchmark 2.1.5
      • NIST 800-53 AC-3
      • PCI DSS 1.2.1
      • GDPR Article 32

📊 [ANALYSIS AGENT] Calculating risk scores...
   🔴 RISK SCORE: 100/100 (CRITICAL)

🔧 [REMEDIATION AGENT] Applying security fixes...
   ✅ Security issue remediated

✅ REMEDIATION APPLIED:
   • Target Bucket: infragenie-backups-XXXX
   • Risk Score Before: 100/100
   • Risk Score After: 10/100
   • Status: ✅ Validated

🔍 [REFLECTION AGENT] Validating end-to-end infrastructure...
   ✅ END-TO-END VALIDATION PASSED

🤖 MULTI-AGENT WORKFLOW:
   1. 🚀 Provisioning Agent → Provisioned EC2 instance
   2. 💾 Storage Agent → Created S3 bucket
   3. 🔍 Observability Agent → Detected security issues
   4. 🛡️  Security Agent → Validated findings
   5. 📊 Analysis Agent → Calculated risk scores
   6. 🔧 Remediation Agent → Applied security fixes
   7. 🔍 Reflection Agent → Validated remediation & reflected
```

## 🔒 Security & Compliance

InfraGenie validates against multiple compliance frameworks:

- **CIS AWS Foundations Benchmark 2.1.5**: S3 bucket public access
- **NIST 800-53 AC-3**: Access Enforcement
- **PCI DSS 1.2.1**: Restrict public access to cardholder data
- **GDPR Article 32**: Security of processing

## 🛠️ Development

### Project Structure

```
infragenie_agentcore_langgraph/
├── run_demo.py                          # Unified demo runner
├── cleanup_demo.py                      # Resource cleanup script
├── infrastructure_lifecycle_demo.py     # 7-agent infrastructure workflow
├── security_demo.py                     # 5-agent security workflow
├── infragenie_langgraph_agent.py       # Main agent implementation
├── mcp_tools.py                        # Ansible MCP integration
├── aws_mcp_tools.py                    # AWS MCP integration
├── oauth_manager.py                    # OAuth token management
├── system_prompt.py                    # Agent system prompts
├── agentcore_main.py                   # AWS Bedrock AgentCore entry
├── docs/                               # Documentation
│   ├── ARCHITECTURE.md                 # Architecture details
│   ├── DEMO_TALKING_POINTS.md         # Demo presentation guide
│   └── INFRASTRUCTURE_LIFECYCLE_DEMO.md
├── tests/                              # Test files
└── scripts/                            # Utility scripts
```

### Running Tests

```bash
# Test MCP connection
python tests/test_mcp_connection.py

# Test AgentCore integration
python tests/test_agentcore_integration.py
```

## 🔧 Troubleshooting

### "Command not found" or Import Errors

**Problem:** Forgot to activate virtual environment

**Solution:**
```bash
source .venv/bin/activate
```

You should see `(.venv)` at the start of your prompt. If you don't see it, the environment isn't activated.

**To deactivate later:**
```bash
deactivate
```

### Demo won't start
- Check `.env` file has all required credentials
- Verify MCP servers are accessible:
  ```bash
  curl https://ansible-mcp.labs.presidio-labs.com/mcp
  curl https://aws-mcp.labs.presidio-labs.com/mcp
  ```
- Ensure virtual environment is activated: `source .venv/bin/activate`

### "No module named 'aws_mcp_tools'" in cleanup script

**Problem:** Running from wrong directory or venv not activated

**Solution:**
```bash
# Make sure you're in the project root
cd infragenie_agentcore_langgraph

# Activate venv
source .venv/bin/activate

# Run from project root
python scripts/cleanup_demo.py
```

### Cleanup fails
- List resources first: `python scripts/cleanup_demo.py --list`
- Try manual cleanup:
  ```bash
  ansible-playbook ansible_demo/delete-aws-vm.yaml
  aws s3 rb s3://infragenie-backups-XXXX --force
  ```

### MCP connection errors
- Verify OAuth credentials in `.env`
- Check token expiration
- Ensure MCP servers are running

### AWS permission errors
- Verify AWS credentials have S3 and EC2 permissions
- Check IAM policies
- Ensure correct AWS region is set

## 📚 Documentation

- [Architecture Details](docs/ARCHITECTURE.md)
- [Code Walkthrough](docs/CODE_WALKTHROUGH.md)
- [Demo Talking Points](docs/DEMO_TALKING_POINTS.md)
- [Reflection Explained](docs/REFLECTION_EXPLAINED.md)

## 📋 Command Cheat Sheet

### Essential Commands

```bash
# 1. ALWAYS activate venv first!
source .venv/bin/activate

# 2. Run demos
python scripts/run_demo.py                    # Interactive menu
python scripts/run_demo.py --infrastructure   # Infrastructure demo
python scripts/run_demo.py --security         # Security demo

# 3. Clean up resources
python scripts/cleanup_demo.py                # Interactive cleanup
python scripts/cleanup_demo.py --all          # Clean everything
python scripts/cleanup_demo.py --list         # List resources

# 4. Deploy agent
agentcore deploy

# 5. Deactivate when done
deactivate
```

### Typical Workflow

```bash
# Navigate to project
cd infragenie_agentcore_langgraph

# Activate venv (ALWAYS FIRST!)
source .venv/bin/activate

# Run demo
python scripts/run_demo.py --infrastructure

# Clean up
python scripts/cleanup_demo.py --all

# Deactivate
deactivate
```

### Quick Checks

```bash
# Check if venv is active (look for (.venv) in prompt)
echo $VIRTUAL_ENV

# List all available commands
python scripts/run_demo.py --help
python scripts/cleanup_demo.py --help

# Check agent deployment status
agentcore status
```

## 🧹 Cleanup

After running demos, clean up resources using the dedicated cleanup script:

### Interactive Cleanup
```bash
python cleanup_demo.py
```

### Direct Cleanup Commands
```bash
# Always activate venv first!
source .venv/bin/activate

# Clean up everything (EC2 + S3)
python scripts/cleanup_demo.py --all

# Clean up EC2 instances only
python scripts/cleanup_demo.py --ec2

# Clean up S3 buckets only
python scripts/cleanup_demo.py --s3

# List resources without deleting
python cleanup_demo.py --list

# Clean up specific bucket
python cleanup_demo.py --bucket infragenie-backups-1234
```

### Manual Cleanup (if needed)
```bash
# Delete EC2 instance
ansible-playbook ansible_demo/delete-aws-vm.yaml

# Delete S3 bucket
aws s3 rb s3://infragenie-backups-XXXX --force
```

### 