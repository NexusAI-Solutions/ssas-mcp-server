"""Command-line entry point for the SSAS MCP server."""

from ssas_mcp_server.server import mcp


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
