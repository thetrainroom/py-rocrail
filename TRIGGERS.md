# PyRocrail Triggers and Actions Guide

Complete reference for creating time-based and event-based automation in PyRocrail.

## Table of Contents

1. [Overview](#overview)
2. [Action Basics](#action-basics)
3. [Time-Based Triggers](#time-based-triggers)
4. [Event-Based Triggers](#event-based-triggers)
5. [Writing Conditions](#writing-conditions)
6. [Helper Functions Reference](#helper-functions-reference)
7. [Examples](#examples)
8. [Best Practices](#best-practices)

---

## Overview

PyRocrail's action system allows you to automate your model railway based on:
- **Time triggers**: Execute actions at specific times
- **Event triggers**: Execute actions when object states change
- **Conditions**: Filter when actions execute using Python expressions

### Basic Structure

```python
from pyrocrail import PyRocrail, Action, Trigger

with PyRocrail("localhost", 8051) as pr:
    # Define what to do
    def my_action(model):
        print("Action executed!")
        loco = model.get_lc("BR01")
        loco.set_speed(50)

    # Define when to do it
    pr.add(Action(
        script=my_action,              # What to execute
        trigger_type=Trigger.TIME,     # When: TIME or EVENT
        trigger="12:30",                # Trigger pattern
        condition="is_daytime()",       # Optional condition
        timeout=60                      # Maximum execution time (seconds)
    ))
```

---

## Action Basics

### Action Parameters

```python
Action(
    script=callable,           # Required: Function(model) to execute
    trigger_type=Trigger,      # Required: Trigger.TIME or Trigger.EVENT
    trigger=str,               # Optional: Pattern (default "*" matches all)
    condition=str,             # Optional: Python expression (default always true)
    timeout=int|float,         # Optional: Max execution time in seconds (default 60)
    on_success=callable,       # Optional: Callback(result, elapsed) on success
    on_error=callable          # Optional: Callback(exception, elapsed) on error
)
```

### Your Script Function

```python
def my_script(model):
    """
    Your script receives the Model object

    Args:
        model: Full access to all layout objects
    """
    # Access any object
    loco = model.get_lc("locomotive_id")
    block = model.get_bk("block_id")
    switch = model.get_sw("switch_id")

    # Check clock
    hour = model.clock.hour
    minute = model.clock.minute

    # Control objects
    loco.set_speed(50)
    switch.turnout()
```

---

## Time-Based Triggers

Execute actions based on the Rocrail fast clock.

### Time Patterns

```python
# Exact time
trigger="12:30"           # Execute at 12:30

# Every hour at specific minute
trigger="*:00"            # Every hour at :00 (8:00, 9:00, 10:00, ...)
trigger="*:15"            # Every hour at :15 (8:15, 9:15, 10:15, ...)
trigger="*:30"            # Every hour at :30

# Specific hour, any minute
trigger="12:*"            # Every minute from 12:00 to 12:59

# Interval patterns
trigger="*/2:00"          # Every 2 hours at :00 (0:00, 2:00, 4:00, ...)
trigger="*/3:30"          # Every 3 hours at :30 (0:30, 3:30, 6:30, ...)
trigger="*:*/15"          # Every 15 minutes (0:00, 0:15, 0:30, ...)
trigger="*:*/5"           # Every 5 minutes

# Every clock update
trigger="*:*"             # Every time the clock updates
trigger="*"               # Same as "*:*"
trigger=None              # Same as "*:*"
```

### Time Examples

```python
# Morning startup at 8:00
pr.add(Action(
    script=morning_routine,
    trigger_type=Trigger.TIME,
    trigger="8:0"
))

# Hourly status report
pr.add(Action(
    script=hourly_report,
    trigger_type=Trigger.TIME,
    trigger="*:0"
))

# Every 15 minutes, but only during daytime
pr.add(Action(
    script=quarter_hour_check,
    trigger_type=Trigger.TIME,
    trigger="*:*/15",
    condition="is_daytime()"
))
```

---

## Event-Based Triggers

Execute actions when object states change. PyRocrail monitors **16 object types**.

### Supported Object Types

| Type | Description | Example IDs |
|------|-------------|-------------|
| `lc` | Locomotives | "BR01", "express1" |
| `bk` | Blocks | "station", "platform1" |
| `sw` | Switches | "SW01", "entry_switch" |
| `sg` | Signals | "SG01", "entry_signal" |
| `st` | Routes | "RT01", "main_route" |
| `fb` | Feedback sensors | "FB01", "sensor1" |
| `co` | Outputs | "lights", "crossing" |
| `car` | Cars | "boxcar1", "tanker2" |
| `operator` | Trains | "freight1", "express" |
| `sc` | Schedules | "morning", "rush_hour" |
| `sb` | Stage blocks | "staging1", "yard" |
| `text` | Text displays | "station_board" |
| `bstr` | Boosters | "booster1", "main_power" |
| `vr` | Variables | "counter", "state_var" |
| `tour` | Tours | "demo_tour" |
| `location` | Locations | "city1", "depot" |
| `weather` | Weather | "weather1" |

### Event Patterns

```python
# Exact match - specific object
trigger="FB01"                    # Only sensor FB01

# Wildcard patterns - multiple objects
trigger="fb*"                     # All feedback sensors (fb01, fb02, fb_entry, ...)
trigger="station*"                # All objects starting with "station"
trigger="*_main"                  # All objects ending with "_main"
trigger="block_*_entry"           # Pattern matching

# Any object (use with conditions!)
trigger="*"                       # ALL object changes (filter in condition)
```

### Event Examples

```python
# Sensor activation
pr.add(Action(
    script=on_sensor_active,
    trigger_type=Trigger.EVENT,
    trigger="FB01",
    condition="obj.state == True"    # Only when activating (not deactivating)
))

# Any block occupation
pr.add(Action(
    script=on_block_occupied,
    trigger_type=Trigger.EVENT,
    trigger="bk*",                   # All blocks
    condition="is_occupied(obj_id)"  # Only when becoming occupied
))

# Locomotive speed changes
pr.add(Action(
    script=on_speed_change,
    trigger_type=Trigger.EVENT,
    trigger="lc*",                   # All locomotives
    condition="speed_above(obj_id, 50)"  # Only when speed > 50
))

# Cross-object trigger
pr.add(Action(
    script=complex_trigger,
    trigger_type=Trigger.EVENT,
    trigger="*",                     # Any object
    condition="""
        obj_type == 'fb' and
        obj.state == True and
        is_straight('entry_switch') and
        is_green('entry_signal')
    """
))
```

---

## Writing Conditions

Conditions are Python expressions that must evaluate to `True` for the action to execute.

### Available Variables

**In ALL conditions:**
```python
hour          # Current Rocrail clock hour (0-23)
minute        # Current Rocrail clock minute (0-59)
time          # Hour + minute/60.0 as float
model         # Full Model object with all getters
```

**In EVENT conditions only:**
```python
obj_type      # Object type string ("fb", "bk", "lc", etc.)
obj_id        # Object ID string
obj           # The actual object that changed
```

### Condition Styles

#### Old Style (Direct Python)

```python
# Verbose but explicit
condition="obj.state == True"
condition="hasattr(obj, 'occ') and obj.occ == True"
condition="model.get_sw('SW01').state == 'straight'"
condition="9 <= hour <= 17"
```

#### New Style (Helper Functions)

```python
# Clean and readable
condition="is_active(obj_id)"
condition="is_occupied(obj_id)"
condition="is_straight('SW01')"
condition="time_between(9, 17)"
```

#### Mixing Both Styles

```python
# You can combine helpers with Python expressions
condition="is_occupied('platform1') and obj.V < 30"
condition="is_daytime() and count_moving() < 5"
condition="is_active(obj_id) or speed_above('loco1', 50)"
```

---

## Helper Functions Reference

All helper functions are available in conditions. They handle missing objects gracefully (return `False` instead of raising exceptions).

### Sensor/Feedback Helpers

```python
is_active(obj_id)         # True if sensor is on/active
is_inactive(obj_id)       # True if sensor is off/inactive

# Examples:
condition="is_active('FB01')"
condition="is_inactive('entry_sensor')"
```

### Block Helpers

```python
is_occupied(block_id)     # True if block is occupied
is_free(block_id)         # True if block is free (not occupied)
is_reserved(block_id)     # True if block is reserved

# Examples:
condition="is_occupied('platform1')"
condition="is_free('next_block') and is_green('entry_signal')"
```

### Switch Helpers

```python
is_straight(switch_id)    # True if switch in straight position
is_turnout(switch_id)     # True if switch in turnout position
is_left(switch_id)        # True if 3-way switch in left position
is_right(switch_id)       # True if 3-way switch in right position

# Examples:
condition="is_straight('SW01')"
condition="is_turnout('entry') or is_turnout('exit')"
```

### Signal Helpers

```python
is_red(signal_id)         # True if signal showing red
is_green(signal_id)       # True if signal showing green
is_yellow(signal_id)      # True if signal showing yellow
is_white(signal_id)       # True if signal showing white/shunt

# Examples:
condition="is_green('entry_signal') and is_green('exit_signal')"
condition="is_red('stop_signal')"
```

### Locomotive Helpers

```python
is_moving(loco_id)                      # True if speed > 0
is_stopped(loco_id)                     # True if speed == 0
is_forward(loco_id)                     # True if direction is forward
is_reverse(loco_id)                     # True if direction is reverse
speed_above(loco_id, threshold)         # True if speed > threshold
speed_below(loco_id, threshold)         # True if speed < threshold
speed_between(loco_id, min, max)        # True if min <= speed <= max

# Examples:
condition="is_moving('BR01')"
condition="speed_above('express1', 50)"
condition="speed_between('freight', 10, 30)"
condition="is_reverse('shunter') and speed_below('shunter', 20)"
```

### Route Helpers

```python
is_locked(route_id)       # True if route is locked
is_unlocked(route_id)     # True if route is unlocked

# Examples:
condition="is_unlocked('main_route')"
```

### Output Helpers

```python
is_on(output_id)          # True if output is on
is_off(output_id)         # True if output is off

# Examples:
condition="is_on('station_lights')"
condition="is_off('crossing_signal')"
```

### Collection/Counting Helpers

```python
count_occupied()                  # Number of occupied blocks
count_active(obj_type="fb")       # Number of active objects (fb or co)
count_moving()                    # Number of moving locomotives
any_moving()                      # True if any locomotive is moving
all_stopped()                     # True if all locomotives are stopped
loco_in_block(loco_id, block_id)  # True if specific loco in specific block
block_has_loco(block_id)          # True if block has any locomotive

# Examples:
condition="count_moving() < 3"
condition="any_moving()"
condition="loco_in_block('BR01', 'platform1')"
condition="count_active('fb') > 5"
```

### Logic Helpers

```python
any_of(checks)            # OR logic - True if any check is True
all_of(checks)            # AND logic - True if all checks are True
none_of(checks)           # NOT OR - True if no checks are True

# Examples:
condition="any_of([is_active('FB01'), is_active('FB02')])"
condition="all_of([is_straight('SW01'), is_green('SG01'), is_free('BK01')])"
condition="none_of([is_moving('loco1'), is_moving('loco2')])"
```

### Time Helpers

```python
time_between(start, end)  # True if start <= hour <= end (handles midnight wrap)
is_daytime()              # True if 6:00 to 20:00
is_nighttime()            # True if 20:00 to 6:00

# Examples:
condition="time_between(8, 17)"       # Business hours
condition="time_between(22, 6)"       # Night (wraps midnight)
condition="is_daytime() and is_moving('passenger1')"
```

---

## Examples

### Simple Examples

```python
# Sensor activates - turn on lights
pr.add(Action(
    script=lambda model: model.get_co('lights').on(),
    trigger_type=Trigger.EVENT,
    trigger="entry_sensor",
    condition="is_active(obj_id)"
))

# Every hour - status report
pr.add(Action(
    script=hourly_status,
    trigger_type=Trigger.TIME,
    trigger="*:0"
))

# Block occupied - slow down approaching train
def slow_approach(model):
    if block_has_loco('approach_block'):
        loco_id = model.get_bk('approach_block').locid
        model.get_lc(loco_id).set_speed(20)

pr.add(Action(
    script=slow_approach,
    trigger_type=Trigger.EVENT,
    trigger="approach_block",
    condition="is_occupied(obj_id)"
))
```

### Medium Complexity

```python
# Platform departure - only if route is clear
def platform_departure(model):
    loco = model.get_lc('express1')
    loco.set_speed(50)
    loco.go()

pr.add(Action(
    script=platform_departure,
    trigger_type=Trigger.EVENT,
    trigger="platform1",
    condition="""
        is_occupied(obj_id) and
        is_straight('exit_switch') and
        is_green('exit_signal') and
        is_free('next_block')
    """
))

# Crossing protection - activate when train approaches
def activate_crossing(model):
    model.get_co('crossing_lights').on()
    model.get_co('crossing_bell').on()

pr.add(Action(
    script=activate_crossing,
    trigger_type=Trigger.EVENT,
    trigger="fb*",
    condition="""
        is_active(obj_id) and
        obj_id in ['approach_fb1', 'approach_fb2'] and
        any_moving()
    """
))
```

### Complex Examples

```python
# Advanced interlocking with multiple conditions
def station_entry_control(model):
    """Only allow entry if all conditions met"""
    route = model.get_st('station_entry')
    route.set()
    signal = model.get_sg('entry_signal')
    signal.green()

pr.add(Action(
    script=station_entry_control,
    trigger_type=Trigger.EVENT,
    trigger="*",  # Monitor everything
    condition="""
        obj_type == 'fb' and
        obj_id == 'approach_sensor' and
        is_active(obj_id) and
        all_of([
            is_free('platform1'),
            is_free('platform2'),
            is_straight('station_entry_sw'),
            is_unlocked('station_entry'),
            count_occupied() < 10
        ]) and
        time_between(6, 22) and
        count_moving() < 5
    """
))

# Rush hour operations
def rush_hour_mode(model):
    """Different behavior during rush hours"""
    if time_between(7, 9) or time_between(17, 19):
        # Increase frequency
        for loco_id in ['commuter1', 'commuter2', 'commuter3']:
            if is_stopped(loco_id):
                model.get_lc(loco_id).go()
    else:
        # Normal operations
        pass

pr.add(Action(
    script=rush_hour_mode,
    trigger_type=Trigger.TIME,
    trigger="*:*/5",  # Check every 5 minutes
    condition="is_daytime()"
))

# Emergency stop on multiple conditions
def emergency_handler(model):
    """Stop everything if problems detected"""
    print("EMERGENCY: Stopping all trains")
    for loco in model.get_locomotives().values():
        loco.stop()
    model.emergency_stop()

pr.add(Action(
    script=emergency_handler,
    trigger_type=Trigger.EVENT,
    trigger="*",
    condition="""
        (
            (obj_type == 'bstr' and is_off(obj_id)) or
            (count_occupied() > 15) or
            (obj_type == 'bk' and is_occupied(obj_id) and
             block_has_loco(obj_id) and count_moving() == 0)
        )
    """
))
```

---

## Best Practices

### 1. Use Helper Functions

**Good:**
```python
condition="is_occupied('platform1') and is_green('signal1')"
```

**Bad:**
```python
condition="hasattr(model.get_bk('platform1'), 'occ') and model.get_bk('platform1').occ and model.get_sg('signal1').aspect == 'green'"
```

### 2. Filter Events Early

**Good (specific trigger):**
```python
trigger="fb*"
condition="is_active(obj_id)"
```

**Bad (too broad):**
```python
trigger="*"  # Fires on EVERY object change!
condition="obj_type == 'fb' and obj.state == True"
```

### 3. Combine Related Checks

**Good:**
```python
condition="all_of([is_straight('SW01'), is_green('SG01'), is_free('BK01')])"
```

**Acceptable:**
```python
condition="is_straight('SW01') and is_green('SG01') and is_free('BK01')"
```

### 4. Handle Errors with Callbacks

```python
def on_success(result, elapsed):
    print(f"Action completed in {elapsed:.2f}s")

def on_error(exception, elapsed):
    print(f"Action failed after {elapsed:.2f}s: {exception}")

pr.add(Action(
    script=my_action,
    trigger_type=Trigger.EVENT,
    trigger="FB01",
    on_success=on_success,
    on_error=on_error
))
```

### 5. Use Meaningful Names

```python
# Good
def morning_station_lights(model):
    """Turn on station lights at 6am"""
    model.get_co('platform_lights').on()
    model.get_co('waiting_room_lights').on()

# Bad
def func1(model):
    model.get_co('co1').on()
```

### 6. Test Conditions Incrementally

```python
# Start simple
condition="is_active(obj_id)"

# Add complexity gradually
condition="is_active(obj_id) and is_daytime()"

# Build up to complex
condition="is_active(obj_id) and is_daytime() and is_straight('SW01')"
```

### 7. Document Complex Conditions

```python
pr.add(Action(
    script=complex_action,
    trigger_type=Trigger.EVENT,
    trigger="*",
    condition="""
        # Only during daytime operations
        is_daytime() and
        # Station platform must be free
        is_free('platform1') and
        # Entry route must be set correctly
        is_straight('entry_switch') and
        is_green('entry_signal') and
        # Not too many trains active
        count_moving() < 5
    """
))
```

### 8. Use Verbose Mode for Debugging

```python
# Enable verbose mode to see condition failures
pr = PyRocrail("localhost", 8051, verbose=True)

# You'll see:
# "Warning: Event condition evaluation failed: is_occupied('invalid_block')"
# "  Error: ..."
```

---

## Complete Reference

### All Object Types That Fire Events

```python
"lc"        # Locomotives (speed, direction, position changes)
"bk"        # Blocks (occupation, reservation changes)
"sw"        # Switches (position changes)
"sg"        # Signals (aspect changes)
"st"        # Routes (state changes)
"fb"        # Feedback sensors (activation/deactivation)
"car"       # Cars (status, location changes)
"operator"  # Operators/Trains (composition changes)
"sc"        # Schedules (state changes)
"sb"        # Stage blocks (occupation changes)
"text"      # Text displays (content changes)
"bstr"      # Boosters (power state changes)
"vr"        # Variables (value changes)
"tour"      # Tours (state changes)
"location"  # Locations (state changes)
"weather"   # Weather (condition changes)
```

**Note:** Outputs (`"co"`) currently don't fire events (planned feature).

### Time Pattern Reference

| Pattern | Description | Example Times |
|---------|-------------|---------------|
| `"12:30"` | Exact time | 12:30 only |
| `"*:00"` | Every hour at :00 | 0:00, 1:00, 2:00, ... |
| `"*:15"` | Every hour at :15 | 0:15, 1:15, 2:15, ... |
| `"*/2:00"` | Every 2 hours at :00 | 0:00, 2:00, 4:00, ... |
| `"*/3:30"` | Every 3 hours at :30 | 0:30, 3:30, 6:30, ... |
| `"*:*/5"` | Every 5 minutes | 0:00, 0:05, 0:10, ... |
| `"*:*/15"` | Every 15 minutes | 0:00, 0:15, 0:30, ... |
| `"*:*"` | Every clock update | Every update |

---

## Troubleshooting

### Action Not Firing

1. **Check trigger pattern**: Does it match your object ID?
   ```python
   # Wrong: trigger="FB01" but your sensor is "fb01" (case sensitive!)
   # Right: trigger="fb*" (matches all)
   ```

2. **Check condition**: Enable verbose mode
   ```python
   pr = PyRocrail("localhost", 8051, verbose=True)
   ```

3. **Verify object exists**:
   ```python
   print(pr.model.get_feedbacks().keys())  # List all sensor IDs
   print(pr.model.get_blocks().keys())     # List all block IDs
   ```

### Condition Always False

1. **Check helper function names** (no typos)
2. **Verify object IDs are correct**
3. **Test condition parts separately**:
   ```python
   # Instead of:
   condition="is_straight('SW01') and is_green('SG01')"

   # Try one at a time:
   condition="is_straight('SW01')"
   # Then:
   condition="is_green('SG01')"
   ```

### Performance Issues

1. **Avoid trigger="*" when possible** - Too broad!
2. **Use specific triggers**: `trigger="fb*"` instead of `trigger="*"`
3. **Keep conditions simple** - Complex expressions slow down evaluation
4. **Use timeout parameter** to prevent runaway scripts

---

## See Also

- [OBJECTS.md](OBJECTS.md) - Complete object reference
- [README.md](README.md) - Quick start guide
- [examples/](examples/) - Tutorial examples
- [Rocrail XMLScript Documentation](https://wiki.rocrail.net/doku.php?id=xmlscripting-en)

---

**Happy Automating! 🚂**
