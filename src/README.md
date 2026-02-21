# Source Code

Core agent implementation and workflow definitions.

## Files

### Entry Point
- **agentcore_main.py** - AgentCore entry point (deployed to AWS)

### Agent Core
- **infragenie_langgraph_agent.py** - Main agent class with LLM orchestration
- **system_prompt.py** - Agent system prompt configuration

### Workflows
- **infrastructure_lifecycle_demo.py** - 7-agent infrastructure lifecycle workflow
- **security_demo.py** - 5-agent security scan workflow

### Tool Integration
- **mcp_tools.py** - Ansible MCP tool wrappers
- **aws_mcp_tools.py** - AWS MCP tool wrappers
- **oauth_manager.py** - OAuth token management for MCP servers

## Architecture

```
agentcore_main.py (entry point)
    ↓
infragenie_langgraph_agent.py (agent with LLM)
    ↓
├── infrastructure_lifecycle_demo.py (7 agents)
├── security_demo.py (5 agents)
└── Tools:
    ├── mcp_tools.py (Ansible)
    └── aws_mcp_tools.py (AWS)
```

## Deployment

This entire `src/` directory gets packaged and deployed to AgentCore when you run:

```bash
agentcore deploy
```
