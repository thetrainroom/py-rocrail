# Rocrail Docker Test Environment

This Docker setup provides a Rocrail server instance for testing PyRocrail without requiring physical model railway hardware.

## Overview

The Docker container runs:
- **Rocrail server** in headless mode (no GUI)
- **Virtual Command Station (VCS)** for simulation (no hardware needed)
- **Example plan** with all major object types (locomotives, blocks, switches, signals, etc.)
- **Port 8051** exposed for TCP/IP connections

## Quick Start

### 1. Build and Start the Container

```bash
cd docker
docker-compose up -d
```

This will:
- Build the Rocrail Docker image
- Start the Rocrail server with the example plan
- Expose port 8051 on localhost

### 2. Test Connection with PyRocrail

```python
from pyrocrail.pyrocrail import PyRocrail

# Connect to the Docker Rocrail server
pr = PyRocrail("localhost", 8051)
pr.start()

# Test basic commands
pr.power_on()
pr.model.get_lc("Loc1").set_speed(50)
pr.model.get_sw("sw1").turnout()
pr.model.get_sg("sg1").green()

# Stop when done
pr.stop()
```

### 3. View Logs

```bash
# Follow server logs
docker-compose logs -f rocrail

# View traces (detailed debug logs)
docker-compose exec rocrail ls -la /rocrail/traces
```

### 4. Stop the Container

```bash
docker-compose down
```

## Example Plan Contents

The example plan (`../example_plan/plan.xml`) includes:

- **1 Locomotive** (`Loc1`) - addr 3, DCC protocol
- **1 Car** (`Car1`) - Passenger lounge car
- **1 Operator/Train** (`Train`) - Train composition with Car1
- **1 Feedback Sensor** (`fb1`) - Using VCS (Virtual Command Station)
- **1 Switch** (`sw1`) - Left-hand turnout
- **1 Signal** (`sg1`) - Light signal, main type
- **1 Block** (`bk1`) - Standard block
- **1 Stage Block** (`sb1`) - Staging yard with fb1 as entrance
- **1 Output** (`co1`) - Control output
- **1 Schedule** (`NEW`) - Route through bk1 and sb1

## Configuration

### Rocrail Server Settings

The Dockerfile runs Rocrail with these options:

```
rocrail -console -w /rocrail/config -l /rocrail/traces
```

- `-console`: Headless mode (no GUI)
- `-w /rocrail/config`: Workspace directory with plan.xml
- `-l /rocrail/traces`: Trace/log directory

### Virtual Command Station

The example plan is pre-configured to use Virtual Command Station (VCS):
- Interface ID: `vcs-1`
- No physical hardware required
- Simulates DCC commands and feedback

## Integration Testing

### Run All Tests Against Docker Server

```bash
# Start the Docker server
cd docker
docker-compose up -d

# Wait for server to be ready
sleep 5

# Run PyRocrail tests
cd ..
python -m pytest tests/ -v

# Or run individual test scripts
python test_system_commands.py
python test_model_queries.py
python test_exception_handling.py
```

### Create Integration Test

```python
import pytest
from pyrocrail.pyrocrail import PyRocrail

@pytest.fixture
def rocrail_server():
    """Connect to Docker Rocrail server"""
    pr = PyRocrail("localhost", 8051)
    pr.start()
    yield pr
    pr.stop()

def test_locomotive_control(rocrail_server):
    """Test controlling a locomotive"""
    pr = rocrail_server

    # Get locomotive from model
    loco = pr.model.get_lc("Loc1")

    # Power on
    pr.power_on()

    # Set speed
    loco.set_speed(30)

    # Change direction
    loco.set_direction(forward=False)

    # Stop
    loco.stop()

    # Power off
    pr.power_off()
```

## Troubleshooting

### Container won't start

Check if port 8051 is already in use:
```bash
# Windows
netstat -ano | findstr :8051

# Linux/Mac
lsof -i :8051
```

### Connection refused

Ensure the container is running:
```bash
docker-compose ps
```

View server logs for errors:
```bash
docker-compose logs rocrail
```

### Plan not loading

Check if the example_plan directory is mounted correctly:
```bash
docker-compose exec rocrail ls -la /rocrail/config
```

## Advanced Usage

### Custom Plan

To test with your own Rocrail plan:

1. Place your plan files in a directory (e.g., `my_plan/`)
2. Update `docker-compose.yml`:
   ```yaml
   volumes:
     - ./my_plan:/rocrail/config:ro
   ```
3. Restart the container:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Different Rocrail Version

Build with a specific Rocrail version:

```bash
docker build --build-arg ROCRAIL_VERSION=2.1.4100 -t rocrail:custom .
```

Update `docker-compose.yml` to use the custom image:
```yaml
services:
  rocrail:
    image: rocrail:custom
    # Remove build section
```

### Network Access from Other Machines

To allow connections from other machines on your network:

Update `docker-compose.yml`:
```yaml
ports:
  - "0.0.0.0:8051:8051"  # Bind to all interfaces
```

**Warning**: This exposes Rocrail to your network. Use with caution.

## Resources

- [Rocrail Wiki](https://wiki.rocrail.net/)
- [Rocrail RCP Protocol](https://wiki.rocrail.net/doku.php?id=develop:cs-protocol-en)
- [PyRocrail Documentation](../README.md)
- [Virtual Command Station](https://wiki.rocrail.net/doku.php?id=virtual-en)

## License

This Docker setup is part of the PyRocrail project. See the main repository for license information.
