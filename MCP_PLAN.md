# PyRocrail MCP Server - Code Assistant

**Purpose**: Help developers write PyRocrail applications through Claude by providing API documentation, code generation, and best practices.

**Target Users**: Developers building automation scripts with PyRocrail
**Scope**: Documentation lookup, code generation, examples - NO live layout control

---

## MCP Tools Design

### 1. `pyrocrail_api_lookup`
**Description**: Get API documentation for objects and methods

**Input**:
```json
{
  "object_type": "locomotive",  // or "lc", "block", "switch", etc.
  "method": "set_speed"          // optional - specific method
}
```

**Output**:
```
Locomotive.set_speed(speed: int) -> None

Set locomotive speed (0-100).

Example:
  loco = pr.model.get_lc("BR01")
  loco.set_speed(50)

See: OBJECTS.md#locomotive
```

**Implementation**:
- Parse OBJECTS.md at startup
- Create searchable index of all objects/methods
- Return formatted documentation + examples

---

### 2. `pyrocrail_list_methods`
**Description**: List all available methods for an object type

**Input**:
```json
{
  "object_type": "switch"
}
```

**Output**:
```
Switch methods:
- straight() - Set to straight position
- turnout() - Set to turnout position
- flip() - Toggle position
- left() - Left position (3-way)
- right() - Right position (3-way)
- lock() - Lock in position
- unlock() - Unlock
```

---

### 3. `pyrocrail_generate_action`
**Description**: Generate action code template

**Input**:
```json
{
  "trigger_type": "time",        // "time" or "event"
  "trigger": "12:30",            // time or object ID
  "description": "Start morning commute"
}
```

**Output**:
```python
def start_morning_commute(model):
    """Start morning commute"""
    # TODO: Get locomotive
    loco = model.get_lc("YOUR_LOCO_ID")

    # TODO: Implement action
    loco.use_schedule("morning_schedule")
    loco.dispatch()
    loco.go()

pr.add(Action(
    script=start_morning_commute,
    trigger_type=Trigger.TIME,
    trigger="12:30"
))
```

---

### 4. `pyrocrail_generate_script`
**Description**: Generate complete PyRocrail script template

**Input**:
```json
{
  "purpose": "basic_control"  // "basic_control", "scheduling", "automation"
}
```

**Output**:
```python
#!/usr/bin/env python3
"""
PyRocrail automation script
"""
from pyrocrail import PyRocrail, Action, Trigger
import time

# Connect to Rocrail
pr = PyRocrail("localhost", 8051)
pr.start()

# TODO: Add your control logic here

# Example: Get a locomotive
# loco = pr.model.get_lc("BR01")
# loco.set_speed(50)

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pr.stop()
```

---

### 5. `pyrocrail_find_example`
**Description**: Find example code for specific tasks

**Input**:
```json
{
  "task": "control locomotive speed"
}
```

**Output**:
```python
# Example: Control locomotive speed
from pyrocrail import PyRocrail

pr = PyRocrail()
pr.start()

loco = pr.model.get_lc("BR01")

# Set speed
loco.set_speed(50)

# Increase gradually
for speed in range(0, 51, 10):
    loco.set_speed(speed)
    time.sleep(1)

# Stop
loco.stop()

Source: examples/01-basic-control.py
```

---

### 6. `pyrocrail_get_attributes`
**Description**: List all attributes for an object type

**Input**:
```json
{
  "object_type": "block"
}
```

**Output**:
```
Block attributes:
- idx: Block ID (str)
- state: Block state - "open"/"closed" (str)
- occ: Occupied flag (bool)
- reserved: Reserved flag (bool)
- locid: Locomotive ID in block (str)
- enterside: Entry side (str)
- speed: Block speed limit (int)
- maxkmh: Maximum speed in km/h (int)

See: OBJECTS.md#block for full details
```

---

### 7. `pyrocrail_check_method`
**Description**: Verify if a method exists and get its signature

**Input**:
```json
{
  "object_type": "locomotive",
  "method": "collect"
}
```

**Output**:
```
❌ Method 'collect' does not exist for Locomotive

Did you mean:
- dispatch() - Dispatch locomotive for automatic control
- go() - Start locomotive in automatic mode

Note: 'collect' was removed as it's not documented in official Rocrail docs.
```

---

### 8. `pyrocrail_best_practices`
**Description**: Get best practices and common patterns

**Input**:
```json
{
  "topic": "error_handling"  // or "actions", "scheduling", etc.
}
```

**Output**:
```
Best Practices: Error Handling

1. Always check object exists before using:
   loco = pr.model.get_lc("BR01")
   if not loco:
       print("Locomotive BR01 not found!")
       return

2. Use try/except for network operations:
   try:
       pr.start()
   except ConnectionError:
       print("Cannot connect to Rocrail server")

3. Always stop PyRocrail on exit:
   try:
       while True:
           time.sleep(1)
   except KeyboardInterrupt:
       pr.stop()

See: examples/README.md for more patterns
```

---

## Project Structure

```
mcp-pyrocrail/
├── src/
│   ├── __init__.py
│   ├── server.py                 # Main MCP server
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── docs_lookup.py        # Documentation parsing
│   │   ├── code_generator.py     # Code templates
│   │   ├── examples_db.py        # Example snippets
│   │   └── validator.py          # Method validation
│   ├── data/
│   │   ├── templates/            # Code templates
│   │   │   ├── action_time.py
│   │   │   ├── action_event.py
│   │   │   └── basic_script.py
│   │   └── best_practices.json   # Best practices data
│   └── parsers/
│       └── objects_md_parser.py  # Parse OBJECTS.md
├── tests/
│   ├── test_docs_lookup.py
│   ├── test_code_generator.py
│   └── test_examples_db.py
├── pyproject.toml
└── README.md
```

---

## Implementation Steps

### Phase 1: Core Infrastructure (Week 1)

**1.1 Project Setup**
```bash
mkdir mcp-pyrocrail
cd mcp-pyrocrail
poetry init
poetry add mcp anthropic-mcp-python
poetry add --group dev pytest mypy ruff
```

**1.2 OBJECTS.md Parser**
Create `src/parsers/objects_md_parser.py`:
- Parse OBJECTS.md into structured data
- Extract object types, methods, attributes
- Build searchable index
- Cache parsed data

**1.3 Basic MCP Server**
Create `src/server.py`:
```python
from mcp.server import Server
from mcp.types import Tool
import asyncio

app = Server("pyrocrail-assistant")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="pyrocrail_api_lookup",
            description="Get API documentation for PyRocrail objects/methods",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {"type": "string"},
                    "method": {"type": "string"}
                },
                "required": ["object_type"]
            }
        ),
        # ... more tools
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "pyrocrail_api_lookup":
        return await docs_lookup(**arguments)
    # ... handle other tools
```

### Phase 2: Documentation Tools (Week 1-2)

**2.1 Implement `pyrocrail_api_lookup`**
```python
# src/tools/docs_lookup.py
class DocsLookup:
    def __init__(self, objects_md_path: str):
        self.data = parse_objects_md(objects_md_path)
        self.index = build_search_index(self.data)

    def lookup(self, object_type: str, method: str = None):
        obj = self.find_object(object_type)
        if not obj:
            return f"Object type '{object_type}' not found"

        if method:
            return self.format_method(obj, method)
        else:
            return self.format_object(obj)
```

**2.2 Implement `pyrocrail_list_methods`**
**2.3 Implement `pyrocrail_get_attributes`**
**2.4 Implement `pyrocrail_check_method`**

### Phase 3: Code Generation (Week 2)

**3.1 Create Templates**
`src/data/templates/action_time.py`:
```python
def {action_name}(model):
    """{description}"""
    # TODO: Get objects
    # loco = model.get_lc("YOUR_LOCO_ID")

    # TODO: Implement action
    pass

pr.add(Action(
    script={action_name},
    trigger_type=Trigger.TIME,
    trigger="{trigger}"
))
```

**3.2 Implement `pyrocrail_generate_action`**
```python
# src/tools/code_generator.py
class CodeGenerator:
    def generate_action(self, trigger_type, trigger, description):
        template = load_template(f"action_{trigger_type}.py")
        action_name = self.sanitize_name(description)
        return template.format(
            action_name=action_name,
            trigger=trigger,
            description=description
        )
```

**3.3 Implement `pyrocrail_generate_script`**

### Phase 4: Examples Database (Week 2-3)

**4.1 Build Examples Index**
```python
# src/tools/examples_db.py
class ExamplesDB:
    def __init__(self, examples_dir: str):
        self.examples = self.scan_examples(examples_dir)
        self.index = self.build_index()

    def find_example(self, task: str):
        # Search examples by description/comments
        # Return relevant code snippets
```

**4.2 Implement `pyrocrail_find_example`**

### Phase 5: Best Practices (Week 3)

**5.1 Create Best Practices Database**
`src/data/best_practices.json`:
```json
{
  "error_handling": {
    "description": "Best practices for error handling",
    "examples": [
      "Always check if objects exist before using",
      "Use try/except for network operations",
      "Always call pr.stop() on exit"
    ],
    "code": "..."
  }
}
```

**5.2 Implement `pyrocrail_best_practices`**

### Phase 6: Testing (Week 3-4)

**6.1 Unit Tests**
```python
# tests/test_docs_lookup.py
def test_lookup_locomotive():
    lookup = DocsLookup("../OBJECTS.md")
    result = lookup.lookup("locomotive", "set_speed")
    assert "set_speed(speed: int)" in result
    assert "Example:" in result

def test_lookup_invalid_method():
    lookup = DocsLookup("../OBJECTS.md")
    result = lookup.lookup("locomotive", "collect")
    assert "does not exist" in result
    assert "Did you mean" in result
```

**6.2 Integration Tests**
```python
# tests/test_mcp_server.py
async def test_mcp_api_lookup():
    async with mcp_client() as client:
        result = await client.call_tool(
            "pyrocrail_api_lookup",
            {"object_type": "switch", "method": "straight"}
        )
        assert result.success
        assert "straight()" in result.content
```

### Phase 7: Documentation (Week 4)

**7.1 README.md**
```markdown
# PyRocrail MCP Server

Code assistant for PyRocrail development.

## Installation

### For Claude Desktop
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "pyrocrail": {
      "command": "uvx",
      "args": ["mcp-pyrocrail"]
    }
  }
}
```

### For Development
```bash
git clone https://github.com/user/mcp-pyrocrail
cd mcp-pyrocrail
poetry install
poetry run mcp-pyrocrail
```

## Usage Examples

### Get API Documentation
```
User: "How do I control a switch?"
Claude: [uses pyrocrail_api_lookup]
```

### Generate Code
```
User: "Generate a time-based action"
Claude: [uses pyrocrail_generate_action]
```
```

**7.2 Usage Guide**
Create `USAGE.md` with examples of all tools

---

## Testing Plan

### Manual Testing with Claude Desktop

**Test 1: API Lookup**
1. Ask: "How do I set locomotive speed in PyRocrail?"
2. Verify: Returns correct method signature + example
3. Ask: "What methods are available for blocks?"
4. Verify: Returns complete list

**Test 2: Code Generation**
1. Ask: "Generate a time-based action at 14:30"
2. Verify: Returns valid Python code with correct syntax
3. Ask: "Create a basic PyRocrail script"
4. Verify: Returns complete runnable template

**Test 3: Examples**
1. Ask: "Show me an example of controlling a route"
2. Verify: Returns relevant code from examples/
3. Ask: "How do I handle errors in PyRocrail?"
4. Verify: Returns best practices

**Test 4: Validation**
1. Ask: "Does locomotive have a 'collect' method?"
2. Verify: Says no, suggests alternatives
3. Ask: "What attributes does a signal have?"
4. Verify: Returns complete list

### Automated Testing

**Coverage Goals**:
- Unit tests: 100% of tool functions
- Integration tests: All MCP tools
- Type checking: mypy --strict passes
- Linting: ruff check passes

---

## Success Metrics

**Functionality**:
- ✅ All 17 PyRocrail objects documented
- ✅ All methods discoverable via MCP
- ✅ Code generation produces valid Python
- ✅ Examples findable by natural language

**Performance**:
- ✅ API lookup < 100ms
- ✅ Code generation < 500ms
- ✅ Startup time < 2s

**Quality**:
- ✅ 0 type errors (mypy strict)
- ✅ 0 lint errors (ruff)
- ✅ Test coverage > 90%

---

## Timeline

- **Week 1**: Core infrastructure + documentation tools
- **Week 2**: Code generation + templates
- **Week 3**: Examples database + best practices
- **Week 4**: Testing + documentation

**Total**: 4 weeks to production-ready MCP server

---

## Future Enhancements (Post-Launch)

### Phase 2 Features:
- **Code review**: Analyze user's PyRocrail code for issues
- **Migration helper**: Help upgrade from old APIs
- **Performance tips**: Suggest optimizations
- **Interactive debugger**: Help troubleshoot issues

### Phase 3 Features:
- **Visual diagram generation**: Create layout diagrams from code
- **Test generation**: Generate unit tests for actions
- **Documentation generator**: Generate docs from code
