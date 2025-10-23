# PyRocrail MCP Server

Model Context Protocol (MCP) server for PyRocrail development assistance.

## What It Does

Helps developers write PyRocrail code through Claude by providing:

- **API Documentation Lookup** - Get method signatures, parameters, and examples
- **Method Validation** - Check if methods exist, get suggestions
- **Code Search** - Find relevant methods and objects
- **Attribute Reference** - List all attributes for objects

## Installation

### Prerequisites
- Python 3.12+
- Poetry
- Claude Desktop (for testing)

### Install Dependencies

```bash
cd mcp-pyrocrail
poetry install
```

## Usage with Claude Desktop

### Step 1: Locate Config File

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- Typically: `C:\Users\<your-username>\AppData\Roaming\Claude\claude_desktop_config.json`
- To open: Press `Win + R`, type `%APPDATA%\Claude`, press Enter

**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Linux**: `~/.config/Claude/claude_desktop_config.json`

Open or create the `claude_desktop_config.json` file in that location.

### Step 2: Add MCP Server Config

Add this to your config file:

**Windows**:
```json
{
  "mcpServers": {
    "pyrocrail": {
      "command": "D:\\src\\py-rocrail\\mcp-pyrocrail\\run_server.bat"
    }
  }
}
```

**Mac/Linux**:
```json
{
  "mcpServers": {
    "pyrocrail": {
      "command": "/path/to/py-rocrail/mcp-pyrocrail/run_server.sh"
    }
  }
}
```

**Important**: Update the path to match your actual mcp-pyrocrail directory location.

### Step 3: Restart Claude Desktop

1. **Completely close** Claude Desktop (check system tray)
2. Start Claude Desktop again
3. The server logs will appear in Claude Desktop's logs

### Verify It's Working

In Claude Desktop, ask: "What methods are available for locomotives in PyRocrail?"

Claude should use the `pyrocrail_list_methods` tool to look up the answer from OBJECTS.md.

## Available Tools

### 1. `pyrocrail_api_lookup`
Get API documentation for objects and methods.

**Example**:
```
User: "How do I set locomotive speed?"
Claude: [uses pyrocrail_api_lookup with object_type="locomotive", method="set_speed"]
```

### 2. `pyrocrail_list_methods`
List all methods for an object type.

**Example**:
```
User: "What methods are available for switches?"
Claude: [uses pyrocrail_list_methods with object_type="switch"]
```

### 3. `pyrocrail_get_attributes`
Get all attributes for an object type.

**Example**:
```
User: "What attributes does a block have?"
Claude: [uses pyrocrail_get_attributes with object_type="block"]
```

### 4. `pyrocrail_check_method`
Validate if a method exists.

**Example**:
```
User: "Does locomotive have a 'collect' method?"
Claude: [uses pyrocrail_check_method with object_type="locomotive", method="collect"]
```

### 5. `pyrocrail_search`
Search across all documentation.

**Example**:
```
User: "Find methods related to speed control"
Claude: [uses pyrocrail_search with query="speed"]
```

## Example Conversation

```
User: "I want to control a locomotive in PyRocrail. How do I do that?"

Claude: Let me look up the Locomotive API for you.
[uses pyrocrail_api_lookup with object_type="locomotive"]

Based on the documentation, here's how to control a locomotive:

1. Get the locomotive object:
   loco = pr.model.get_lc("BR01")

2. Set the speed (0-100):
   loco.set_speed(50)

3. Control direction:
   loco.set_direction(True)  # True = forward

4. Start in automatic mode:
   loco.go()

Would you like to see more specific examples?
```

## Testing the Server

### Test with stdio

```bash
poetry run python -m mcp_pyrocrail.server
```

The server will start and wait for JSON-RPC messages on stdin.

### Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector poetry run python -m mcp_pyrocrail.server
```

This opens a web interface to test the MCP server interactively.

## Development

### Run Tests

```bash
poetry run pytest
```

### Type Checking

```bash
poetry run mypy src/
```

### Linting

```bash
poetry run ruff check src/
```

## Troubleshooting

### Server not appearing in Claude Desktop

1. Check the config file path is correct
2. Verify the `cwd` path points to mcp-pyrocrail directory (use `\\` for Windows paths)
3. Completely close Claude Desktop (check system tray)
4. Restart Claude Desktop
5. Check Claude Desktop logs for errors

### Checking Server Logs

On Windows, Claude Desktop logs are at:
`%APPDATA%\Claude\logs\mcp*.log`

Look for error messages from the pyrocrail server. The logs will show:
- "Successfully loaded OBJECTS.md" if working correctly
- "ERROR: OBJECTS.md not found" if path is wrong
- Any other error details

### Server transport closed error

If you see "Server transport closed unexpectedly" or "Poetry could not find pyproject.toml":
1. This means Poetry is running from the wrong directory
2. **Solution**: Use the startup script instead of calling poetry directly:
   - Windows: Use `run_server.bat`
   - Mac/Linux: Use `run_server.sh`
3. Update your config to use the full path to the startup script
4. Completely restart Claude Desktop (not just close the window)
5. Test the server manually from the correct directory:
   ```bash
   cd /path/to/py-rocrail/mcp-pyrocrail
   poetry run python -m mcp_pyrocrail.server
   ```

### OBJECTS.md not found

The server looks for OBJECTS.md in the parent PyRocrail directory. Make sure:
- The MCP server is located in `py-rocrail/mcp-pyrocrail/`
- OBJECTS.md exists in `py-rocrail/OBJECTS.md`
- The `cwd` path in config points to the mcp-pyrocrail directory

## Architecture

```
mcp-pyrocrail/
├── src/mcp_pyrocrail/
│   ├── server.py           # Main MCP server
│   ├── tools/
│   │   └── docs_lookup.py  # Documentation lookup
│   └── parsers/
│       └── objects_md_parser.py  # OBJECTS.md parser
└── tests/
```

## License

Same as PyRocrail (see parent project)
