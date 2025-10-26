# PyRocrail Object Reference

Complete reference for all PyRocrail object classes with links to official Rocrail documentation.

**Last Updated**: 2025-10-20

---

## Quick Reference

| Object | Element | Description | Rocrail Docs |
|--------|---------|-------------|--------------|
| [Locomotive](#locomotive) | `<lc>` | Train engine control | [lc-gen-en](https://wiki.rocrail.net/doku.php?id=lc-gen-en) |
| [Block](#block) | `<bk>` | Track block management | [block-gen-en](https://wiki.rocrail.net/doku.php?id=block-gen-en) |
| [Switch](#switch) | `<sw>` | Turnout/point control | [switch-gen-en](https://wiki.rocrail.net/doku.php?id=switch-gen-en) |
| [Signal](#signal) | `<sg>` | Signal aspect control | [signal-gen-en](https://wiki.rocrail.net/doku.php?id=signal-gen-en) |
| [Route](#route) | `<st>` | Route/path control | [route-gen-en](https://wiki.rocrail.net/doku.php?id=route-gen-en) |
| [Feedback](#feedback) | `<fb>` | Sensor/detector input | [sensor-gen-en](https://wiki.rocrail.net/doku.php?id=sensor-gen-en) |
| [Output](#output) | `<co>` | Accessory output control | [output-gen-en](https://wiki.rocrail.net/doku.php?id=output-gen-en) |
| [Car](#car) | `<car>` | Rolling stock management | [car-gen-en](https://wiki.rocrail.net/doku.php?id=car-gen-en) |
| [Operator](#operator) | `<operator>` | Train composition ("Trains" in GUI) | [operator-gen-en](https://wiki.rocrail.net/doku.php?id=operator-gen-en) |
| [Schedule](#schedule) | `<sc>` | Timetable/schedule | [schedule-gen-en](https://wiki.rocrail.net/doku.php?id=schedule-gen-en) |
| [Stage](#stage) | `<sb>` | Staging yard block | [stage-details-en](https://wiki.rocrail.net/doku.php?id=stage-details-en) |
| [Text](#text) | `<tx>` | Information display | [text-gen-en](https://wiki.rocrail.net/doku.php?id=text-gen-en) |
| [Booster](#booster) | `<booster>` | Power district control | [booster-gen-en](https://wiki.rocrail.net/doku.php?id=booster-gen-en) |
| [Variable](#variable) | `<vr>` | Global variable storage | [variable-gen-en](https://wiki.rocrail.net/doku.php?id=variable-gen-en) |
| [Tour](#tour) | `<tour>` | Automated demo sequences | [tour-gen-en](https://wiki.rocrail.net/doku.php?id=tour-gen-en) |
| [Location](#location) | `<location>` | Geographic tracking | [location-gen-en](https://wiki.rocrail.net/doku.php?id=location-gen-en) |
| [Weather](#weather) | `<weather>` | Atmospheric effects | [weather-gen-en](https://wiki.rocrail.net/doku.php?id=weather-gen-en) |
| [Action](#action) | `<action>` | Event-driven scripts | [actions-en](https://wiki.rocrail.net/doku.php?id=actions-en) |

---

## Locomotive

**Element**: `<lc>` | **File**: `src/pyrocrail/objects/locomotive.py`

**Description**: Locomotive objects represent train engines and provide control over speed, direction, functions, and automatic operation.

**Official Documentation**:
- [Locomotive Properties](https://wiki.rocrail.net/doku.php?id=lc-gen-en)
- [XMLScript Locomotive Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#locomotive)

### Methods

#### Manual Control
```python
loco.set_speed(speed: int) -> None
```
Set locomotive speed (0-100).

```python
loco.set_direction(forward: bool) -> None
```
Set direction (True=forward, False=reverse).

```python
loco.stop() -> None
```
Emergency stop (speed to 0).

```python
loco.set_function(fn_num: int, state: bool) -> None
```
Control function (F0-F31). Uses `<fn>` tag format with all function states as required by Rocrail protocol.

```python
loco.go_forward(speed: int | None = None) -> None
loco.go_reverse(speed: int | None = None) -> None
```
Convenience methods for directional movement.

#### Automatic Control
```python
loco.go() -> None
```
Start locomotive in automatic mode (cmd="go").

```python
loco.dispatch() -> None
```
Dispatch for automatic control (cmd="dispatch").

#### Schedule Management
```python
loco.use_schedule(schedule_id: str) -> None
```
Assign schedule to locomotive (cmd="useschedule").

```python
loco.regularreset() -> None
```
Remove assigned schedule (cmd="regularreset").

```python
loco.softreset() -> None
```
Soft reset locomotive (cmd="softreset").

#### Train/Class Management
```python
loco.swap() -> None
```
Swap/reverse direction (cmd="swap").

```python
loco.set_class(class_name: str | None = None) -> None
```
Set or clear locomotive class (cmd="classset").

```python
loco.assign_train(train_id: str) -> None
```
Assign train/operator (cmd="assigntrain").

```python
loco.release_train() -> None
```
Release train/operator (cmd="releasetrain").

### Key Attributes
- `idx`: Locomotive ID
- `V`: Current speed (0-100)
- `dir`: Direction (True=forward, False=reverse)
- `addr`: DCC address
- `V_max`, `V_min`, `V_mid`: Speed limits
- `fn`: Dictionary of function states
- `train`: Assigned train/operator ID
- `mode`: Operating mode

### Example Usage
```python
# Get locomotive
loco = pr.model.get_lc("BR01")

# Manual control
loco.set_speed(50)
loco.set_direction(True)
loco.set_function(0, True)  # Lights on

# Automatic mode
loco.use_schedule("morning_commute")
loco.dispatch()
loco.go()

# Train assignment
loco.assign_train("freight_01")
```

---

## Block

**Element**: `<bk>` | **File**: `src/pyrocrail/objects/block.py`

**Description**: Block objects represent track sections for train detection, reservation, and automatic routing.

**Official Documentation**:
- [Block Properties](https://wiki.rocrail.net/doku.php?id=block-gen-en)
- [XMLScript Block Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#block)

### Methods

```python
block.reserve(loco_id: str) -> None
```
Reserve block for specific locomotive (cmd="reserve").

```python
block.free() -> None
```
Free/release the block (cmd="free").

```python
block.go() -> None
```
Give go permission to locomotive (cmd="go").

```python
block.stop() -> None
```
Stop locomotive in block (cmd="stop").

```python
block.open() -> None
block.close() -> None
```
Open or close block for entry (state="open"/"closed").

```python
block.accept_ident() -> None
```
Accept locomotive identification (cmd="acceptident").

### Key Attributes
- `idx`: Block ID
- `state`: Block state (open/closed)
- `reserved`: Reserved flag
- `occ`: Occupied flag
- `locid`: Locomotive ID in block
- `enterside`: Entry side
- `speed`: Block speed limit
- `maxkmh`: Maximum speed in km/h

### Example Usage
```python
# Get block
block = pr.model.get_bk("BK01")

# Reserve for locomotive
block.reserve("BR01")
block.go()

# Close block
block.close()

# Check state
if block.occ:
    print(f"Block occupied by {block.locid}")
```

---

## Switch

**Element**: `<sw>` | **File**: `src/pyrocrail/objects/switch.py`

**Description**: Switch objects control turnouts, points, and crossings for track routing.

**Official Documentation**:
- [Switch Properties](https://wiki.rocrail.net/doku.php?id=switch-gen-en)
- [XMLScript Switch Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#switch)

### Methods

```python
switch.straight() -> None
```
Set to straight/through position (cmd="straight").

```python
switch.turnout() -> None
```
Set to turnout/diverging position (cmd="turnout").

```python
switch.flip() -> None
```
Toggle between straight and turnout (cmd="flip").

```python
switch.left() -> None
switch.right() -> None
```
For 3-way switches (cmd="left"/"right").

```python
switch.lock() -> None
switch.unlock() -> None
```
Lock/unlock switch position (cmd="lock"/"unlock").

### Key Attributes
- `idx`: Switch ID
- `state`: Current state (straight/turnout/left/right)
- `type`: Switch type (default/threeway/dcrossing)
- `addr1`, `port1`: Primary address
- `addr2`, `port2`: Secondary address (3-way)

### Example Usage
```python
# Get switch
sw = pr.model.get_sw("SW01")

# Set position
sw.straight()
sw.turnout()
sw.flip()  # Toggle

# 3-way switch
sw3 = pr.model.get_sw("SW3WAY")
sw3.left()
sw3.right()

# Lock in position
sw.straight()
sw.lock()
```

---

## Signal

**Element**: `<sg>` | **File**: `src/pyrocrail/objects/signal.py`

**Description**: Signal objects control signal aspects for safe train operation and automatic routing.

**Official Documentation**:
- [Signal Properties](https://wiki.rocrail.net/doku.php?id=signal-gen-en)
- [XMLScript Signal Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#signal)

### Methods

#### Basic Aspects
```python
signal.red() -> None
signal.green() -> None
signal.yellow() -> None
signal.white() -> None
```
Set standard signal aspects (cmd="red"/"green"/"yellow"/"white").

```python
signal.blank() -> None
```
Turn off all signal lights (cmd="blank").

#### Programmatic Control
```python
signal.set_aspect(aspect: str) -> None
```
Set aspect by name (red/green/yellow/white).

```python
signal.next_aspect() -> None
```
Cycle to next aspect (cmd="aspect").

```python
signal.aspect_number(aspect_num: int) -> None
```
For complex signals with numbered aspects (cmd="aspect0" through "aspect31").

#### Mode Control
```python
signal.auto() -> None
signal.manual() -> None
```
Switch between automatic and manual mode (cmd="auto"/"manual").

### Key Attributes
- `idx`: Signal ID
- `aspect`: Current aspect (0-31)
- `aspectnr`: Aspect number
- `state`: Signal state
- `type`: Signal type

### Example Usage
```python
# Get signal
sig = pr.model.get_sg("SG01")

# Set aspects
sig.red()      # Stop
sig.yellow()   # Caution
sig.green()    # Clear

# Automatic mode
sig.auto()

# Complex signal with multiple aspects
sig.aspect_number(5)
```

---

## Route

**Element**: `<st>` | **File**: `src/pyrocrail/objects/route.py`

**Description**: Route objects define paths through the layout by coordinating switches, signals, and blocks.

**Official Documentation**:
- [Route Properties](https://wiki.rocrail.net/doku.php?id=route-gen-en)
- [XMLScript Route Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#route)

### Methods

```python
route.set() -> None
route.go() -> None
```
Activate the route (cmd="set").

```python
route.lock() -> None
```
Lock route (prevent changes) (cmd="lock").

```python
route.unlock() -> None
```
Unlock route (cmd="unlock").

```python
route.free() -> None
```
Free/deactivate route (cmd="free").

```python
route.test() -> None
```
Test route without activation (cmd="test").

### Key Attributes
- `idx`: Route ID
- `bka`: From block
- `bkb`: To block
- `status`: Route status
- `state`: Route state (free/locked/set)
- `speed`: Route speed limit
- `switch_commands`: List of switch commands
- `output_commands`: List of output commands
- `permissions`: List of permissions

### Example Usage
```python
# Get route
route = pr.model.get_st("RT01")

# Activate route
route.set()

# Lock route during passage
route.lock()

# Free after train passes
route.free()
route.unlock()
```

---

## Feedback

**Element**: `<fb>` | **File**: `src/pyrocrail/objects/feedback.py`

**Description**: Feedback objects represent sensors and detectors for train position detection.

**Official Documentation**:
- [Feedback/Sensor Properties](https://wiki.rocrail.net/doku.php?id=sensor-gen-en)
- [XMLScript Feedback Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#feedback)

### Methods

```python
fb.on() -> None
```
Set sensor to occupied/on state (state="true").

```python
fb.off() -> None
```
Set sensor to free/off state (state="false").

```python
fb.flip() -> None
```
Toggle sensor state (cmd="flip").

```python
fb.set(state: bool) -> None
```
Set sensor to specific state (True=on, False=off).

### Key Attributes
- `idx`: Feedback ID
- `state`: Sensor state (true/false)
- `identifier`: Detected identifier
- `val`: Sensor value
- `addr`: Sensor address

### Example Usage
```python
# Get feedback sensor
fb = pr.model.get_fb("FB01")

# Simulate sensor activation (for testing)
fb.on()
fb.off()

# Check sensor state
if fb.state:
    print("Sensor occupied")
```

---

## Output

**Element**: `<co>` | **File**: `src/pyrocrail/objects/output.py`

**Description**: Output objects control accessories like lights, sounds, and other layout effects.

**Official Documentation**:
- [Output Properties](https://wiki.rocrail.net/doku.php?id=output-gen-en)
- [XMLScript Output Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#output)

### Methods

```python
output.on() -> None
```
Turn output on (cmd="on").

```python
output.off() -> None
```
Turn output off (cmd="off").

```python
output.flip() -> None
```
Toggle output state (cmd="flip").

```python
output.active(duration_ms: int | None = None) -> None
```
Activate output for duration then turn off (cmd="active").

```python
output.xml() -> None
```
Send full output state including RGB color (if configured).

### Key Attributes
- `idx`: Output ID
- `state`: Output state (on/off)
- `value`: Output value when on
- `valueoff`: Output value when off
- `color`: Color object (RGB/RGBW) if configured

### Example Usage
```python
# Get output
out = pr.model.get_co("CO01")

# Control output
out.on()
out.off()
out.flip()

# Timed activation (5 seconds)
out.active(5000)

# RGB color output
if out.color:
    out.color.red = 255
    out.color.green = 128
    out.color.blue = 0
    out.xml()  # Send color update
```

---

## Car

**Element**: `<car>` | **File**: `src/pyrocrail/objects/car.py`

**Description**: Car objects represent rolling stock (freight cars, passenger cars) for cargo operations.

**Official Documentation**:
- [Car Properties](https://wiki.rocrail.net/doku.php?id=car-gen-en)
- [XMLScript Car Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#car)

### Methods

```python
car.empty() -> None
```
Set car status to empty (cmd="empty").

```python
car.loaded() -> None
```
Set car status to loaded (cmd="loaded").

```python
car.maintenance() -> None
```
Set car to maintenance status (cmd="maintenance").

```python
car.assign_waybill(waybill_id: str) -> None
```
Assign waybill to car (cmd="assignwaybill").

```python
car.reset_waybill() -> None
```
Reset/clear waybill assignment (cmd="resetwaybill").

#### Decoder Functions (for cars with lighting/sound)
```python
car.set_function(fn_num: int, state: bool) -> None
```
Control decoder function (F0-F31). Cars with decoders can have functions for interior lights, sound effects, etc. Uses `<fn>` tag format with all function states as required by Rocrail protocol.

### Key Attributes
- `idx`: Car ID
- `status`: Car status (empty/loaded/maintenance)
- `type`: Car type (box/flatcar/tanker/etc)
- `subtype`: Car subtype
- `location`: Current location
- `waybill`: Assigned waybill ID
- `len`: Car length
- `weight_empty`: Empty weight
- `weight_loaded`: Loaded weight
- `addr`: Decoder address (0 = no decoder)
- `fncnt`: Function count (typically 32)
- `fn`: Function states dict
- `uselights`: Use lights flag
- `fnlights`: Function number for lights

### Example Usage
```python
# Get car
car = pr.model.get_car("CAR01")

# Load/unload
car.loaded()
car.empty()

# Waybill management
car.assign_waybill("WB01")
car.reset_waybill()

# Maintenance
car.maintenance()

# Decoder functions (for cars with lighting/sound decoders)
passenger_car = pr.model.get_car("PassengerCoach1")
passenger_car.set_function(0, True)   # Turn on interior lights
passenger_car.set_function(1, True)   # Turn on sound effects
passenger_car.set_function(0, False)  # Turn off lights
```

---

## Operator

**Element**: `<operator>` | **File**: `src/pyrocrail/objects/operator.py`

**Description**: Operator objects represent train compositions (locomotive + cars) for freight operations.

**GUI Note**: In Rocview (Rocrail's GUI), operators appear in the **"Trains"** menu/list. The XML element is `<operator>`, but they are commonly referred to as "trains" in the interface.

**Official Documentation**:
- [Operator Properties](https://wiki.rocrail.net/doku.php?id=operator-gen-en)
- [XMLScript Operator Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#operator)

### Methods

```python
operator.empty_car(car_ids: str) -> None
```
Empty specified cars in train (cmd="emptycar").

```python
operator.load_car(car_ids: str) -> None
```
Load specified cars in train (cmd="loadcar").

```python
operator.add_car(car_ids: str) -> None
```
Add cars to train composition (cmd="addcar").

```python
operator.leave_car(car_ids: str) -> None
```
Remove cars from train composition (cmd="leavecar").

### Key Attributes
- `idx`: Operator ID
- `lcid`: Assigned locomotive ID
- `carids`: Comma-separated list of car IDs
- `cargo`: Cargo type
- `location`: Current location
- `V_max`: Maximum speed
- `length`: Total train length

### Example Usage
```python
# Get operator (train)
train = pr.model.get_operator("TRAIN01")

# Load/unload cars
train.load_car("CAR01,CAR02")
train.empty_car("CAR01")

# Modify composition
train.add_car("CAR03")
train.leave_car("CAR02")

# Check composition
print(f"Train consists of: {train.carids}")
```

---

## Schedule

**Element**: `<sc>` | **File**: `src/pyrocrail/objects/schedule.py`

**Description**: Schedule objects define timetables with stops and departure times for automated train operation.

**Official Documentation**:
- [Schedule Properties](https://wiki.rocrail.net/doku.php?id=schedule-gen-en)

### Methods

**Note**: Schedules are assigned to locomotives using `loco.use_schedule(schedule_id)`. They do not have their own control commands.

### Key Attributes
- `idx`: Schedule ID
- `trainid`: Assigned train/operator ID
- `group`: Schedule group
- `class_`: Train class
- `fromhour`, `tohour`: Active time range
- `cycles`: Number of cycles (0=infinite)
- `entries`: List of ScheduleEntry objects

### ScheduleEntry Attributes
- `block`: Block ID for stop
- `hour`, `minute`: Departure time
- `ahour`, `aminute`: Arrival time
- `minwait`: Minimum wait time
- `regularstop`: Regular stop flag
- `swap`: Swap direction flag
- `departspeed`: Departure speed

### Example Usage
```python
# Get schedule
schedule = pr.model.get_schedule("SCH01")

# Assign to locomotive
loco = pr.model.get_lc("BR01")
loco.use_schedule(schedule.idx)

# Inspect schedule
print(f"Schedule {schedule.idx} has {len(schedule.entries)} stops")
for entry in schedule.entries:
    print(f"  {entry.block} at {entry.hour}:{entry.minute:02d}")
```

---

## Stage

**Element**: `<sb>` | **File**: `src/pyrocrail/objects/stage.py`

**Description**: Stage blocks are specialized blocks for staging yards with multiple track sections.

**Official Documentation**:
- [Stage Block Properties](https://wiki.rocrail.net/doku.php?id=stage-details-en)
- [XMLScript Stage Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#stage)

### Methods

```python
stage.compress() -> None
```
Advance trains to fill gaps in staging yard (cmd="compress").

```python
stage.expand() -> None
```
Activate train in end section if exit is open (cmd="expand").

```python
stage.go() -> None
```
Give go permission (cmd="go").

```python
stage.open() -> None
stage.close() -> None
```
Open/close staging block for entry (cmd="open"/"close").

```python
stage.free() -> None
```
Free the staging block (cmd="free").

#### Section Query Methods
```python
stage.get_section(section_id: str) -> Section | None
```
Get section by ID (e.g., "T0_0").

```python
stage.get_section_by_number(nr: int) -> Section | None
```
Get section by number (0-indexed).

```python
stage.get_occupied_sections() -> list[Section]
```
Get all sections with locomotives.

```python
stage.get_free_sections() -> list[Section]
```
Get all empty sections.

```python
stage.get_section_count() -> int
```
Get total number of sections.

```python
stage.get_locomotives_in_staging() -> list[str]
```
Get list of locomotive IDs in staging yard.

```python
stage.get_front_locomotive() -> str | None
```
Get locomotive at front/entry (lowest numbered occupied section).

```python
stage.get_exit_locomotive() -> str | None
```
Get locomotive ready to depart (highest numbered occupied section).

```python
stage.get_entry_section() -> Section | None
```
Get entry section (section 0).

```python
stage.get_exit_section() -> Section | None
```
Get exit section (highest numbered section).

### Key Attributes
- `idx`: Stage ID
- `state`: Current state (open/closed)
- `entering`: Entering flag
- `reserved`: Reserved flag
- `totallength`: Total yard length
- `totalsections`: Number of sections
- `sections`: List of Section objects
- `fbenterid`: Entry feedback sensor
- `entersignal`: Entry signal
- `exitsignal`: Exit signal

### Section Attributes
Each section in `stage.sections` has:
- `idx`: Section ID (e.g., "T0_0")
- `nr`: Section number (0-indexed)
- `fbid`: Feedback sensor ID for this section
- `len`: Section length
- `lcid`: Locomotive ID currently in section (empty string if free)

### Example Usage
```python
# Get stage block
stage = pr.model.get_stage("SB_T0")

# Open for entry
stage.open()

# Close when full
stage.close()

# Compress trains
stage.compress()

# Release train
stage.go()

# Query sections
print(f"Staging yard has {stage.get_section_count()} sections")
print(f"Occupied: {len(stage.get_occupied_sections())}")
print(f"Free: {len(stage.get_free_sections())}")

# Get locomotives in staging
locos = stage.get_locomotives_in_staging()
print(f"Locomotives: {locos}")

# Access individual sections
for section in stage.sections:
    if section.is_occupied():
        print(f"Section {section.nr}: {section.lcid} (length: {section.len}mm)")
    else:
        print(f"Section {section.nr}: empty")

# Get specific section
section_0 = stage.get_section_by_number(0)
if section_0:
    print(f"First section ID: {section_0.idx}")
    print(f"Feedback sensor: {section_0.fbid}")

# Get locomotives by position
front_loco = stage.get_front_locomotive()
exit_loco = stage.get_exit_locomotive()
print(f"Front locomotive (entered first): {front_loco}")
print(f"Exit locomotive (ready to depart): {exit_loco}")

# Depart the exit locomotive
if exit_loco:
    stage.expand()  # Activate train in exit section
    stage.go()      # Give go permission
```

---

## Text

**Element**: `<tx>` | **File**: `src/pyrocrail/objects/text.py`

**Description**: Text objects display information on station displays, panels, and information boards.

**Official Documentation**:
- [Text Properties](https://wiki.rocrail.net/doku.php?id=text-gen-en)

### Methods

```python
text.set_format(format_str: str, **kwargs: str) -> None
```
Set text format with parameters (e.g., `"Loco: %lcid%"`).

**Note**: Text blinking is controlled by the `refresh` attribute (>99), not by a command.

### Key Attributes
- `idx`: Text ID
- `format`: Text format string with placeholders
- `bkid`: Optional block ID reference
- `lcid`: Optional locomotive ID reference
- `refresh`: Refresh rate (>99 for blinking)

### Example Usage
```python
# Get text display
text = pr.model.get_text("TXT01")

# Update display format
text.set_format("Train: %lcid% in %bkid%", lcid="BR01", bkid="BK01")

# Simple text
text.set_format("Welcome to the station")
```

---

## Booster

**Element**: `<booster>` | **File**: `src/pyrocrail/objects/booster.py`

**Description**: Booster objects control power districts for zone-based power management and short circuit handling.

**Official Documentation**:
- [Booster Properties](https://wiki.rocrail.net/doku.php?id=booster-gen-en)
- [XMLScript Booster Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#booster)

### Methods

```python
booster.on() -> None
```
Turn booster power on (uses `<powercmd cmd="on"/>`).

```python
booster.off() -> None
```
Turn booster power off (uses `<powercmd cmd="off"/>`).

### Key Attributes
- `idx`: Booster ID
- `state`: Power state
- `iid`: Interface ID
- `uid`: Unit ID

### Example Usage
```python
# Get booster
booster = pr.model.get_booster("BOOST01")

# Control power
booster.on()
booster.off()

# Handle short circuit
try:
    # ... train operation
except ShortCircuitError:
    booster.off()
    time.sleep(1)
    booster.on()
```

---

## Variable

**Element**: `<vr>` | **File**: `src/pyrocrail/objects/variable.py`

**Description**: Variable objects store global state that can be shared between PyRocrail and Rocrail's built-in actions, or persisted across sessions.

**Official Documentation**:
- [Variable Properties](https://wiki.rocrail.net/doku.php?id=variable-gen-en)
- [XMLScript Variable Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#variable)

**Note**: For most use cases, regular Python variables are recommended. Rocrail variables are useful when you need to:
- Share state between PyRocrail and Rocrail's internal actions/conditions
- Persist values across sessions (using `generated=False`)

### Methods

```python
var.random() -> None
```
Set variable to random value (cmd="random").

```python
var.set_value(value: int | None = None, text: str | None = None, generated: bool = True) -> None
```
Set variable value and/or text. Use `generated=False` to persist across sessions.

### Key Attributes
- `idx`: Variable ID
- `value`: Integer value
- `text`: Text string
- `generated`: If True, variable is temporary; if False, persists between sessions

### Example Usage
```python
# Get variable
var = pr.model.get_variable("VAR01")

# Set value
var.set_value(value=42)

# Set text
var.set_value(text="Hello")

# Set both
var.set_value(value=100, text="Count: 100")

# Persistent variable (survives server restart)
var.set_value(value=42, generated=False)

# Random value
var.random()
print(f"Random value: {var.value}")

# For most cases, just use Python variables:
my_counter = 0  # Simpler than Rocrail variables
```

---

## Tour

**Element**: `<tour>` | **File**: `src/pyrocrail/objects/tour.py`

**Description**: Tour objects define automated demonstration sequences for visitor presentations.

**Official Documentation**:
- [Tour Properties](https://wiki.rocrail.net/doku.php?id=tour-gen-en)

### Methods

**Note**: Tours do not have direct control commands. They are configured in Rocrail and execute automatically based on their schedule.

### Key Attributes
- `idx`: Tour ID
- Configuration attributes set via Rocrail GUI

### Example Usage
```python
# Get tour
tour = pr.model.get_tour("TOUR01")

# Tours are controlled via Rocrail, not direct commands
# Read tour configuration
print(f"Tour: {tour.idx}")
```

---

## Location

**Element**: `<location>` | **File**: `src/pyrocrail/objects/location.py`

**Description**: Location objects represent geographic points like cities, stations, or regions, and provide sophisticated train flow management for hidden yards through occupancy control.

**Official Documentation**:
- [Location Details](https://wiki.rocrail.net/doku.php?id=locations-details-en)
- [XMLScript Location Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#location)

### Primary Purpose
Locations control train flow management, especially useful for hidden yards:
- **Minimal Occupancy** (`minocc`): Ensures a minimum number of trains always remain in the location
- **Maximal Occupancy** (`maxocc`): Limits the total number of trains allowed
- **FIFO Mode**: Controls whether trains depart in first-in-first-out order
- **Scheduling**: Generates timetables and manages train assignments

### Methods

```python
location.info(svalue: str | None = None) -> None
```
Set or query location information (cmd="info").

### Key Attributes
- `idx`: Location ID
- `minocc`: Minimal occupancy - minimum trains that must remain
- `maxocc`: Maximal occupancy - maximum trains allowed
- `fifo`: FIFO (First-In-First-Out) mode enabled
- `random`: Random train selection for departure
- `scheduleid`: Associated schedule ID
- `trains`: Only assigned train locomotives allowed

### Flow Management Rules
- **Rule of thumb**: Set `minocc` = (number of trains to remain) + 1
- Trains will not depart in auto mode if `minocc` threshold not met
- Can be temporarily overridden with train (re)Start command
- FIFO allows trains to exit alternately from hidden yards
- Perfect for controlling traffic density on visible layout sections

### Example Usage
```python
# Get location (e.g., hidden yard)
hidden_yard = pr.model.get_location("HIDDEN_01")

# Check occupancy settings
print(f"Min occupancy: {hidden_yard.minocc}")
print(f"Max occupancy: {hidden_yard.maxocc}")
print(f"FIFO enabled: {hidden_yard.fifo}")

# Query location info for dynamic text displays
hidden_yard.info()

# Use with text displays
hidden_yard.info(svalue="yard_display_01")

# Example: Hidden yard with 5 tracks, keep 4 trains
# In Rocrail plan, set minocc=5 (4 trains + 1)
# This ensures at least 4 trains always remain in the yard
```

---

## Weather

**Element**: `<weather>` | **File**: `src/pyrocrail/objects/weather.py`

**Description**: Weather objects control atmospheric effects and lighting for time-of-day simulation.

**Official Documentation**:
- [Weather Properties](https://wiki.rocrail.net/doku.php?id=weather-gen-en)
- [XMLScript Weather Commands](https://wiki.rocrail.net/doku.php?id=xmlscripting-en#weather)

### Methods

```python
weather.setweather() -> None
```
Set weather conditions (cmd="setweather").

```python
weather.weathertheme() -> None
```
Apply weather theme (cmd="weathertheme").

```python
weather.go() -> None
```
Start weather effects (cmd="go").

```python
weather.stop() -> None
```
Stop weather effects (cmd="stop").

### Key Attributes
- `idx`: Weather ID
- Configuration attributes

### Example Usage
```python
# Get weather
weather = pr.model.get_weather("WEATHER01")

# Control weather
weather.setweather()
weather.go()

# Stop effects
weather.stop()
```

---

## Action

**Element**: `<action>` | **File**: `src/pyrocrail/objects/action.py`

**Description**: Action objects represent event-driven automation scripts (note: PyRocrail uses Python Action class instead).

**Official Documentation**:
- [Actions Overview](https://wiki.rocrail.net/doku.php?id=actions-en)

**Note**: PyRocrail provides its own Action class for Python-based automation. See the main README for Action usage examples.

---

## Additional Resources

### General Documentation
- [Rocrail Wiki Homepage](https://wiki.rocrail.net/)
- [XMLScript Reference](https://wiki.rocrail.net/doku.php?id=xmlscripting-en)
- [Wrapper XML Reference](https://wiki.rocrail.net/rocrail-snapshot/rocrail/wrapper-en.html)

### Development
- [Rocrail Protocol](https://wiki.rocrail.net/doku.php?id=develop:cs-protocol-en)
- [TCP/IP Communication](https://wiki.rocrail.net/doku.php?id=rocrail-server-en#tcp_ip)

### Support
- [Rocrail Forum](https://forum.rocrail.net/)
- [PyRocrail GitHub](https://github.com/user/py-rocrail)

---

**Note**: All methods and attributes listed in this documentation are verified against the official Rocrail documentation. If you discover any discrepancies or have questions, please refer to the official Rocrail wiki or open an issue on GitHub.
