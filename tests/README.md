# PyRocrail Tests

## Test Organization

```
tests/
├── unit/              # Unit tests (no Rocrail server needed)
├── integration/       # Integration tests (require Rocrail server)
├── fixtures/          # Test data (PCAP files)
└── tools/             # Test utilities
```

## Running Tests

### Prerequisites

Extract PCAP fixtures (required for unit tests):

```bash
python tests/tools/pcap_parser.py tests/fixtures/pcap/rocrail_start.pcapng
python tests/tools/pcap_parser.py tests/fixtures/pcap/rocrail_fahren.pcapng
python tests/tools/pcap_parser.py tests/fixtures/pcap/rocrail_schalten.pcapng
python tests/tools/pcap_parser.py tests/fixtures/pcap/rocrail_edit.pcapng
```

This generates `.txt` files that tests use to replay Rocrail communication.

### Unit Tests (No Rocrail Required)

Unit tests use PCAP fixtures and mocks. Run from project root:

```bash
# Run all unit tests
python -m tests.unit.test_trigger_improved
python -m tests.unit.test_trigger_execution
python -m tests.unit.test_trigger_callbacks
python -m tests.unit.test_mock_communicator
python -m tests.unit.test_pcap_state_updates
python -m tests.unit.test_exception_handling
python -m tests.unit.test_model_queries
python -m tests.unit.test_system_commands
```

### Integration Tests (Require Rocrail)

Integration tests need a running Rocrail server:

```bash
# Start Rocrail with Docker
cd docker
docker compose up -d

# Run integration tests from project root
python -m tests.integration.test_automode_multi
python -m tests.integration.test_feedback_sensors
python -m tests.integration.test_block_close

# Or run inside Docker container
docker exec pyrocrail-test-server sh -c "cd /tests && python3 tests/integration/test_automode_multi.py"

# Stop Docker
docker compose down
```

### With Pytest (Optional)

```bash
# Install pytest
pip install pytest

# Run all tests
pytest tests/

# Run specific test directory
pytest tests/unit/
pytest tests/integration/

# Run with verbose output
pytest tests/unit/test_trigger_improved.py -v
```

## Test Types

### Unit Tests
- **test_trigger_*.py**: Time-based and event-based trigger patterns
- **test_pcap_*.py**: PCAP replay and state updates
- **test_mock_communicator.py**: Mock communicator functionality
- **test_exception_handling.py**: Exception message parsing
- **test_model_queries.py**: Model query commands
- **test_system_commands.py**: System control commands (power, auto mode)

### Integration Tests
- **test_automode_multi.py**: Multiple automode moves with stop command
- **test_feedback_sensors.py**: Real feedback sensor control
- **test_block_close.py**: Block state management
- **test_docker_rocrail.py**: Comprehensive Rocrail integration tests (pytest)

## CI/CD

GitHub Actions runs:
1. **lint-and-unit-tests**: Ruff linting + all unit tests
2. **docker-integration-tests**: Docker build + integration tests

See `.github/workflows/pylint.yml` for details.
