"""
mcp.py

Version : 1.6.0
Author  : aumezawa
"""

from typing import Literal
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import Connection, SSEConnection, StreamableHttpConnection


class McpClient:
    """MCP Client Class."""

    def __init__(
        self,
        name: str,
        server_url: str,
        transport: Literal["sse", "streamable_http"] = "streamable_http",
        api_token: str | None = None,
    ) -> None:
        """Initialize MCP Server."""
        self.name = name
        self.server_url = server_url
        self.transport = transport
        self.api_token = api_token

    async def get_tools(self) -> list[BaseTool]:
        """Get tools on MCP server."""
        headers = {}
        if self.api_token is not None:
            headers["Authorization"] = f"Bearer {self.api_token}"

        connection: Connection
        if self.transport == "sse":
            connection = SSEConnection(url=self.server_url, transport=self.transport, headers=headers)
        elif self.transport == "streamable_http":
            connection = StreamableHttpConnection(url=self.server_url, transport=self.transport, headers=headers)
        else:
            msg = "transport must be 'sse' or 'streamable_http'."
            raise ValueError(msg)

        connections: dict[str, Connection] = {}
        connections[self.name] = connection
        client = MultiServerMCPClient(connections)

        return await client.get_tools()
