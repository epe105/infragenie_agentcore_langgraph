# InfraGenie Scripts

Executable scripts for running and managing InfraGenie demos.

## Scripts

### run_demo.py

Main demo runner that calls your deployed AgentCore agent.

**Usage:**
```bash
# Interactive menu
python scripts/run_demo.py

# Direct commands
python scripts/run_demo.py --infrastructure    # Infrastructure lifecycle demo
python scripts/run_demo.py --security          # Security scan demo
python scripts/run_demo.py --query "List all AAP inventories"
```

**Requirements:**
- AgentCore CLI installed (`pip install agentcore`)
- Agent deployed to AgentCore (`agentcore deploy`)
- AWS credentials configured

**What it does:**
- Calls your deployed agent via `agentcore invoke`
- No local dependencies needed (agent runs in AWS)
- Demonstrates multi-agent workflows through natural language

### cleanup_demo.py

Cleans up resources created by InfraGenie demos.

**Usage:**
```bash
# Interactive menu
python scripts/cleanup_demo.py

# Direct commands
python scripts/cleanup_demo.py --all           # Clean up everything
python scripts/cleanup_demo.py --ec2           # EC2 instances only
python scripts/cleanup_demo.py --s3            # S3 buckets only
python scripts/cleanup_demo.py --list          # List resources
python scripts/cleanup_demo.py --bucket <name> # Specific bucket
```

**Requirements:**
- Python virtual environment activated
- MCP servers running (Ansible MCP + AWS MCP)
- AWS credentials configured
- AAP credentials configured

**What it does:**
- Lists InfraGenie demo resources (EC2, S3)
- Deletes S3 buckets via AWS MCP
- Deletes EC2 instances via Ansible AAP job template
- Provides cleanup summary

## Setup

**IMPORTANT: Always activate the virtual environment first!**

```bash
source .venv/bin/activate
```

You'll see `(.venv)` in your prompt when activated.

1. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Add your AAP and AWS credentials

4. **Deploy agent (for run_demo.py):**
   ```bash
   agentcore deploy
   ```

## Troubleshooting

### "command not found" or "No module named..."

**You forgot to activate the virtual environment!**

```bash
source .venv/bin/activate
```

Look for `(.venv)` at the start of your prompt. If you don't see it, the environment isn't active.

### "No module named 'aws_mcp_tools'"

This means the script can't find the source modules. Make sure:
- You're running from the project root: `python scripts/cleanup_demo.py`
- The `src/` directory exists with the MCP tool modules
- Your virtual environment is activated: `source .venv/bin/activate`

### "agentcore command not found"

Install the AgentCore CLI:
```bash
pip install agentcore
```

### "AWS MCP tools not available"

Make sure:
- MCP servers are configured in `.bedrock_agentcore.yaml`
- AWS credentials are in `.env`
- Agent is deployed: `agentcore deploy`

### "Could not find 'AWS - Delete VM' job template"

Make sure:
- AAP credentials are in `.env`
- Job template exists in AAP
- Ansible MCP server is running

## Architecture

```
scripts/
├── run_demo.py       → Calls AgentCore agent (no local imports)
└── cleanup_demo.py   → Uses MCP tools directly (imports from src/)
```

**run_demo.py** is simple - it just calls the deployed agent via CLI.

**cleanup_demo.py** needs direct access to MCP tools because it performs cleanup operations that aren't part of the agent's workflow.

## Related Documentation

- [Main README](../README.md) - Complete documentation with command cheat sheet
- [Architecture](../docs/ARCHITECTURE.md) - System design
- [Code Walkthrough](../docs/CODE_WALKTHROUGH.md) - Source code guide
- [Demo Talking Points](../docs/DEMO_TALKING_POINTS.md) - Presentation guide
- [Reflection Explained](../docs/REFLECTION_EXPLAINED.md) - How reflection works
