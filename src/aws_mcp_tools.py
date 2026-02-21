"""
AWS MCP Tools Integration for LangGraph

Uses HTTP streaming to connect to the AWS MCP server.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from oauth_manager import OAuthTokenManager, get_oauth_config


class AWSMCPToolWrapper(BaseTool):
    """Wrapper to make AWS MCP tools compatible with LangGraph"""
    
    mcp_tool_name: str = Field(description="Original MCP tool name")
    token_manager: OAuthTokenManager = Field(description="OAuth token manager")
    mcp_input_schema: Dict[str, Any] = Field(description="MCP tool input schema")
    
    def __init__(self, mcp_tool_name: str, mcp_tool_info: Dict[str, Any], token_manager: OAuthTokenManager):
        # Extract input schema
        input_schema = mcp_tool_info.get("inputSchema", {})
        
        # Create args_schema dynamically from MCP input schema
        from pydantic import create_model
        
        # Build field definitions for Pydantic model
        field_definitions = {}
        properties = input_schema.get("properties", {})
        required_fields = input_schema.get("required", [])
        
        for field_name, field_info in properties.items():
            field_type = field_info.get("type", "string")
            field_desc = field_info.get("description", "")
            is_required = field_name in required_fields
            
            # Map JSON schema types to Python types
            if field_type == "string":
                python_type = str
            elif field_type == "integer":
                python_type = int
            elif field_type == "number":
                python_type = float
            elif field_type == "boolean":
                python_type = bool
            else:
                python_type = str  # Default to string
            
            # Make optional if not required
            if not is_required:
                from typing import Optional
                python_type = Optional[python_type]
                field_definitions[field_name] = (python_type, Field(default=None, description=field_desc))
            else:
                field_definitions[field_name] = (python_type, Field(description=field_desc))
        
        # Create dynamic Pydantic model for args
        if field_definitions:
            ArgsSchema = create_model(f"{mcp_tool_name}_args", **field_definitions)
        else:
            ArgsSchema = None
        
        # Initialize parent class with args_schema
        super().__init__(
            name=f"aws_{mcp_tool_name}",
            description=mcp_tool_info.get("description", f"Execute {mcp_tool_name} via aws-mcp"),
            args_schema=ArgsSchema,
            mcp_tool_name=mcp_tool_name,
            token_manager=token_manager,
            mcp_input_schema=input_schema
        )
    
    def _run(self, **kwargs) -> str:
        """Execute the MCP tool synchronously"""
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        """Execute the MCP tool asynchronously via HTTP streaming"""
        try:
            # Get fresh token
            token = self.token_manager.get_token()
            
            # Get AWS MCP server URL from environment or Parameter Store
            mcp_server_url = os.getenv("AWS_MCP_SERVER_URL")
            if not mcp_server_url:
                # Try to get from Parameter Store
                try:
                    import boto3
                    ssm = boto3.client('ssm', region_name='us-east-1')
                    mcp_server_url = ssm.get_parameter(Name='/infragenie/oauth/aws_server_url')['Parameter']['Value']
                except Exception as e:
                    return f"Error: AWS_MCP_SERVER_URL environment variable not set and failed to load from Parameter Store: {e}"
            
            # Use HTTP streaming
            import httpx
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Initialize session
                async with client.stream(
                    "POST",
                    mcp_server_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "clientInfo": {"name": "infragenie-langgraph-aws", "version": "1.0.0"}
                        }
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    }
                ) as response:
                    
                    print(f"AWS MCP Initialize Response Status: {response.status_code}")
                    
                    # Extract session ID from headers
                    session_id = response.headers.get('mcp-session-id')
                    if not session_id:
                        return f"Failed to get session ID from AWS MCP server. Status: {response.status_code}"
                    
                    print(f"Got AWS MCP session ID: {session_id}")
                    
                    # Read the initialize response stream
                    async for chunk in response.aiter_text():
                        pass  # Process initialize response if needed
                
                # Send initialized notification (required by MCP protocol)
                async with client.stream(
                    "POST",
                    mcp_server_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                        "params": {}
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                        "mcp-session-id": session_id
                    }
                ) as response:
                    print(f"AWS MCP initialized notification sent: {response.status_code}")
                    # Read any response
                    async for chunk in response.aiter_text():
                        pass
                
                # Make the tool call
                async with client.stream(
                    "POST",
                    mcp_server_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": self.mcp_tool_name,
                            "arguments": kwargs
                        }
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                        "mcp-session-id": session_id
                    }
                ) as response:
                    
                    print(f"AWS MCP Tool Call Response Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        # Read the streaming response
                        full_response = ""
                        async for chunk in response.aiter_text():
                            full_response += chunk
                        
                        print(f"AWS MCP response: {full_response[:500]}...")
                        
                        # Parse SSE format
                        if full_response.startswith("event: message\ndata: "):
                            json_start = full_response.find("data: ") + 6
                            json_end = full_response.find("\n\n", json_start)
                            if json_end == -1:
                                json_end = len(full_response)
                            json_str = full_response[json_start:json_end].strip()
                            
                            try:
                                result = json.loads(json_str)
                                
                                if "result" in result and "content" in result["result"]:
                                    content_parts = []
                                    for content in result["result"]["content"]:
                                        if isinstance(content, dict) and "text" in content:
                                            # Parse and format JSON content
                                            try:
                                                parsed_data = json.loads(content["text"])
                                                formatted_output = json.dumps(parsed_data, indent=2)
                                                content_parts.append(formatted_output)
                                            except json.JSONDecodeError:
                                                # If not JSON, clean up the text
                                                clean_text = content["text"]
                                                clean_text = clean_text.replace('\\n', '\n')
                                                clean_text = clean_text.replace('\\"', '"')
                                                content_parts.append(clean_text)
                                        else:
                                            content_parts.append(str(content))
                                    return "\n".join(content_parts)
                                else:
                                    return str(result.get("result", result))
                            except Exception as json_error:
                                print(f"JSON parsing error: {json_error}")
                                return f"Response received but couldn't parse: {full_response[:200]}"
                        else:
                            return f"Unexpected response format: {full_response[:200]}"
                    else:
                        error_text = ""
                        async for chunk in response.aiter_text():
                            error_text += chunk
                        return f"HTTP error {response.status_code}: {error_text[:200]}"
                        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Error executing AWS MCP tool {self.mcp_tool_name}: {str(e)}"


class AWSMCPToolsManager:
    """Manages AWS MCP tools connection"""
    
    def __init__(self):
        self.token_manager: Optional[OAuthTokenManager] = None
        self.tools: List[AWSMCPToolWrapper] = []
    
    async def initialize(self) -> List[AWSMCPToolWrapper]:
        """Initialize AWS MCP connection and load available tools"""
        try:
            print("Initializing AWS MCP connection...")
            
            # Get OAuth configuration (same as Ansible)
            client_id, client_secret, issuer_url, audience = get_oauth_config()
            self.token_manager = OAuthTokenManager(client_id, client_secret, issuer_url, audience)
            
            # Get initial token
            token = self.token_manager.get_token()
            print("AWS MCP OAuth token obtained successfully")
            
            # Get AWS MCP server URL
            mcp_server_url = os.getenv("AWS_MCP_SERVER_URL")
            if not mcp_server_url:
                # Try to get from Parameter Store
                try:
                    import boto3
                    ssm = boto3.client('ssm', region_name='us-east-1')
                    mcp_server_url = ssm.get_parameter(Name='/infragenie/oauth/aws_server_url')['Parameter']['Value']
                except Exception as e:
                    print(f"Error: AWS_MCP_SERVER_URL not set and failed to load from Parameter Store: {e}")
                    return []
            
            print(f"AWS MCP Server URL: {mcp_server_url}")
            
            # Use HTTP streaming to discover tools
            import httpx
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Initialize session
                async with client.stream(
                    "POST",
                    mcp_server_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "clientInfo": {"name": "infragenie-langgraph-aws", "version": "1.0.0"}
                        }
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    }
                ) as response:
                    session_id = response.headers.get('mcp-session-id')
                    if not session_id:
                        print("Failed to get AWS MCP session ID")
                        return []
                    
                    print(f"AWS MCP session initialized: {session_id}")
                    
                    # Read initialize response
                    async for chunk in response.aiter_text():
                        pass
                
                # Send initialized notification (REQUIRED by MCP protocol)
                async with client.stream(
                    "POST",
                    mcp_server_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                        "params": {}
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                        "mcp-session-id": session_id
                    }
                ) as response:
                    print(f"AWS MCP initialized notification sent")
                    async for chunk in response.aiter_text():
                        pass
                
                # Now request tools list
                async with client.stream(
                    "POST",
                    mcp_server_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {}
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                        "mcp-session-id": session_id
                    }
                ) as response:
                    full_response = ""
                    async for chunk in response.aiter_text():
                        full_response += chunk
                    
                    # Parse tools list
                    if full_response.startswith("event: message\ndata: "):
                        json_start = full_response.find("data: ") + 6
                        json_end = full_response.find("\n\n", json_start)
                        if json_end == -1:
                            json_end = len(full_response)
                        json_str = full_response[json_start:json_end].strip()
                        
                        result = json.loads(json_str)
                        
                        if "result" in result and "tools" in result["result"]:
                            tools_list = result["result"]["tools"]
                            print(f"Discovered {len(tools_list)} AWS MCP tools from server")
                            
                            # Create LangGraph-compatible tools
                            self.tools = []
                            for tool_info in tools_list:
                                wrapper = AWSMCPToolWrapper(
                                    mcp_tool_name=tool_info["name"],
                                    mcp_tool_info=tool_info,
                                    token_manager=self.token_manager
                                )
                                self.tools.append(wrapper)
                            
                            print(f"Successfully initialized {len(self.tools)} AWS MCP tools")
                            return self.tools
                        else:
                            print(f"No tools found in AWS MCP response: {result}")
                            return []
            
        except Exception as e:
            print(f"Failed to initialize AWS MCP tools: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def refresh_token_if_needed(self):
        """Refresh OAuth token if needed"""
        if self.token_manager:
            try:
                # This will refresh if needed
                self.token_manager.get_token()
            except Exception as e:
                print(f"Failed to refresh AWS MCP token: {e}")


# Global instance
aws_mcp_manager = AWSMCPToolsManager()


async def get_aws_mcp_tools() -> List[AWSMCPToolWrapper]:
    """Get initialized AWS MCP tools for use in LangGraph"""
    if not aws_mcp_manager.tools:
        await aws_mcp_manager.initialize()
    return aws_mcp_manager.tools


def get_aws_mcp_tools_sync() -> List[AWSMCPToolWrapper]:
    """Synchronous wrapper to get AWS MCP tools"""
    return asyncio.run(get_aws_mcp_tools())
