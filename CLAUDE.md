# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyRocrail is a Python library for interfacing with Rocrail model railway control software. It provides a Python API to communicate with Rocrail servers via XML-over-TCP protocol.

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
  - System control: `power_on()`, `power_off()`, `emergency_stop()`, `auto_on()`, `auto_off()`

- **Communicator** (`src/pyrocrail/communicator.py`): Low-level TCP communication with Rocrail
  - XML message protocol with custom header format: `<xmlh><xml size="X" name="type"/></xmlh>message`
  - Threaded message parsing and decoding
  - Mutex-protected send/receive operations

- **Model** (`src/pyrocrail/model.py`): Rocrail layout model representation
  - Maintains all object domains: feedback, outputs, locomotives, switches, signals, routes, blocks
  - Handles clock synchronization and time-based callbacks
  - XML plan parsing and object instantiation
  - Getter methods: `get_fb()`, `get_co()`, `get_lc()`, `get_sw()`, `get_sg()`, `get_st()`, `get_bk()`

- **Control Objects** (`src/pyrocrail/objects/`): Complete Rocrail entity representations
  - `Feedback`: Sensor/feedback objects with on/off/flip operations
  - `Output`: Control outputs with on/off and color support
  - `Locomotive`: Speed, direction, lights, function control with dispatch/collect
  - `Switch`: Straight/turnout positioning with flip and state management
  - `Signal`: Multi-aspect signals (red/green/yellow/white) with auto/manual modes
  - `Route`: Route activation, locking, and state management
  - `Block`: Block reservation, occupancy detection, and locomotive tracking
  - `Action`: Script containers with trigger types and conditions

### Communication Flow

1. PyRocrail establishes connection via Communicator
2. Model requests plan via `<model cmd="plan"/>` and waits for response
3. Feedback sensors and outputs are parsed and stored in domain dictionaries
4. Time callbacks trigger registered actions via ThreadPoolExecutor
5. Actions can manipulate model objects which send XML commands back to Rocrail

### Configuration

- **pyproject.toml**: Uses Poetry for dependency management
- **Black formatter**: 180 character line length, `src/` only
- **Ruff**: E, F, N rule sets enabled, 5000 char line length (defers to black)
- **Pyright**: Strict type checking mode, Python 3.12 target
- **CI**: GitHub Actions runs ruff on all Python files

### Development Notes

- The library assumes Rocrail server running on localhost:8051 by default
- XML protocol requires null-terminated messages
- Object attributes are dynamically set using `set_attr()` utility with type conversion
- Threading is extensively used - be careful with shared state
- The `example_plan/` directory contains sample Rocrail configuration files