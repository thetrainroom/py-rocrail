# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyRocrail is a Python library for interfacing with Rocrail model railway control software. It provides a Python API to communicate with Rocrail servers via XML-over-TCP protocol.

**Key Features:**
- **17 Object Types**: Full support for locomotives, blocks, switches, signals, routes, and more
- **Real-time Control**: Direct TCP/IP communication with Rocrail server
- **Event-Driven**: Action system for time-based and event-based automation
- **Type-Safe**: Complete type annotations (0 pyright errors)
- **Verified Commands**: All commands verified against official Rocrail documentation

**Primary Documentation**: See [OBJECTS.md](OBJECTS.md) for complete reference documentation of all object types and their commands.

## Development Commands

### Code Quality and Linting
```bash
# Run ruff linter (primary linter used in CI)
ruff check $(git ls-files '*.py')

# Run black formatter with 180 character line length
black --line-length 180 src/

# Run pyright type checker with strict mode
pyright
```

### Testing
```bash
# Run the basic test script
python test.py
```

## Architecture

### Core Components

- **PyRocrail** (`src/pyrocrail/pyrocrail.py`): Main orchestrator class that manages the connection and action execution
  - Handles time-based and event-based actions via threading
  - Uses ThreadPoolExecutor for concurrent script execution
  - Manages lifecycle of communicator and model
  - System control: `power_on()`, `power_off()`, `emergency_stop()`, `auto_on()`, `auto_off()`, `reset()`, `save()`, `shutdown()`
  - Clock control: `set_clock()` for fast clock, time setting, and freeze/resume
  - Session control: `start_of_day()`, `end_of_day()`, `update_ini()`

- **Communicator** (`src/pyrocrail/communicator.py`): Low-level TCP communication with Rocrail
  - XML message protocol with custom header format: `<xmlh><xml size="X" name="type"/></xmlh>message`
  - Threaded message parsing and decoding
  - Mutex-protected send/receive operations

- **Model** (`src/pyrocrail/model.py`): Rocrail layout model representation
  - Maintains 17 object domains for all controllable layout elements
  - Handles clock synchronization and time-based callbacks
  - XML plan parsing and object instantiation
  - Model queries: `request_locomotive_list()`, `request_switch_list()`, `request_feedback_list()`, `request_locomotive_properties()`, `add_object()`, `remove_object()`, `modify_object()`, `merge_plan()`
  - Getter methods for all object types:
    - `get_lc()` - Locomotives, `get_bk()` - Blocks, `get_sw()` - Switches, `get_sg()` - Signals
    - `get_st()` - Routes, `get_fb()` - Feedback sensors, `get_co()` - Outputs
    - `get_car()` - Cars, `get_operator()` - Operators (trains), `get_schedule()` - Schedules
    - `get_stage()` - Staging yards, `get_text()` - Text displays, `get_booster()` - Boosters
    - `get_variable()` - Variables, `get_tour()` - Tours, `get_location()` - Locations, `get_weather()` - Weather
  - Collection getter methods (return all objects):
    - `get_locomotives()`, `get_blocks()`, `get_switches()`, `get_signals()`, `get_routes()`
    - `get_feedbacks()`, `get_outputs()`, `get_cars()`, `get_operators()`, `get_schedules()`, `get_stages()`

- **Control Objects** (`src/pyrocrail/objects/`): 17 complete Rocrail entity types - see [OBJECTS.md](OBJECTS.md) for full documentation
  - **Core Control**: `Locomotive` (speed, direction, functions), `Block` (reservation, occupancy), `Switch` (turnout control), `Signal` (aspect control), `Route` (path routing)
  - **Detection & Output**: `Feedback` (sensors), `Output` (accessories), `Text` (displays), `Booster` (power districts)
  - **Rolling Stock**: `Car` (waybills, loading), `Operator` (train compositions, shown as "Trains" in GUI)
  - **Operations**: `Schedule` (timetables), `Tour` (demo mode), `Location` (flow management for hidden yards), `Stage` (staging yards)
  - **Global State**: `Variable` (cross-client state tracking), `Weather` (atmospheric effects)
  - **Automation**: `Action` (time-based and event-based script execution)

### Communication Flow

1. PyRocrail establishes connection via Communicator
2. Model requests plan via `<model cmd="plan"/>` and waits for response
3. All 17 object types are parsed from plan XML and stored in domain dictionaries
4. State updates from server automatically refresh object attributes
5. Time callbacks trigger registered actions via ThreadPoolExecutor
6. Actions can manipulate model objects which send XML commands back to Rocrail
7. All commands verified against official Rocrail XMLScript documentation

### Configuration

- **pyproject.toml**: Uses Poetry for dependency management
- **Black formatter**: 180 character line length, `src/` only
- **Ruff**: E, F, N rule sets enabled, 5000 char line length (defers to black)
- **Pyright**: Strict type checking mode, Python 3.12 target, 0 errors maintained
- **CI**: GitHub Actions runs ruff and pyright on all Python files

### Development Notes

- The library assumes Rocrail server running on localhost:8051 by default
- XML protocol requires null-terminated messages
- Object attributes are dynamically set using `set_attr()` utility with type conversion
- Threading is extensively used - be careful with shared state
- The `example_plan/` directory contains sample Rocrail configuration files

### Command Verification

**All commands in this library have been verified against official Rocrail documentation:**
- Primary source: [XMLScript Documentation](https://wiki.rocrail.net/doku.php?id=xmlscripting-en)
- Secondary source: [Rocrail Wrapper XML Reference](https://wiki.rocrail.net/rocrail-snapshot/rocrail/wrapper-en.html)
- Each object type documented in [OBJECTS.md](OBJECTS.md) includes links to official Rocrail documentation
- Commands not found in official docs have been removed to ensure compatibility
- Type-safe: All methods have complete type annotations and pass pyright strict mode (0 errors)

**When adding new features:**
1. Always verify commands exist in official XMLScript documentation
2. Add type annotations for all parameters and return values
3. Document with docstrings including Args and usage notes
4. Run `ruff check`, `black`, and `pyright` before committing
5. Update [OBJECTS.md](OBJECTS.md) with new commands and examples