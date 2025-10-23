"""PyRocrail MCP Server - Main server implementation"""

import sys
import asyncio
from pathlib import Path
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from .tools.docs_lookup import DocsLookup


# Find OBJECTS.md in parent directory
OBJECTS_MD_PATH = Path(__file__).parent.parent.parent.parent / "OBJECTS.md"

# Verify path exists
if not OBJECTS_MD_PATH.exists():
    print(f"ERROR: OBJECTS.md not found at {OBJECTS_MD_PATH}", file=sys.stderr)
    print(f"Current file: {__file__}", file=sys.stderr)
    print(f"Resolved path: {OBJECTS_MD_PATH.resolve()}", file=sys.stderr)
    sys.exit(1)

# Initialize tools
try:
    docs_lookup = DocsLookup(str(OBJECTS_MD_PATH))
    print(f"Successfully loaded OBJECTS.md from {OBJECTS_MD_PATH}", file=sys.stderr)
except Exception as e:
    print(f"ERROR: Failed to initialize DocsLookup: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Create MCP server
app = Server("pyrocrail-assistant")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="pyrocrail_api_lookup",
            description="Get API documentation for PyRocrail objects and methods. "
                       "Provide object_type (e.g., 'locomotive', 'switch', 'block') and optionally a method name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "Object type name (e.g., 'locomotive', 'lc', 'switch', 'block')"
                    },
                    "method": {
                        "type": "string",
                        "description": "Optional: specific method name to get documentation for"
                    }
                },
                "required": ["object_type"]
            }
        ),
        Tool(
            name="pyrocrail_list_methods",
            description="List all available methods for a PyRocrail object type with brief descriptions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "Object type name (e.g., 'locomotive', 'switch', 'block')"
                    }
                },
                "required": ["object_type"]
            }
        ),
        Tool(
            name="pyrocrail_get_attributes",
            description="Get all attributes for a PyRocrail object type with descriptions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "Object type name (e.g., 'locomotive', 'switch', 'block')"
                    }
                },
                "required": ["object_type"]
            }
        ),
        Tool(
            name="pyrocrail_check_method",
            description="Check if a method exists for an object type and get validation with suggestions if it doesn't.",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "Object type name"
                    },
                    "method": {
                        "type": "string",
                        "description": "Method name to check"
                    }
                },
                "required": ["object_type", "method"]
            }
        ),
        Tool(
            name="pyrocrail_search",
            description="Search across all PyRocrail documentation for methods, objects, or concepts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""

    try:
        if name == "pyrocrail_api_lookup":
            object_type = arguments["object_type"]
            method = arguments.get("method")
            result = docs_lookup.api_lookup(object_type, method)
            return [TextContent(type="text", text=result)]

        elif name == "pyrocrail_list_methods":
            object_type = arguments["object_type"]
            result = docs_lookup.list_methods(object_type)
            return [TextContent(type="text", text=result)]

        elif name == "pyrocrail_get_attributes":
            object_type = arguments["object_type"]
            result = docs_lookup.get_attributes(object_type)
            return [TextContent(type="text", text=result)]

        elif name == "pyrocrail_check_method":
            object_type = arguments["object_type"]
            method = arguments["method"]
            result = docs_lookup.check_method(object_type, method)
            return [TextContent(type="text", text=result)]

        elif name == "pyrocrail_search":
            query = arguments["query"]
            result = docs_lookup.search(query)
            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point for the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run():
    """Synchronous entry point"""
    asyncio.run(main())


if __name__ == "__main__":
    run()
