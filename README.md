# PyRocrail

Python library for controlling [Rocrail](https://wiki.rocrail.net/) model railway systems.

PyRocrail provides a Pythonic interface to the Rocrail server, allowing you to control locomotives, switches, signals, routes, and other layout objects programmatically. Replace XML scripting with Python for better automation and control.

## Features

- **17 Object Types**: Full support for locomotives, blocks, switches, signals, routes, and more
- **Real-time Control**: Direct TCP/IP communication with Rocrail server
- **Event-Driven**: Action system for time-based and event-based automation
- **Type-Safe**: Complete type annotations for IDE support and error detection
- **Verified Commands**: All commands verified against official Rocrail documentation

## Documentation

- **[Object Reference](OBJECTS.md)** - Complete documentation for all object types with links to official Rocrail docs
- **[Testing Strategy](TESTING_STRATEGY.md)** - Testing approach and guidelines
- **[Examples](examples/)** - Tutorial examples and usage patterns

## Quick Start

```python
from pyrocrail import PyRocrail, Action, Trigger
import time

# Connect to Rocrail using context manager (automatic cleanup)
with PyRocrail("localhost", 8051) as pr:
    # Control a locomotive
    loco = pr.model.get_lc("BR01")
    loco.set_speed(50)
    loco.set_direction(True)
    loco.go()

    # Set a switch
    switch = pr.model.get_sw("SW01")
    switch.turnout()

    # Activate a route
    route = pr.model.get_st("RT01")
    route.set()

    # Time-based action (run at 12:30)
    def morning_announcement(model):
        print("Morning operations starting")

    pr.add(Action(
        script=morning_announcement,
        trigger_type=Trigger.TIME,
        trigger="12:30"
    ))

    # Event-based action (when sensor activates)
    def on_train_detected(model):
        loco = model.get_lc("BR01")
        loco.set_speed(25)  # Slow down

    pr.add(Action(
        script=on_train_detected,
        trigger_type=Trigger.EVENT,
        trigger="FB01",
        condition="obj.state == True"
    ))

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
# Automatically cleaned up when exiting 'with' block
```

## Installation

```bash
# Clone the repository
git clone https://github.com/thetrainroom/py-rocrail.git
cd py-rocrail

# Install with Poetry
poetry install

# Or install with pip
pip install -e .
```

## Supported Objects

See **[OBJECTS.md](OBJECTS.md)** for complete documentation.

| Object | Description | Rocrail Docs |
|--------|-------------|--------------|
| Locomotive | Train engine control | [lc-gen-en](https://wiki.rocrail.net/doku.php?id=lc-gen-en) |
| Block | Track section management | [block-gen-en](https://wiki.rocrail.net/doku.php?id=block-gen-en) |
| Switch | Turnout/point control | [switch-gen-en](https://wiki.rocrail.net/doku.php?id=switch-gen-en) |
| Signal | Signal aspect control | [signal-gen-en](https://wiki.rocrail.net/doku.php?id=signal-gen-en) |
| Route | Path routing | [route-gen-en](https://wiki.rocrail.net/doku.php?id=route-gen-en) |
| Feedback | Sensor detection | [sensor-gen-en](https://wiki.rocrail.net/doku.php?id=sensor-gen-en) |
| Output | Accessory control | [output-gen-en](https://wiki.rocrail.net/doku.php?id=output-gen-en) |
| Car | Rolling stock | [car-gen-en](https://wiki.rocrail.net/doku.php?id=car-gen-en) |
| Operator | Train compositions ("Trains" in GUI) | [operator-gen-en](https://wiki.rocrail.net/doku.php?id=operator-gen-en) |
| Schedule | Timetables | [schedule-gen-en](https://wiki.rocrail.net/doku.php?id=schedule-gen-en) |
| Stage | Staging yards | [stage-details-en](https://wiki.rocrail.net/doku.php?id=stage-details-en) |
| Text | Information displays | [text-gen-en](https://wiki.rocrail.net/doku.php?id=text-gen-en) |
| Booster | Power districts | [booster-gen-en](https://wiki.rocrail.net/doku.php?id=booster-gen-en) |
| Variable | Global variables | [variable-gen-en](https://wiki.rocrail.net/doku.php?id=variable-gen-en) |
| Weather | Atmospheric effects | [weather-gen-en](https://wiki.rocrail.net/doku.php?id=weather-gen-en) |

Plus: Tour, Location, and more...

## Development

```bash
# Run linter
ruff check $(git ls-files '*.py')

# Run type checker
pyright src/pyrocrail

# Format code
black --line-length 180 src/
```

## References

- [Rocrail Wiki](https://wiki.rocrail.net/)
- [XMLScript Documentation](https://wiki.rocrail.net/doku.php?id=xmlscripting-en)
- [Rocrail Protocol](https://wiki.rocrail.net/doku.php?id=develop:cs-protocol-en)

## License

See LICENSE file for details
