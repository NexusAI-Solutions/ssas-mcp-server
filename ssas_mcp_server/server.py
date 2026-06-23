"""
SSAS MCP Server - Query SQL Server Analysis Services from any MCP client.

A lightweight Model Context Protocol (MCP) server that lets AI agents
query SQL Server Analysis Services (SSAS) via DAX or MDX.
"""

import json
import logging
import os
import traceback
from typing import Any

from mcp.server.fastmcp import FastMCP

from ssas_mcp_server.adomd import ensure_adomd_available

logger = logging.getLogger(__name__)

# Make sure the ADOMD.NET DLL is discoverable before pyadomd tries to load it.
ensure_adomd_available()

# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------


def _connection_string() -> str:
    """Build the ADOMD.NET connection string from environment variables."""
    explicit = os.environ.get("SSAS_CONNECTION_STRING")
    if explicit:
        return explicit

    server = os.environ.get("SSAS_SERVER", "localhost")
    database = os.environ.get("SSAS_DATABASE", "")
    provider = os.environ.get("SSAS_PROVIDER", "MSOLAP")

    parts = [f"Provider={provider}", f"Data Source={server}"]
    if database:
        parts.append(f"Initial Catalog={database}")
    return ";".join(parts) + ";"


def _execute(query: str) -> list[dict[str, Any]]:
    """Execute a DAX or MDX query and return rows as a list of dicts."""
    from pyadomd import Pyadomd

    conn = Pyadomd(_connection_string())
    conn.open()
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, [_serialize(v) for v in row])))
        return rows
    finally:
        conn.close()


def _serialize(value: Any) -> Any:
    """Ensure a value is JSON-serializable."""
    if value is None:
        return None
    if isinstance(value, (int, float, str, bool)):
        return value
    # Handle Decimal, datetime, and other types returned by ADOMD.NET
    return str(value)


def _escape_dmv(value: str) -> str:
    """Escape a string value for use in a DMV (schema rowset) query."""
    return value.replace("'", "''")


# ---------------------------------------------------------------------------
# MCP Server & Tools
# ---------------------------------------------------------------------------

mcp = FastMCP("ssas")


@mcp.tool()
def execute_query(query: str) -> str:
    """Execute a DAX or MDX query against the SSAS database.

    Args:
        query: A valid DAX (EVALUATE ...) or MDX (SELECT ...) query string.

    Returns:
        JSON array of result rows.

    Examples:
        DAX:  EVALUATE TOPN(10, 'Sales')
        MDX:  SELECT [Measures].[Amount] ON 0 FROM [Model]
    """
    try:
        rows = _execute(query)
        return json.dumps(rows, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception("execute_query failed")
        return json.dumps({"error": str(e), "details": traceback.format_exc()})


@mcp.tool()
def list_catalogs() -> str:
    """List all catalogs (databases) on the SSAS server."""
    try:
        rows = _execute("SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS")
        return json.dumps(rows, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception("list_catalogs failed")
        return json.dumps({"error": str(e), "details": traceback.format_exc()})


@mcp.tool()
def list_tables() -> str:
    """List all tables (dimensions and measure groups) in the current database."""
    try:
        rows = _execute(
            "SELECT [TABLE_NAME], [TABLE_TYPE] "
            "FROM $SYSTEM.DBSCHEMA_TABLES "
            "ORDER BY [TABLE_NAME]"
        )
        return json.dumps(rows, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception("list_tables failed")
        return json.dumps({"error": str(e), "details": traceback.format_exc()})


@mcp.tool()
def list_columns(table_name: str) -> str:
    """List all columns for a given table in the SSAS model.

    Args:
        table_name: The table name as returned by list_tables.
    """
    try:
        safe_name = _escape_dmv(table_name)
        rows = _execute(
            "SELECT [TABLE_NAME], [COLUMN_NAME], [DATA_TYPE], [IS_NULLABLE] "
            "FROM $SYSTEM.DBSCHEMA_COLUMNS "
            f"WHERE [TABLE_NAME] = '{safe_name}' "
            "ORDER BY [COLUMN_NAME]"
        )
        return json.dumps(rows, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception("list_columns failed")
        return json.dumps({"error": str(e), "details": traceback.format_exc()})


@mcp.tool()
def list_measures() -> str:
    """List all measures defined in the SSAS model with their expressions."""
    try:
        rows = _execute(
            "SELECT [MEASURE_NAME], [MEASURE_UNIQUE_NAME], "
            "[MEASURE_CAPTION], [DATA_TYPE], [EXPRESSION] "
            "FROM $SYSTEM.MDSCHEMA_MEASURES "
            "WHERE [MEASURE_IS_VISIBLE] "
            "ORDER BY [MEASURE_NAME]"
        )
        return json.dumps(rows, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception("list_measures failed")
        return json.dumps({"error": str(e), "details": traceback.format_exc()})


@mcp.tool()
def describe_model() -> str:
    """Get a high-level overview of the SSAS model: tables, measures, and metadata."""
    try:
        tables = _execute(
            "SELECT [TABLE_NAME], [TABLE_TYPE] "
            "FROM $SYSTEM.DBSCHEMA_TABLES "
            "ORDER BY [TABLE_NAME]"
        )
        measures = _execute(
            "SELECT [MEASURE_NAME] FROM $SYSTEM.MDSCHEMA_MEASURES "
            "WHERE [MEASURE_IS_VISIBLE]"
        )
        summary = {
            "database": os.environ.get("SSAS_DATABASE", "unknown"),
            "server": os.environ.get("SSAS_SERVER", "unknown"),
            "table_count": len(tables),
            "measure_count": len(measures),
            "tables": tables,
        }
        return json.dumps(summary, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception("describe_model failed")
        return json.dumps({"error": str(e), "details": traceback.format_exc()})
