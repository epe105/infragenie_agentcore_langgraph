"""
Simple MCP Tools Integration for LangGraph

Uses HTTP streaming to connect to the MCP server and properly format responses.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from oauth_manager import OAuthTokenManager, get_oauth_config


class MCPToolWrapper(BaseTool):
    """Wrapper to make MCP tools compatible with LangGraph"""
    
    mcp_tool_name: str = Field(description="Original MCP tool name")
    token_manager: OAuthTokenManager = Field(description="OAuth token manager")
    
    def __init__(self, mcp_tool_name: str, mcp_tool_info: Dict[str, Any], token_manager: OAuthTokenManager):
        # Initialize parent class first with required fields
        super().__init__(
            name=f"ansible_{mcp_tool_name}",
            description=mcp_tool_info.get("description", f"Execute {mcp_tool_name} via ansible-mcp"),
            mcp_tool_name=mcp_tool_name,
            token_manager=token_manager
        )
    
    def _run(self, **kwargs) -> str:
        """Execute the MCP tool synchronously"""
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        """Execute the MCP tool asynchronously via HTTP streaming"""
        try:
            # Get fresh token
            token = self.token_manager.get_token()
            
            # Get MCP server URL from environment
            mcp_server_url = os.getenv("ANSIBLE_MCP_SERVER_URL")
            if not mcp_server_url:
                return "Error: ANSIBLE_MCP_SERVER_URL environment variable not set"
            
            # Use HTTP streaming like the Strands version
            import httpx
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Use streaming connection
                async with client.stream(
                    "POST",
                    mcp_server_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "clientInfo": {
                                "name": "infragenie-langgraph",
                                "version": "1.0.0"
                            }
                        }
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    }
                ) as response:
                    
                    print(f"Streaming Initialize Response Status: {response.status_code}")
                    
                    # Extract session ID from headers
                    session_id = response.headers.get('mcp-session-id')
                    if not session_id:
                        return f"Failed to get session ID from streaming response. Status: {response.status_code}"
                    
                    print(f"Got streaming session ID: {session_id}")
                    
                    # Read the initialize response stream
                    async for chunk in response.aiter_text():
                        print(f"Initialize stream chunk: {chunk[:100]}...")
                        # Process initialize response if needed
                        pass
                
                # Now make the tool call with streaming
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
                    
                    print(f"Streaming Tool Call Response Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        # Read the streaming response
                        full_response = ""
                        async for chunk in response.aiter_text():
                            full_response += chunk
                        
                        print(f"Full streaming response: {full_response[:500]}...")
                        
                        # Parse SSE format
                        if full_response.startswith("event: message\ndata: "):
                            json_start = full_response.find("data: ") + 6
                            json_end = full_response.find("\n\n", json_start)
                            if json_end == -1:
                                json_end = len(full_response)
                            json_str = full_response[json_start:json_end].strip()
                            
                            try:
                                result = json.loads(json_str)
                                print(f"Parsed streaming JSON result: {result}")
                                
                                if "result" in result and "content" in result["result"]:
                                    content_parts = []
                                    for content in result["result"]["content"]:
                                        if isinstance(content, dict) and "text" in content:
                                            # Parse the JSON content and format it nicely
                                            try:
                                                parsed_data = json.loads(content["text"])
                                                
                                                # Format the inventory data nicely
                                                if "results" in parsed_data and isinstance(parsed_data["results"], list):
                                                    formatted_output = f"Found {parsed_data.get('count', len(parsed_data['results']))} inventories:\n\n"
                                                    
                                                    for i, inventory in enumerate(parsed_data["results"], 1):
                                                        formatted_output += f"{i}. {inventory.get('name', 'Unknown')} (ID: {inventory.get('id', 'N/A')})\n"
                                                        
                                                        if inventory.get('description'):
                                                            formatted_output += f"   Description: {inventory['description']}\n"
                                                        
                                                        formatted_output += f"   Organization: {inventory.get('summary_fields', {}).get('organization', {}).get('name', 'Unknown')}\n"
                                                        formatted_output += f"   Total Hosts: {inventory.get('total_hosts', 0)}\n"
                                                        
                                                        if inventory.get('has_active_failures'):
                                                            formatted_output += f"   Hosts with Failures: {inventory.get('hosts_with_active_failures', 0)}\n"
                                                        
                                                        formatted_output += f"   Total Groups: {inventory.get('total_groups', 0)}\n"
                                                        formatted_output += f"   Has Inventory Sources: {'Yes' if inventory.get('has_inventory_sources') else 'No'}\n"
                                                        
                                                        if inventory.get('has_inventory_sources'):
                                                            formatted_output += f"   Total Inventory Sources: {inventory.get('total_inventory_sources', 0)}\n"
                                                            if inventory.get('inventory_sources_with_failures', 0) > 0:
                                                                formatted_output += f"   Inventory Sources with Failures: {inventory.get('inventory_sources_with_failures', 0)}\n"
                                                        
                                                        formatted_output += f"   Created: {inventory.get('created', 'Unknown')}\n"
                                                        formatted_output += f"   Modified: {inventory.get('modified', 'Unknown')}\n\n"
                                                    
                                                    content_parts.append(formatted_output)
                                                else:
                                                    # For any other JSON data, clean it up and make it readable
                                                    clean_text = json.dumps(parsed_data, indent=2)
                                                    # Remove escaped newlines and quotes
                                                    clean_text = clean_text.replace('\\n', '\n').replace('\\"', '"')
                                                    content_parts.append(clean_text)
                                            except json.JSONDecodeError:
                                                # If it's not JSON, clean up the raw text
                                                clean_text = content["text"]
                                                # Remove escaped characters that make text hard to read
                                                clean_text = clean_text.replace('\\n', '\n')
                                                clean_text = clean_text.replace('\\"', '"')
                                                clean_text = clean_text.replace('\\/', '/')
                                                clean_text = clean_text.replace('\\\\', '\\')
                                                content_parts.append(clean_text)
                                        else:
                                            content_parts.append(str(content))
                                    return "\n".join(content_parts)
                                else:
                                    return str(result.get("result", result))
                            except Exception as json_error:
                                print(f"JSON parsing error in streaming: {json_error}")
                                return f"Streaming response received but couldn't parse: {full_response[:200]}"
                        else:
                            return f"Unexpected streaming response format: {full_response[:200]}"
                    else:
                        error_text = ""
                        async for chunk in response.aiter_text():
                            error_text += chunk
                        return f"Streaming HTTP error {response.status_code}: {error_text[:200]}"
                        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Error in streaming execution of {self.mcp_tool_name}: {str(e)}"


class MCPToolsManager:
    """Manages MCP tools connection and provides LangGraph-compatible tools"""
    
    def __init__(self):
        self.token_manager: Optional[OAuthTokenManager] = None
        self.tools: List[MCPToolWrapper] = []
    
    async def initialize(self) -> List[MCPToolWrapper]:
        """Initialize MCP connection and load available tools"""
        try:
            print("Initializing MCP connection...")
            
            # Get OAuth configuration
            client_id, client_secret, issuer_url, audience = get_oauth_config()
            self.token_manager = OAuthTokenManager(client_id, client_secret, issuer_url, audience)
            
            # Get initial token to verify connectivity
            token = self.token_manager.get_token()
            print("OAuth token obtained successfully")
            
            # Create the known tools with realistic descriptions
            known_tools = [
                {"name": "list_inventories", "description": "List all available inventories in Ansible Automation Platform"},
                {"name": "get_inventory", "description": "Get detailed information about a specific inventory"},
                {"name": "run_job", "description": "Execute an Ansible job template"},
                {"name": "job_status", "description": "Check the status of a running or completed job"},
                {"name": "job_logs", "description": "Retrieve logs from an Ansible job execution"},
                {"name": "create_project", "description": "Create a new project in Ansible Automation Platform"},
                {"name": "create_job_template", "description": "Create a new job template"},
                {"name": "list_inventory_sources", "description": "List all inventory sources"},
                {"name": "get_inventory_source", "description": "Get details of a specific inventory source"},
                {"name": "create_inventory_source", "description": "Create a new inventory source"},
                {"name": "update_inventory_source", "description": "Update an existing inventory source"},
                {"name": "delete_inventory_source", "description": "Delete an inventory source"},
                {"name": "sync_inventory_source", "description": "Synchronize an inventory source"},
                {"name": "create_inventory", "description": "Create a new inventory"},
                {"name": "delete_inventory", "description": "Delete an existing inventory"},
                {"name": "list_job_templates", "description": "List all available job templates"},
                {"name": "get_job_template", "description": "Get details of a specific job template"},
                {"name": "list_jobs", "description": "List all jobs in the system"},
                {"name": "list_recent_jobs", "description": "List recently executed jobs"}
            ]
            
            print(f"Creating {len(known_tools)} MCP tools")
            
            # Create LangGraph-compatible tools
            self.tools = []
            for tool_info in known_tools:
                wrapper = MCPToolWrapper(
                    mcp_tool_name=tool_info["name"],
                    mcp_tool_info={"description": tool_info["description"]},
                    token_manager=self.token_manager
                )
                self.tools.append(wrapper)
            
            print(f"Successfully initialized {len(self.tools)} MCP tools")
            return self.tools
            
        except Exception as e:
            print(f"Failed to initialize MCP tools: {e}")
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
                print(f"Failed to refresh token: {e}")


# Global instance
mcp_manager = MCPToolsManager()


async def get_mcp_tools() -> List[MCPToolWrapper]:
    """Get initialized MCP tools for use in LangGraph"""
    if not mcp_manager.tools:
        await mcp_manager.initialize()
    return mcp_manager.tools


def get_mcp_tools_sync() -> List[MCPToolWrapper]:
    """Synchronous wrapper to get MCP tools"""
    return asyncio.run(get_mcp_tools())