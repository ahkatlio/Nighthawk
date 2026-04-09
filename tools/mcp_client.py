import asyncio
from typing import Any, Dict, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
import os
import subprocess
from pathlib import Path

import anyio

class MCPToolClient:
    def __init__(self):
        mcp_base = Path(__file__).parent / "mcp_server"
        self.flask_server_path = mcp_base / "server.py"
        self.mcp_client_path = mcp_base / "client.py"
        
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(self.mcp_client_path)],
            env=None
        )
        self.client_context = None
        self.session = None
        self.flask_process = None
        self.mcp_task = None
        
    async def _run_mcp_client(self):
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.session = session
                    self._ready.set()
                    await asyncio.Future()  # block forever
        except asyncio.CancelledError:
            self.session = None

    async def connect(self):
        # Start the local Flask Kali Server in background
        if not self.flask_process:
            self.flask_process = subprocess.Popen(
                [sys.executable, str(self.flask_server_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # Give it a second to start up
            await asyncio.sleep(1.5)
            
        try:
            self._ready = asyncio.Event()
            self.mcp_task = asyncio.create_task(self._run_mcp_client())
            await self._ready.wait()
        except BaseExceptionGroup as eg:
            import logging
            logging.error(f"Error starting client context: {eg}")
            raise

    async def get_tools(self) -> List[Dict[str, Any]]:
        if not self.session:
            await self.connect()
        response = await self.session.list_tools()
        tools = []
        for tool in response.tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })
        return tools

    async def execute_tool(self, name: str, arguments: dict) -> str:
        if not self.session:
            await self.connect()
        result = await self.session.call_tool(name, arguments)
        output = ""
        for content in result.content:
            if content.type == "text":
                output += content.text + "\n"
        return output
        
    async def close(self):
        if self.mcp_task:
            self.mcp_task.cancel()
        if self.flask_process:
            self.flask_process.terminate()
            self.flask_process.wait(timeout=2)

