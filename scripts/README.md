# InfraGenie Scripts

## The Only Script You Need

### run_demo_interactive.py

**This is the ONLY script you run.** It handles everything:
- Interactive menu with demo options
- Two-level approval (plan approval + remediation approval)
- Command-line options for automation
- Natural language prompts

**Usage:**
```bash
# Interactive menu (recommended)
python scripts/run_demo_interactive.py

# Direct commands
python scripts/run_demo_interactive.py --infrastructure    # Infrastructure lifecycle demo
python scripts/run_demo_interactive.py --security          # Security scan demo

# Natural language prompts
python scripts/run_demo_interactive.py --prompt "provision an ec2 vm and an s3 bucket"
python scripts/run_demo_interactive.py --prompt "scan my s3 buckets for security issues"

# Get help
python scripts/run_demo_interactive.py --help
```

**Requirements:**
- Virtual environment activated (`source .venv/bin/activate`)
- AgentCore CLI installed (`pip install agentcore`)
- Agent deployed to AgentCore (`agentcore deploy`)
- AWS credentials configured

**What it does:**
1. **Step 1: Planning** - Creates execution plan using system prompt-based planner
2. **Approval Gate #1** - Prompts for plan approval (strategic decision)
3. **Step 2: Execution** - Runs multi-agent workflow
4. **Approval Gate #2** - Prompts for remediation approval (tactical decision)
5. **Step 3: Completion** - Applies remediation and generates insights

## Setup

**IMPORTANT: Always activate the virtual environment first!**

```bash
source .venv/bin/activate
```

You'll see `(.venv)` in your prompt when activated.

**Steps:**

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

4. **Deploy agent:**
   ```bash
   agentcore deploy
   ```

5. **Run the demo:**
   ```bash
   python scripts/run_demo_interactive.py
   ```

## Troubleshooting

### "command not found" or "No module named..."

**You forgot to activate the virtual environment!**

```bash
source .venv/bin/activate
```

Look for `(.venv)` at the start of your prompt. If you don't see it, the environment isn't active.

### "agentcore command not found"

Install the AgentCore CLI:
```bash
pip install agentcore
```

### Script won't start

Make sure:
- Virtual environment is activated: `source .venv/bin/activate`
- You're running from the project root: `python scripts/run_demo_interactive.py`
- Agent is deployed: `agentcore deploy`

### "AWS credentials expired"

Refresh your AWS credentials:
```bash
aws sso login
```

### Demo times out

The demo creates real infrastructure which takes time:
- Planning: ~10 seconds
- Execution: 3-10 minutes (EC2 provisioning is slow)
- Be patient and wait for prompts

## How It Works

```
User runs: python scripts/run_demo_interactive.py
    ↓
Script calls: agentcore invoke (deployed agent in AWS)
    ↓
Agent executes: Multi-agent workflow with MCP tools
    ↓
Script handles: Two approval prompts (plan + remediation)
    ↓
Final response: Execution log + summary
```

**Simple and clean** - just one script to run!

## Command Examples

```bash
# Most common: Interactive menu
python scripts/run_demo_interactive.py

# Infrastructure lifecycle demo
python scripts/run_demo_interactive.py --infrastructure

# Security scan demo
python scripts/run_demo_interactive.py --security

# Natural language (administrators speak naturally!)
python scripts/run_demo_interactive.py --prompt "provision an ec2 vm and an s3 bucket"
python scripts/run_demo_interactive.py --prompt "scan my buckets for security issues"
```

## Related Documentation

- [Main README](../README.md) - Complete documentation with command cheat sheet
- [Architecture](../docs/ARCHITECTURE.md) - System design
- [Code Walkthrough](../docs/CODE_WALKTHROUGH.md) - Source code guide
- [Demo Talking Points](../docs/DEMO_TALKING_POINTS.md) - Presentation guide
