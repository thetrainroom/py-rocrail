# Testing Strategy for PyRocrail

**Purpose**: Establish comprehensive testing methodology for PyRocrail library
**Date**: 2025-10-17
**Status**: PCAP-based testing implemented ✅

---

## 1. Current Testing Situation

### 1.1 Existing Test Infrastructure

**Tests Implemented**:
- ✅ **PCAP Replay Testing** (`tests/tools/pcap_replay_test.py`) - Replays real network captures
- ✅ **PCAP Analysis Tools** - Extract and analyze XML messages from captures
- ✅ **State Update Verification** - Confirms state updates are handled correctly
- ⚠️ `test.py` in root - Basic smoke test (needs update)

**Working**:
- ✅ PCAP-based regression testing with real data
- ✅ Message handling coverage analysis
- ✅ State update validation

**Still Needed**:
- ⬜ Unit test framework (pytest)
- ⬜ CI/CD integration
- ⬜ Formal test suite

---

## 2. Testing Architecture

### 2.1 Test Pyramid

```
        /\
       /  \
      / E2E\         End-to-End: Real Rocrail (manual/optional)
     /------\
    /  Integ \       Integration: Mock Rocrail server
   /----------\
  /    Unit    \     Unit: Individual classes/methods
 /--------------\
```

### 2.2 Test Types

1. **Unit Tests** (70% of tests)
   - Individual object methods
   - State management
   - Command formatting
   - Validation logic

2. **Integration Tests** (25% of tests)
   - Communication with mock server
   - XML parsing/encoding
   - State synchronization
   - Threading behavior

3. **End-to-End Tests** (5% of tests)
   - Real Rocrail server
   - Complete workflows
   - Manual/optional execution

---

## 3. Testing Framework

### 3.1 Tools

```toml
# Add to pyproject.toml [tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"              # Test framework
pytest-cov = "^4.1.0"          # Coverage reporting
pytest-mock = "^3.12.0"        # Mocking support
pytest-asyncio = "^0.23.0"     # Async test support
pytest-timeout = "^2.2.0"      # Timeout handling
freezegun = "^1.4.0"           # Time mocking for clock tests
```

### 3.2 Directory Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── fixtures/                   # Sample XML files
│   ├── sample_plan.xml
│   ├── sample_lc.xml
│   ├── sample_bk.xml
│   └── malformed.xml
├── unit/
│   ├── __init__.py
│   ├── test_locomotive.py
│   ├── test_block.py
│   ├── test_switch.py
│   ├── test_signal.py
│   ├── test_route.py
│   ├── test_feedback.py
│   ├── test_output.py
│   └── test_model.py
├── integration/
│   ├── __init__.py
│   ├── test_communicator.py
│   ├── test_state_updates.py
│   ├── test_command_flow.py
│   └── mock_rocrail.py         # Mock server
└── e2e/
    ├── __init__.py
    ├── test_real_server.py     # Requires real Rocrail
    └── MANUAL_TESTS.md         # Manual test checklist
```

---

## 4. Mock Rocrail Server

### 4.1 Purpose

Simulate Rocrail server for integration tests without requiring real installation.

### 4.2 Features

```python
class MockRocrailServer:
    """Mock Rocrail server for testing"""

    def __init__(self, port=18051):  # Different port than real Rocrail
        self.port = port
        self.state = {}  # Track object states
        self.message_log = []  # Record all messages
        self._socket = None
        self._thread = None

    def start(self):
        """Start mock server"""
        pass

    def stop(self):
        """Stop mock server"""
        pass

    def send_plan(self):
        """Send mock plan XML"""
        pass

    def send_clock(self, hour, minute):
        """Send clock update"""
        pass

    def send_fb_event(self, fb_id, state):
        """Send feedback sensor event"""
        pass

    def send_lc_update(self, lc_id, speed, direction):
        """Send locomotive state update"""
        pass

    def send_bk_update(self, bk_id, state, locid):
        """Send block state update"""
        pass

    def handle_command(self, xml):
        """Process incoming command and update internal state"""
        pass
```

### 4.3 Test Scenarios

1. **Connection**
   - Successful connection
   - Connection refused
   - Connection timeout
   - Reconnection after disconnect

2. **Plan Loading**
   - Complete plan parsing
   - Partial plan (missing sections)
   - Malformed XML
   - Large plans (performance)

3. **Command Execution**
   - Valid commands
   - Invalid commands
   - Unknown object IDs
   - Concurrent commands

4. **State Updates**
   - Feedback events
   - Clock ticks
   - Block occupancy changes
   - Locomotive position updates

---

## 5. Unit Test Examples

### 5.1 Locomotive Tests

```python
# tests/unit/test_locomotive.py

import pytest
from unittest.mock import Mock
from pyrocrail.objects.locomotive import Locomotive
import xml.etree.ElementTree as ET


@pytest.fixture
def mock_communicator():
    """Mock communicator for testing"""
    return Mock()


@pytest.fixture
def sample_lc_xml():
    """Sample locomotive XML"""
    xml_str = '''<lc id="BR01" addr="3" V_max="100" V_min="0" dir="true"/>'''
    return ET.fromstring(xml_str)


def test_locomotive_init(sample_lc_xml, mock_communicator):
    """Test locomotive initialization"""
    lc = Locomotive(sample_lc_xml, mock_communicator)
    assert lc.idx == "BR01"
    assert lc.addr == 3
    assert lc.V_max == 100
    assert lc.dir == True


def test_set_speed(sample_lc_xml, mock_communicator):
    """Test speed setting"""
    lc = Locomotive(sample_lc_xml, mock_communicator)
    lc.set_speed(50)

    mock_communicator.send.assert_called_once()
    args = mock_communicator.send.call_args
    assert args[0][0] == "lc"
    assert 'V="50"' in args[0][1]
    assert lc.V == 50


def test_set_speed_clipping(sample_lc_xml, mock_communicator):
    """Test speed clipping to valid range"""
    lc = Locomotive(sample_lc_xml, mock_communicator)

    # Test upper bound
    lc.set_speed(150)
    assert lc.V == 100

    # Test lower bound
    lc.set_speed(-10)
    assert lc.V == 0


def test_direction_change(sample_lc_xml, mock_communicator):
    """Test direction changes"""
    lc = Locomotive(sample_lc_xml, mock_communicator)

    lc.set_direction(False)
    assert lc.dir == False
    assert 'dir="false"' in mock_communicator.send.call_args[0][1]

    lc.set_direction(True)
    assert lc.dir == True
    assert 'dir="true"' in mock_communicator.send.call_args[0][1]


def test_lights_control(sample_lc_xml, mock_communicator):
    """Test lights on/off"""
    lc = Locomotive(sample_lc_xml, mock_communicator)

    lc.set_lights(True)
    assert lc.lights == True

    lc.set_lights(False)
    assert lc.lights == False


def test_function_control(sample_lc_xml, mock_communicator):
    """Test function control"""
    lc = Locomotive(sample_lc_xml, mock_communicator)

    lc.set_function(1, True)
    assert lc.fn[1] == True

    lc.set_function(1, False)
    assert lc.fn[1] == False


def test_dispatch_collect(sample_lc_xml, mock_communicator):
    """Test dispatch and collect commands"""
    lc = Locomotive(sample_lc_xml, mock_communicator)

    lc.dispatch()
    assert 'cmd="dispatch"' in mock_communicator.send.call_args[0][1]

    lc.collect()
    assert 'cmd="collect"' in mock_communicator.send.call_args[0][1]
```

### 5.2 Block Tests

```python
# tests/unit/test_block.py

def test_block_reservation(sample_bk_xml, mock_communicator):
    """Test block reservation"""
    bk = Block(sample_bk_xml, mock_communicator)

    bk.reserve("BR01")
    assert bk.reserved == True
    assert bk.locid == "BR01"
    assert bk.state == "reserved"


def test_block_free(sample_bk_xml, mock_communicator):
    """Test freeing block"""
    bk = Block(sample_bk_xml, mock_communicator)
    bk.reserve("BR01")

    bk.free()
    assert bk.reserved == False
    assert bk.locid == ""
    assert bk.state == "free"


def test_block_state_queries(sample_bk_xml, mock_communicator):
    """Test block state query methods"""
    bk = Block(sample_bk_xml, mock_communicator)

    assert bk.is_free() == True

    bk.reserve("BR01")
    assert bk.is_reserved() == True
    assert bk.is_free() == False

    bk.close()
    assert bk.is_closed() == True
```

### 5.3 Switch Tests

```python
# tests/unit/test_switch.py

def test_switch_positions(sample_sw_xml, mock_communicator):
    """Test switch position changes"""
    sw = Switch(sample_sw_xml, mock_communicator)

    sw.straight()
    assert sw.state == "straight"
    assert sw.switched == False

    sw.turnout()
    assert sw.state == "turnout"
    assert sw.switched == True


def test_switch_flip(sample_sw_xml, mock_communicator):
    """Test switch flip operation"""
    sw = Switch(sample_sw_xml, mock_communicator)

    initial_state = sw.switched
    sw.flip()
    assert sw.switched == (not initial_state)

    sw.flip()
    assert sw.switched == initial_state
```

---

## 6. PCAP-Based Testing (✅ IMPLEMENTED)

### 6.1 Current PCAP Tests

We now have real PCAP captures from actual Rocrail operation:

**Available Captures**:
- `rocrail_start.pcapng` (2.9MB) - Startup and plan loading
- `rocrail_fahren.pcapng` (1.3MB) - Trains running
- `rocrail_schalten.pcapng` (406KB) - Switching operations
- `rocrail_edit.pcapng` (266KB) - Editing mode

**Tools Implemented**:
1. **`pcap_parser.py`** - Extracts XML messages from PCAP
2. **`pcap_stats.py`** - Analyzes message statistics
3. **`pcap_replay_test.py`** - Tests PyRocrail with real messages

**Current Test Results** (as of 2025-10-17):
```
rocrail_start.txt:  62.9% handled (1676 of 2666 messages)
rocrail_fahren.txt: 62.5% handled (2169 of 3470 messages)
```

**State Updates Verified** ✅:
- Locomotive state updates: 190 messages handled
- Feedback sensor updates: 150 messages handled
- Block state updates: 15 messages handled
- Switch state updates: 43 messages handled
- Signal state updates: 19 messages handled
- Route state updates: 19 messages handled

### 6.2 Running PCAP Tests

```bash
# Extract messages from PCAP
python tests/tools/pcap_parser.py tests/fixtures/pcap/rocrail_fahren.pcapng

# Analyze statistics
python tests/tools/pcap_stats.py tests/fixtures/pcap/rocrail_fahren.txt

# Test PyRocrail handling
python tests/tools/pcap_replay_test.py tests/fixtures/pcap/rocrail_fahren.txt
```

### 6.3 Integration Test Examples (TODO)

```python
# tests/integration/test_communicator.py

import pytest
import time
from unittest.mock import Mock
from pyrocrail.communicator import Communicator
from pyrocrail.model import Model
from tests.integration.mock_rocrail import MockRocrailServer


@pytest.fixture
def mock_server():
    """Start mock Rocrail server"""
    server = MockRocrailServer(port=18051)  # Different port
    server.start()
    yield server
    server.stop()


def test_connection_success(mock_server):
    """Test successful connection to server"""
    com = Communicator("localhost", 18051)
    com.start()

    assert com.run == True

    com.stop()


def test_send_receive(mock_server):
    """Test sending and receiving messages"""
    com = Communicator("localhost", 18051)
    model = Mock()
    com.model = model
    com.start()

    # Send command
    com.send("lc", '<lc id="BR01" V="50"/>')

    # Wait for processing
    time.sleep(0.1)

    # Verify server received it
    assert len(mock_server.message_log) > 0
    assert "BR01" in mock_server.message_log[-1]

    com.stop()


def test_plan_loading(mock_server):
    """Test plan loading from server"""
    mock_server.set_plan(sample_plan_xml)

    com = Communicator("localhost", 18051)
    model = Model(com)
    com.start()

    com.send("model", '<model cmd="plan"/>')

    # Wait for plan to arrive
    time.sleep(0.5)

    assert model.plan_recv == True
    assert len(model._lc_domain) > 0

    com.stop()
```

### 6.4 State Update Tests (✅ IMPLEMENTED)

```python
# tests/integration/test_state_updates.py

def test_feedback_event_handling(mock_server):
    """Test handling feedback events from server"""
    com = Communicator("localhost", 18051)
    model = Model(com)
    com.start()
    model.init()

    # Add feedback to model
    fb_xml = ET.fromstring('<fb id="FB01" state="false"/>')
    fb = Feedback(fb_xml, com)
    model._fb_domain["FB01"] = fb

    # Server sends feedback event
    mock_server.send_fb_event("FB01", True)

    time.sleep(0.1)

    # Verify state updated
    assert model.get_fb("FB01").state == True

    com.stop()


def test_locomotive_state_update(mock_server):
    """Test locomotive state updates from server"""
    com = Communicator("localhost", 18051)
    model = Model(com)
    com.start()
    model.init()

    lc = model.get_lc("BR01")
    initial_speed = lc.V

    # Server sends locomotive state update
    mock_server.send_lc_update("BR01", speed=75, direction=False)

    time.sleep(0.1)

    # Verify state updated
    assert lc.V == 75
    assert lc.dir == False

    com.stop()


def test_block_occupancy_update(mock_server):
    """Test block occupancy updates"""
    com = Communicator("localhost", 18051)
    model = Model(com)
    com.start()
    model.init()

    bk = model.get_bk("BK1")

    # Server sends block occupancy event
    mock_server.send_bk_update("BK1", state="occupied", locid="BR01")

    time.sleep(0.1)

    # Verify state updated
    assert bk.occ == True
    assert bk.locid == "BR01"
    assert bk.state == "occupied"

    com.stop()


def test_clock_synchronization(mock_server):
    """Test clock synchronization"""
    com = Communicator("localhost", 18051)
    model = Model(com)
    com.start()
    model.init()

    callback_called = False
    def time_callback():
        nonlocal callback_called
        callback_called = True

    model.time_callback = time_callback

    # Server sends clock update
    mock_server.send_clock(12, 30)

    time.sleep(0.1)

    assert model.clock.hour == 12
    assert model.clock.minute == 30
    assert callback_called == True

    com.stop()
```

---

## 7. End-to-End Tests

### 7.1 Real Server Tests

```python
# tests/e2e/test_real_server.py

import pytest
import time
from pyrocrail import PyRocrail

@pytest.mark.e2e
@pytest.mark.skip(reason="Requires real Rocrail server")
def test_full_workflow():
    """
    Test complete workflow with real Rocrail server

    Prerequisites:
    - Rocrail server running on localhost:8051
    - Example plan loaded (example_plan/)
    - At least one locomotive configured
    """
    rr = PyRocrail("localhost", 8051)
    rr.start()

    # Power on
    rr.power_on()
    time.sleep(1)

    # Get a locomotive
    lc = rr.model.get_lc("BR01")  # Adjust to your plan

    # Set speed
    lc.set_speed(50)
    time.sleep(2)

    # Stop
    lc.set_speed(0)

    # Power off
    rr.power_off()

    rr.stop()
```

### 7.2 Manual Test Checklist

Create `tests/e2e/MANUAL_TESTS.md`:

```markdown
# Manual Test Checklist

## Prerequisites
- [ ] Rocrail server running on localhost:8051
- [ ] Example plan loaded from example_plan/
- [ ] Physical layout or virtual layout available

## Basic Tests
- [ ] Connection successful
- [ ] Plan loads correctly (all objects parsed)
- [ ] Power on/off works
- [ ] Emergency stop works
- [ ] Auto mode on/off works

## Locomotive Tests
- [ ] Set speed (0-100)
- [ ] Change direction
- [ ] Lights on/off
- [ ] Function control (F1-F28)
- [ ] Dispatch/collect
- [ ] Emergency stop

## Block Tests
- [ ] Reserve block
- [ ] Free block
- [ ] Block state queries
- [ ] Go/stop commands

## Switch Tests
- [ ] Straight position
- [ ] Turnout position
- [ ] Flip operation
- [ ] Lock/unlock

## Signal Tests
- [ ] All aspects (red/green/yellow/white)
- [ ] Auto/manual mode

## Route Tests
- [ ] Activate route
- [ ] Lock/unlock route
- [ ] Test route

## Output Tests
- [ ] Turn on/off
- [ ] Color control (if RGB outputs)

## Feedback Tests
- [ ] Simulate sensor on/off
- [ ] Read sensor state

## Advanced Tests
- [ ] Time-based actions execute on schedule
- [ ] Multiple concurrent operations
- [ ] Long-running stability test (1 hour)
- [ ] Reconnection after network interruption
```

---

## 8. Coverage Requirements

### 8.1 Coverage Targets

- **Overall**: 80% minimum
- **Core objects** (Locomotive, Block, Switch, etc.): 90% minimum
- **Communicator**: 85% minimum
- **Model**: 85% minimum
- **PyRocrail**: 80% minimum

### 8.2 Coverage Configuration

```toml
# Add to pyproject.toml
[tool.coverage.run]
source = ["src/pyrocrail"]
omit = [
    "*/tests/*",
    "*/test_*.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### 8.3 Coverage Commands

```bash
# Run tests with coverage
pytest --cov=src/pyrocrail --cov-report=html --cov-report=term

# View HTML report
# Open htmlcov/index.html in browser

# Generate coverage badge
coverage-badge -o coverage.svg -f
```

---

## 9. Continuous Integration

### 9.1 GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Poetry
      run: |
        curl -sSL https://install.python-poetry.org | python3 -

    - name: Install dependencies
      run: |
        poetry install --with dev

    - name: Run linters
      run: |
        poetry run ruff check src/
        poetry run pyright

    - name: Run unit tests
      run: |
        poetry run pytest tests/unit -v --cov=src/pyrocrail --cov-report=xml

    - name: Run integration tests
      run: |
        poetry run pytest tests/integration -v

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
```

---

## 10. Test Execution

### 10.1 Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With coverage
pytest --cov=src/pyrocrail --cov-report=html

# Specific test file
pytest tests/unit/test_locomotive.py

# Specific test
pytest tests/unit/test_locomotive.py::test_set_speed

# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run in parallel (requires pytest-xdist)
pytest -n auto

# Skip E2E tests
pytest -m "not e2e"
```

### 10.2 Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

echo "Running tests..."
poetry run pytest tests/unit -q

if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

echo "Running linters..."
poetry run ruff check src/

if [ $? -ne 0 ]; then
    echo "Linting failed. Commit aborted."
    exit 1
fi

exit 0
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## 11. Implementation Roadmap

### Phase 1: Foundation ✅ COMPLETED
- ✅ Set up PCAP testing infrastructure
- ✅ Create PCAP parser and analysis tools
- ✅ Extract real XML messages from network captures
- ✅ Create PCAP replay test framework

### Phase 2: State Update Implementation ✅ COMPLETED
- ✅ Implement locomotive state updates
- ✅ Implement feedback state updates
- ✅ Implement block state updates
- ✅ Implement switch state updates
- ✅ Implement signal state updates
- ✅ Implement route state updates
- ✅ Verify with PCAP replay tests (62.5% handling achieved)

### Phase 3: Unit Tests (TODO - Next Priority)
- ⬜ Set up pytest infrastructure
- ⬜ Create conftest.py with basic fixtures
- ⬜ Test all locomotive methods (90% coverage)
- ⬜ Test all block methods (90% coverage)
- ⬜ Test all switch methods (90% coverage)
- ⬜ Test all signal methods (90% coverage)
- ⬜ Test all route methods (90% coverage)
- ⬜ Test all feedback methods (90% coverage)
- ⬜ Test all output methods (90% coverage)

### Phase 4: Integration Tests (TODO)
- ⬜ Mock server implementation (can use PCAP replay approach)
- ⬜ Test communicator connection/disconnection
- ⬜ Test plan loading
- ⬜ Test command flow
- ✅ State update tests (using PCAP)

### Phase 5: CI/CD (TODO)
- ⬜ Set up GitHub Actions
- ⬜ Configure coverage reporting
- ⬜ Add badges to README
- ⬜ Set up pre-commit hooks

### Phase 6: E2E Tests (TODO)
- ⬜ Create manual test documentation
- ⬜ Optional automated E2E tests
- ⬜ Performance benchmarks
- ⬜ Load testing

---

## 12. Success Metrics

### 12.1 Current Achievement (2025-10-17)

**PCAP Testing**:
- ✅ 62.5% of operational messages handled correctly
- ✅ All major state updates (lc, fb, bk, sw, sg, st) working
- ✅ 436 state updates processed in running capture
- ✅ Zero parsing errors
- ✅ Real-world data validation

**Code Quality**:
- ✅ All code passes ruff linting
- ✅ Consistent state update pattern across objects
- ✅ Warning system for unknown objects

### 12.2 Target Metrics (TODO)

**Quantitative**:
- ⬜ 80%+ overall code coverage (currently ~0% with formal tests)
- ⬜ 100% tests passing on all platforms
- ⬜ < 30 seconds total test execution time
- ⬜ Zero flaky tests

**Qualitative**:
- ✅ Confidence in refactoring (PCAP tests catch regressions)
- ✅ Catch regressions early (PCAP replay)
- ⬜ Documentation through tests
- ⬜ Easier onboarding for contributors

---

## 13. Quick Start: Testing PyRocrail Today

### 13.1 PCAP-Based Regression Testing

```bash
# Test with existing captures
python tests/tools/pcap_replay_test.py tests/fixtures/pcap/rocrail_start.txt
python tests/tools/pcap_replay_test.py tests/fixtures/pcap/rocrail_fahren.txt

# Should show 62%+ handled with no state update warnings
```

### 13.2 Manual Testing with Real Rocrail

```python
from pyrocrail import PyRocrail

def on_change(obj_type, obj_id, obj):
    """Log all state changes"""
    print(f"{obj_type} {obj_id} updated")

rr = PyRocrail("localhost", 8051)
rr.model.change_callback = on_change
rr.start()

# Operate layout - you should see real-time updates!
```

### 13.3 Capturing New Test Data

```bash
# Start Wireshark with filter: tcp.port == 8051
# Operate your layout
# Save as: tests/fixtures/pcap/my_test.pcapng

# Extract and test
python tests/tools/pcap_parser.py tests/fixtures/pcap/my_test.pcapng
python tests/tools/pcap_replay_test.py tests/fixtures/pcap/my_test.txt
```

---

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest Best Practices](https://docs.pytest.org/en/latest/goodpractices.html)
- [Python Testing with pytest (Book)](https://pragprog.com/titles/bopytest/python-testing-with-pytest/)
- [Rocrail RCP Protocol](https://wiki.rocrail.net/doku.php?id=develop:cs-protocol-en)
- **[PCAP Testing Guide](./PCAP_TESTING_GUIDE.md)** - How to capture and test with real data
- **[State Update Implementation](./STATE_UPDATE_IMPLEMENTATION.md)** - Current implementation status
