# InfraGenie LangGraph Agent

Successfully replicated InfraGenie agent functionality using LangGraph instead of Strands.

## ✅ What Works

- **MCP Integration**: Full HTTP streaming connection to ansible-mcp server
- **OAuth Authentication**: Connects using credentials from AWS Parameter Store
- **Real Data**: Retrieves actual inventory data from Ansible Automation Platform
- **19 MCP Tools**: All tools loaded and functional
- **Fast Response**: ~10-15 second response times
- **Session Management**: Proper MCP protocol implementation
- **Structured Responses**: Professional formatting with emojis and organization

## 🏗️ Project Structure

### Core Files
- **`agentcore_main.py`** - AWS AgentCore entry point
- **`infragenie_langgraph_agent.py`** - Main LangGraph agent implementation
- **`mcp_tools.py`** - HTTP streaming MCP client for Ansible tools
- **`oauth_manager.py`** - OAuth token management for MCP authentication
- **`system_prompt.py`** - Agent identity and response formatting instructions

### Configuration Files
- **`.bedrock_agentcore.yaml`** - AgentCore deployment configuration
- **`requirements.txt`** - Python dependencies
- **`.env`** - Environment variables (OAuth credentials)

### Documentation
- **`README.md`** - This file
- **`.env.example`** - Example environment configuration

## 🔧 Key Features

1. **HTTP Streaming**: Uses proper MCP streaming protocol like Strands
2. **Session Management**: Maintains MCP sessions across tool calls
3. **Error Handling**: Graceful fallbacks and detailed logging
4. **Data Processing**: Parses and formats JSON responses from MCP server
5. **OAuth Integration**: Automatic token refresh from AWS Parameter Store
6. **Professional Responses**: Structured formatting with emojis and clear organization

## 📊 Current Status

**WORKING**: Agent successfully connects to ansible-mcp server and retrieves real inventory data with professional formatting.

## 🚀 Deployment

```bash
agentcore deploy
```

## 🧪 Testing

```bash
agentcore invoke '{"prompt": "Show me my ansible inventory overview"}'
agentcore invoke '{"prompt": "How many inventories do I have?"}'
```

## 📝 Configuration Notes

- OAuth credentials stored in Parameter Store at `/infragenie/oauth/*`
