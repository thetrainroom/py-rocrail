# PyRocrail Examples

This directory contains example scripts demonstrating PyRocrail functionality.

## Prerequisites

All examples require:
1. **Rocrail server** running (default: `localhost:8051`)
2. **Python 3.12+** with PyRocrail installed: `pip install -e .`

### Docker Setup (Recommended for Testing)

```bash
cd docker
docker compose up -d
```

This starts Rocrail with the demo plan (3 locomotives, 8 blocks).

## Examples

### 01_simple_connection.py
**Basic connection and model inspection**

Shows how to:
- Connect to Rocrail
- Wait for model to load
- List locomotives, blocks, switches, etc.
- Control power on/off

```bash
python examples/01_simple_connection.py
```

### 02_automode_control.py
**Automatic train control**

Demonstrates:
- Finding a locomotive in a block
- Enabling automatic mode
- Starting a locomotive with `go()` command
- Monitoring locomotive movement
- Stopping and cleaning up

```bash
python examples/02_automode_control.py
```

**Requirements**: Locomotive placed in a block with configured routes.

### 03_time_triggers.py
**Time-based automation**

Shows how to:
- Register actions that execute at specific times
- Use wildcards for hourly/periodic triggers
- Schedule morning startup / evening shutdown
- Speed up Rocrail clock for testing

```bash
python examples/03_time_triggers.py
```

**Triggers demonstrated**:
- `hour="*", minute="0"` - Every hour at XX:00
- `hour="8", minute="0"` - Specific time (08:00)
- `hour="*", minute="*/15"` - Every 15 minutes

### 04_event_triggers.py
**Event-based automation**

Demonstrates:
- Feedback sensor activation events
- Block occupation events
- Switch change events
- Locomotive arrival at specific blocks

```bash
python examples/04_event_triggers.py
```

**Triggers demonstrated**:
- `Trigger.FB, fb_id="*", fb_state="true"` - Any sensor ON
- `Trigger.BK, bk_id="*", bk_occ="true"` - Any block occupied
- `Trigger.SW, sw_id="*"` - Any switch changed

### basic_usage.py
**Comprehensive API reference**

Complete examples of:
- Locomotive control (speed, direction, functions)
- Switch control (straight, turnout, flip)
- Signal control (red, yellow, green)
- Route control (set, free, check status)
- Block control (reserve, free, check occupation)
- Feedback sensor control
- Output control
- Automation scripts

```bash
python examples/basic_usage.py
```

**Note**: Edit the file to uncomment specific examples you want to run.

## Running Examples with Docker

If using Docker Rocrail:

```bash
# Start Docker Rocrail
cd docker && docker compose up -d

# Run example from host
python examples/01_simple_connection.py

# Or run inside Docker container
docker exec pyrocrail-test-server python3 /tests/examples/01_simple_connection.py
```

## Customizing Examples

All examples use placeholder IDs like `"loco1"`, `"station1"`, etc.

To use with your layout:
1. Open the example file
2. Replace placeholder IDs with your actual object IDs
3. Check your Rocrail plan for available locomotives, blocks, etc.

Find your object IDs in Rocrail:
- **Locomotives**: Tables → Locomotives → ID column
- **Blocks**: Tables → Blocks → ID column
- **Switches**: Tables → Switches → ID column
- **Signals**: Tables → Signals → ID column

## Troubleshooting

### Connection fails
```
Error: [Errno 111] Connection refused
```
- Ensure Rocrail is running on `localhost:8051`
- Check Rocrail Server settings (Rocrail → Services → TCP)

### Object not found
```
KeyError: 'loco1'
```
- Replace `'loco1'` with an actual ID from your layout
- Check Tables → Locomotives in Rocrail for valid IDs

### Automode doesn't work
- Ensure VCS (Virtual Command Station) is configured
- Check that blocks have configured routes between them
- Place locomotive in a block before starting automode

## Next Steps

After trying these examples:

1. **Read the tests**: `tests/integration/` has more advanced examples
2. **Check documentation**: See main README.md for full API
3. **Build your own**: Copy and modify examples for your layout

## Getting Help

- **GitHub Issues**: https://github.com/anthropics/pyrocrail/issues
- **Rocrail Wiki**: https://wiki.rocrail.net/
- **PyRocrail Docs**: See repository README.md
