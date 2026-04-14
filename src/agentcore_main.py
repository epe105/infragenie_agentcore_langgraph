"""
InfraGenie AgentCore Entry Point - LangGraph Implementation

AWS AgentCore-compatible entry point that uses LangGraph instead of Strands.
This replicates the functionality of the original Strands implementation.
"""

import os
import asyncio
from typing import Dict, Any
from bedrock_agentcore import BedrockAgentCoreApp
from infragenie_langgraph_agent import InfraGenieAgentCore

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, assume environment variables are set
    pass

app = BedrockAgentCoreApp()

# Global agent instance
agent_instance = None

def get_agent():
    """Get or create the global agent instance"""
    global agent_instance
    if agent_instance is None:
        agent_instance = InfraGenieAgentCore()
    return agent_instance

@app.entrypoint
def invoke(payload):
    """InfraGenie AI agent function with ansible-mcp integration using LangGraph"""
    user_message = payload.get("prompt", "Hello! I'm InfraGenie, your agentic operations assistant. How can I help you orchestrate your infrastructure today?")
    config = payload.get("config", None)  # Extract config for thread management

    try:
        agent = get_agent()

        # Check if this is a continuation request with approval decision
        if "approval_continuation" in payload:
            continuation_data = payload["approval_continuation"]
            state = continuation_data["state"]
            approved = continuation_data["approved"]
            workflow_type = continuation_data["workflow_type"]

            # Continue from Graph 3 with approval decision
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, agent.continue_with_approval(state, approved, workflow_type))
                        result = future.result()
                else:
                    result = loop.run_until_complete(agent.continue_with_approval(state, approved, workflow_type))
            except RuntimeError:
                result = asyncio.run(agent.continue_with_approval(state, approved, workflow_type))

            return {"result": result}

        # Normal message processing
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If there's already a running loop, create a new one
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, agent.process_message(user_message, config))
                    result = future.result()
            else:
                result = loop.run_until_complete(agent.process_message(user_message, config))
        except RuntimeError:
            # No event loop, create a new one
            result = asyncio.run(agent.process_message(user_message, config))

        return {"result": result}
    except Exception as e:
        # Fallback response if agent fails
        return {
            "result": f"InfraGenie is currently initializing. Error: {str(e)}. Please ensure OAuth environment variables are configured in the AgentCore console.",
            "status": "initialization_error"
        }

if __name__ == "__main__":
    app.run()