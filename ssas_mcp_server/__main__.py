"""Allow running the server with: python -m ssas_mcp_server"""

from ssas_mcp_server.server import mcp

mcp.run(transport="stdio")
