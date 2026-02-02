"""
InfraGenie AgentCore Implementation using LangGraph

AgentCore-compatible version that uses AWS Bedrock models instead of external APIs.
This provides the same functionality as the Strands version but with LangGraph workflows.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_aws import ChatBedrock
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict, Annotated
from system_prompt import INFRAGENIE_SYSTEM_PROMPT
from mcp_tools import get_mcp_tools, mcp_manager


class AgentState(TypedDict):
    """State for the InfraGenie agent"""
    messages: Annotated[List[Any], add_messages]
    tools_available: bool


class InfraGenieAgentCore:
    """InfraGenie agent implementation for AWS AgentCore using LangGraph"""
    
    def __init__(self):
        self.llm = self._initialize_bedrock_llm()
        self.tools: List[BaseTool] = []
        self.graph = None
        self.initialized = False
    
    def _initialize_bedrock_llm(self):
        """Initialize AWS Bedrock LLM"""
        # Use Claude 3.5 Sonnet via inference profile (supported for on-demand)
        return ChatBedrock(
            model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            model_kwargs={
                "temperature": 0.1,
                "max_tokens": 4000
            }
        )
    
    async def initialize(self):
        """Initialize the agent with MCP tools and build the graph"""
        if self.initialized:
            return
        
        try:
            # Load MCP tools
            self.tools = await get_mcp_tools()
            print(f"Loaded {len(self.tools)} MCP tools")
            
            # Bind tools to LLM
            if self.tools:
                self.llm_with_tools = self.llm.bind_tools(self.tools)
            else:
                self.llm_with_tools = self.llm
            
            # Build the graph
            self._build_graph()
            self.initialized = True
            
        except Exception as e:
            print(f"Warning: Failed to initialize MCP tools: {e}")
            # Fallback to agent without tools
            self.tools = []
            self.llm_with_tools = self.llm
            self._build_graph()
            self.initialized = True
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        if self.tools:
            workflow.add_node("tools", ToolNode(self.tools))
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        if self.tools:
            workflow.add_conditional_edges(
                "agent",
                self._should_continue,
                {
                    "continue": "tools",
                    "end": END,
                }
            )
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge("agent", END)
        
        # Compile the graph
        self.graph = workflow.compile()
    
    def _agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Agent node that processes messages and decides on actions"""
        messages = state["messages"]
        
        # Add system message if not present
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            messages = [SystemMessage(content=INFRAGENIE_SYSTEM_PROMPT)] + messages
        
        # Get response from LLM
        response = self.llm_with_tools.invoke(messages)
        
        return {
            "messages": [response],
            "tools_available": len(self.tools) > 0
        }
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if we should continue to tools or end"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the last message has tool calls, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        else:
            return "end"
    
    async def process_message(self, message: str) -> str:
        """Process a user message and return the agent's response"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Refresh token if needed
            await mcp_manager.refresh_token_if_needed()
            
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=message)],
                "tools_available": len(self.tools) > 0
            }
            
            # Run the graph
            result = await self.graph.ainvoke(initial_state)
            
            # Extract the final message
            final_messages = result["messages"]
            if final_messages:
                last_message = final_messages[-1]
                if isinstance(last_message, AIMessage):
                    return last_message.content
                else:
                    return str(last_message)
            else:
                return "I apologize, but I couldn't process your request."
                
        except Exception as e:
            return f"I encountered an error while processing your request: {str(e)}"