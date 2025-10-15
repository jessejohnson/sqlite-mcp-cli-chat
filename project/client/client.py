import asyncio
import textwrap
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .llm import get_llm_client
from .messages import UserMessage
from util import slog

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: ClientSession
        self.exit_stack = AsyncExitStack()
        self.llm = get_llm_client()
        self.messages = []
        self.available_tools = []
        self.available_resources = []

    async def connect_to_server(self, server_script_path: str):
        """Connect to the server """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a Python or JS file")
        
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

    async def get_tools(self):
        """Get list of MCP tools available to the client"""

        # List available tools
        response = await self.session.list_tools()
        slog.debug(response)
        tools = response.tools
        self.available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]
        slog.info(f"Connected to server with {len(self.available_tools)} tools: {[tool.name for tool in tools]}")

    async def get_resources(self):
        """Get list of resources available to the client"""

        # List available resources
        response = await self.session.list_resources()
        resources = response.resources
        self.available_resources = [{
            "name": r.name,
            "title": r.title,
            "uri": str(r.uri),
            "description": r.description
        } for r in response.resources]
        slog.info(f"\nConnected to server with {len(self.available_resources)} resources: {[r.name for r in resources]}")

    async def handle_query(self, query: str) -> str:
        """Process a query from our server"""

        self.messages.append(
            UserMessage(content=query, type="text")
        )
        slog.debug(f"self.messages: {self.messages}")

        while True:
            response = self.llm.send(self.messages, self.available_tools)
            slog.debug(f"response: {response}")
            for m in response.messages:
                print(f"{m.as_chat()}")
            self.messages.extend(response.messages)
            if response.should_use_tool:
                if response.tool_name is not None and response.tool_input is not None:
                    tool_result = await self.session.call_tool(
                        response.tool_name,
                        response.tool_input
                    )
                    slog.debug(f"tool_result is {tool_result}")
                    user_tool_messages = self.llm.read_tool_result(
                        response.tool_name,
                        response.tool_input,
                        tool_result
                    )
                    for m in user_tool_messages:
                        print(f"{textwrap.shorten(m.as_chat(), width=90, placeholder='...')}")
                    self.messages.extend(user_tool_messages)       
            else:
                return "<<<"
        return "<<<"
    
    async def chat_loop(self):
        """Run interactive chat loop!"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit/q' to exit.")
        while True:
            try:
                query = input("Query: ").strip()
                if query.lower() == 'quit' or query.lower() == 'q':
                    break
                response = await self.handle_query(query)
                print("\n" + response)
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.exit_stack.aclose()