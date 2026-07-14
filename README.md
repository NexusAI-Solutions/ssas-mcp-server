# SSAS MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that connects AI agents to **SQL Server Analysis Services (SSAS)**. It lets tools like GitHub Copilot, Claude (via Codex or Claude Code), and other MCP clients run DAX and MDX queries, explore models, and list measures, all through natural language.

> **Windows only** \
> SSAS uses the ADOMD.NET client library, which requires .NET Framework on Windows.

## Features

| Tool              | Description                                              |
| ----------------- | -------------------------------------------------------- |
| `execute_query`   | Run any DAX (`EVALUATE ...`) or MDX (`SELECT ...`) query |
| `list_catalogs`   | List all databases on the SSAS instance                  |
| `list_tables`     | List tables, dimensions, and measure groups               |
| `list_columns`    | List columns for a specific table                        |
| `list_measures`   | List all visible measures with their DAX expressions     |
| `describe_model`  | High-level summary: tables, measures, metadata           |

## Prerequisites

1. **Python 3.10+**
2. **ADOMD.NET client library** \
   The DLL `Microsoft.AnalysisServices.AdomdClient.dll` must be present on the machine. It ships with any of these:
   - SQL Server Management Studio (SSMS)
   - Power BI Desktop
   - The standalone [AMO/ADOMD client libraries](https://learn.microsoft.com/en-us/analysis-services/client-libraries)

   The server auto-detects common install locations. If your DLL is elsewhere, set the `ADOMD_DLL_PATH` environment variable to the folder containing it.

## Installation

```bash
pip install ssas-mcp-server
```

After installation, the server can be started with:

```bash
ssas-mcp-server
```

Or install from source:

```bash
git clone https://github.com/NexusAI-Solutions/ssas-mcp-server.git
cd ssas-mcp-server
pip install .
```

## Configuration

The server is configured through environment variables:

| Variable                 | Required | Description                                                        |
| ------------------------ | -------- | ------------------------------------------------------------------ |
| `SSAS_SERVER`            | Yes      | SSAS instance name (e.g. `SERVER\INSTANCE`)                             |
| `SSAS_DATABASE`          | Yes      | Database / catalog name                                            |
| `SSAS_PROVIDER`          | No       | OLAP provider (default: `MSOLAP`)                                 |
| `SSAS_CONNECTION_STRING` | No       | Full ADOMD connection string (overrides server/database/provider)  |
| `ADOMD_DLL_PATH`         | No       | Explicit path to the folder containing the ADOMD.NET DLL           |

## Usage

### Run directly

```bash
set SSAS_SERVER=SERVER\INSTANCE
set SSAS_DATABASE=My Cube
ssas-mcp-server
```

The server starts in stdio mode and waits for an MCP client to connect.

You can also run it as a Python module:

```bash
python -m ssas_mcp_server
```

### VS Code / Codex

Add this to your `.vscode/mcp.json`:

```json
{
  "servers": {
    "ssas": {
      "command": "ssas-mcp-server",
      "env": {
        "SSAS_SERVER": "SERVER\\INSTANCE",
        "SSAS_DATABASE": "My Cube"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add ssas -- ssas-mcp-server
```

Then set the environment variables in your shell before starting Claude Code, or pass them inline.

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ssas": {
      "command": "ssas-mcp-server",
      "env": {
        "SSAS_SERVER": "SERVER\\INSTANCE",
        "SSAS_DATABASE": "My Cube"
      }
    }
  }
}
```

## Example queries

Once connected, you can ask your AI assistant things like:

- "List all tables in the SSAS model"
- "Show me the measures and their DAX expressions"
- "Run this DAX query: `EVALUATE TOPN(10, 'Sales', [Revenue], DESC)`"
- "Describe the data model"
- "What columns does the Customers table have?"

## Troubleshooting

### `Could not load file or assembly 'Microsoft.AnalysisServices.AdomdClient'`

The ADOMD.NET DLL was not found. Solutions:

1. **Install SSMS, Power BI Desktop, or the standalone AMO client libraries.**
2. **Set `ADOMD_DLL_PATH`** to the folder containing `Microsoft.AnalysisServices.AdomdClient.dll`.

To find the DLL on your system:

```cmd
where /r "C:\Program Files" Microsoft.AnalysisServices.AdomdClient.dll
```

### `Server is not found or not accessible`

- Verify the server name matches exactly what works in SSMS or Power BI.
- For named instances, use the `SERVER\INSTANCE` format.
- Make sure the SQL Server Browser service is running if you are connecting by instance name.

## License

MIT