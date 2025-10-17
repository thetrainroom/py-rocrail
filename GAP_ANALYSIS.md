# Gap Analysis: PyRocrail vs Rocrail Specification

**Date**: 2025-10-17 (Updated)
**Source**: [Rocrail Wiki](https://wiki.rocrail.net/) - [XMLScript Documentation](https://wiki.rocrail.net/doku.php?id=xmlscripting-en)

## Executive Summary

PyRocrail currently implements **11 of ~22** runtime-controllable object types (50%) with **verified command support**. This library aims to replace XML scripting with Python for better control and automation.

**Current Status:**
- ✅ **State updates**: COMPLETE (10 object types, 100% coverage for implemented objects)
- ✅ **Core objects**: 8 of 11 objects have 100% command coverage
- ✅ **Route parsing**: Switch/output/permission child elements
- ✅ **Car/Operator/Schedule/Stage**: Rolling stock, train composition, timetables, and staging yards
- ❌ **Missing**: 11+ object types (Turntable, Text, etc.)

**Recent Progress (2025-10-17):**
- Implemented Car, Operator, Schedule, and Stage objects
- Car: 5 commands (630 messages in PCAP now handled!)
- Operator: 4 commands (90 messages in PCAP now handled!)
- Schedule: 3 commands (UNVERIFIED - not in official docs) + entry parsing
- Stage: 6 commands (staging yard management)
- Implemented state update handling for all 10 major object types
- Verified all commands against official XMLScript documentation
- **Message handling: 89.9%** (2396 of 2666 messages)

---

## 1. Missing Object Types (Runtime Controllable)

These Rocrail objects can be controlled at runtime but are **NOT implemented**:

### 1.1 Text (tx)
**Purpose**: Text displays for stations/panels
**Commands**: Set text content, format control, display on/off
**Use Case**: Station announcements, panel displays
**Priority**: MEDIUM

---

### 1.2 Turntable (tt)
**Purpose**: Turntable/fiddle yard control
**Commands**:
- `goto` - Move to track number
- `rotate` - Rotate degrees
- `calibrate` - Calibrate position
- `lock`/`unlock` - Lock/unlock bridge

**Use Case**: Engine servicing facilities, staging yards
**Priority**: HIGH

---

### 1.3 Tour
**Purpose**: Automated tour sequences
**Commands**: start, stop, reset
**Use Case**: Demo mode, visitor presentations
**Priority**: LOW

---

### 1.4 Location
**Purpose**: Geographic locations on layout
**Commands**: Modify properties, state tracking
**Use Case**: Station management, geography tracking
**Priority**: LOW

---

### 1.5 Analyser
**Purpose**: Track analyser for decoder programming
**Commands**: start, stop, readcv, writecv
**Use Case**: Decoder programming, maintenance
**Priority**: MEDIUM

---

### 1.6 Booster
**Purpose**: Power district/booster control
**Commands**: on, off, status
**Use Case**: Power management, short circuit handling
**Priority**: MEDIUM

---

### 1.7 Link
**Purpose**: Cross-references between objects
**Commands**: activate, deactivate
**Use Case**: Complex object relationships
**Priority**: LOW

---

### 1.8 Variable (var)
**Purpose**: Global variables for scripting
**Commands**: get, set, increment, decrement
**Use Case**: State tracking in Python scripts
**Priority**: MEDIUM

---

### 1.9 Selector Table (seltab)
**Purpose**: Selection tables for routing
**Commands**: select, next, previous
**Use Case**: Complex routing decisions
**Priority**: LOW

---

### 1.10 Weather
**Purpose**: Weather effects control
**Commands**: Set conditions, themes, lighting effects
**Use Case**: Atmospheric effects, time-of-day simulation
**Priority**: LOW

---

## 2. Implemented Objects - Command Coverage

### 2.1 Locomotive (`src/pyrocrail/objects/locomotive.py`)

**✅ Implemented Commands** (11 total):
- `set_speed()` - Speed control (0-100%)
- `set_direction()` - Direction (forward/reverse)
- `stop()` - Emergency stop
- `set_lights()` - Main lights on/off
- `set_function()` - Function control (F0-F28)
- `dispatch()` - Dispatch for auto mode
- `collect()` - Collect from auto mode
- `shortcut()` - Short circuit handling
- `regularreset()` - Remove assigned schedule ✨ NEW
- `softreset()` - Soft reset ✨ NEW
- `use_schedule()` - Assign schedule ✨ NEW

**✅ State Updates**: Speed, direction, position, block, mode, functions

**❌ Missing** (Not in XMLScript docs):
- Additional commands may exist but are not documented in official XMLScript reference
- Commands like `velocity`, `gotoblock`, `consist` etc. mentioned in other sources but not verified

**Coverage**: 11 documented commands ✅

---

### 2.2 Block (`src/pyrocrail/objects/block.py`)

**✅ Implemented Commands** (7 total - ✅ COMPLETE):
- `reserve()` - Reserve block for locomotive
- `free()` - Free the block
- `go()` - Give go permission
- `stop()` - Stop locomotive in block
- `close()` - Close block (no entry)
- `open()` - Open block (allow entry)
- `accept_ident()` - Accept locomotive identification

**✅ State Updates**: Occupancy, reservation, locomotive ID, entering state

**✅ Configuration Properties** (not commands):
- `speed`, `maxkmh` - Speed limits (set in plan, not runtime commands)
- `waittime` - Wait time (set in plan)
- Properties can be read but not changed via commands

**Coverage**: 100% of XMLScript documented commands ✅

---

### 2.3 Switch (`src/pyrocrail/objects/switch.py`)

**✅ Implemented Commands** (7 total - ✅ COMPLETE):
- `straight()` - Set to straight position
- `turnout()` - Set to turnout position
- `flip()` - Toggle position
- `lock()` - Lock in position
- `unlock()` - Unlock
- `left()` - Left position (3-way switches) ✨ NEW
- `right()` - Right position (3-way switches) ✨ NEW

**✅ State Updates**: Position (straight/turnout/left/right)

**Coverage**: 100% of XMLScript documented commands ✅

---

### 2.4 Signal (`src/pyrocrail/objects/signal.py`)

**✅ Implemented Commands** (10 total - ✅ COMPLETE):
- `red()` - Stop aspect
- `green()` - Clear aspect
- `yellow()` - Caution aspect
- `white()` - Shunt aspect
- `auto()` - Automatic mode
- `manual()` - Manual mode
- `set_aspect()` - Programmatic aspect setting
- `next_aspect()` - Cycle to next aspect
- `aspect_number()` - Complex signals (aspect 0-31) ✨ NEW
- `blank()` - Turn off signal ✨ NEW

**✅ State Updates**: Current aspect, mode

**Coverage**: 100% of XMLScript documented commands ✅

---

### 2.5 Route (`src/pyrocrail/objects/route.py`)

**✅ Implemented Commands** (5 total - ✅ COMPLETE):
- `set()` / `go()` - Activate route
- `lock()` - Lock route
- `unlock()` - Unlock route
- `free()` - Free route
- `test()` - Test route without activating

**✅ Child Element Parsing** (✨ NEW):
- `SwitchCommand` - Parses switch commands in routes
- `OutputCommand` - Parses output commands in routes
- `Permission` - Parses route permissions

**✅ State Updates**: Route state (free/locked/set), status

**❌ Additional Commands** (mentioned but not documented):
- `classset`, `classadd`, `classdel` - Exist but no examples in XMLScript docs

**Coverage**: 100% of documented commands + child parsing ✅

---

### 2.6 Output (`src/pyrocrail/objects/output.py`)

**✅ Implemented Commands** (4 total - ✅ COMPLETE):
- `on()` - Turn on
- `off()` - Turn off
- `flip()` - Toggle state ✨ NEW
- `active()` - Timed activation ✨ NEW
- Color support (RGB/RGBW via xml())

**✅ State Updates**: State (on/off), value

**Coverage**: 100% of XMLScript documented commands ✅

---

### 2.7 Feedback (`src/pyrocrail/objects/feedback.py`)

**✅ Implemented Commands** (4 total - ✅ COMPLETE):
- `on()` - Set sensor on
- `off()` - Set sensor off
- `flip()` - Toggle state
- `set()` - Set to boolean state

**✅ State Updates**: Sensor state (on/off)

**Coverage**: 100% of XMLScript documented commands ✅

---

### 2.8 Car (`src/pyrocrail/objects/car.py`) ✨ NEW

**✅ Implemented Commands** (5 total - ✅ COMPLETE):
- `empty()` - Set car status to empty
- `loaded()` - Set car status to loaded
- `maintenance()` - Set car to maintenance status
- `assign_waybill()` - Assign waybill to car
- `reset_waybill()` - Reset/clear waybill assignment

**✅ State Updates**: Status (empty/loaded/maintenance), location, waybill

**Configuration Attributes**:
- `type`, `subtype` - Car type and subtype
- `roadname`, `number`, `color` - Car identification
- `len`, `weight_empty`, `weight_loaded` - Physical properties

**Coverage**: 100% of XMLScript documented commands ✅

---

### 2.9 Operator (`src/pyrocrail/objects/operator.py`) ✨ NEW

**✅ Implemented Commands** (4 total - ✅ COMPLETE):
- `empty_car()` - Empty specified cars in train
- `load_car()` - Load specified cars in train
- `add_car()` - Add cars to train composition
- `leave_car()` - Remove cars from train composition

**✅ State Updates**: Locomotive assignment, car list, cargo type, location

**Configuration Attributes**:
- `lcid` - Assigned locomotive ID
- `carids` - Comma-separated list of car IDs
- `cargo`, `class_`, `roadname` - Train classification
- `V_max`, `length`, `radius` - Physical constraints

**Coverage**: 100% of XMLScript documented commands ✅

---

### 2.10 Schedule (`src/pyrocrail/objects/schedule.py`) ✨ NEW

**⚠️  Implemented Commands** (3 total - UNVERIFIED):
- `start()` - Start the schedule (UNVERIFIED)
- `stop()` - Stop the schedule (UNVERIFIED)
- `reset()` - Reset to beginning (UNVERIFIED)

**⚠️  Warning**: These commands are NOT documented in official XMLScript reference and may not work with actual Rocrail servers.

**✅ State Updates**: All schedule attributes, entry list

**✅ Schedule Entry Parsing**:
- `ScheduleEntry` dataclass for each stop/waypoint
- Parses block, hour, minute, minwait, regularstop, etc.
- Full timetable structure support

**Configuration Attributes**:
- `trainid`, `group`, `class_` - Schedule classification
- `timeframe`, `fromhour`, `tohour` - Time configuration
- `cycles`, `maxdelay` - Operation settings
- `entries` - List of ScheduleEntry objects

**Coverage**: Structure complete, commands unverified ⚠️

---

### 2.11 Stage (`src/pyrocrail/objects/stage.py`) ✨ NEW

**✅ Implemented Commands** (6 total - ✅ COMPLETE):
- `compress()` - Advance trains to fill gaps in staging yard
- `expand()` - Activate train in end section if exit is open
- `open()` - Open staging block for entry
- `close()` - Close staging block (no entry)
- `free()` - Free the staging block
- `go()` - Give go permission to train in staging block

**✅ State Updates**: All stage attributes including state, entering, reserved, occupancy

**Configuration Attributes**:
- `state` - Current state (open/closed/etc.)
- `entering`, `reserved` - Status flags
- `totallength`, `totalsections` - Occupancy tracking
- `slen`, `gap` - Section configuration
- `fbenterid`, `entersignal`, `exitsignal` - Sensor and signal configuration
- `waitmode`, `minwaittime`, `maxwaittime` - Wait time configuration
- `exitspeed`, `stopspeed`, `speedpercent` - Speed settings
- `usewd`, `wdsleep` - Watchdog configuration
- `minocc`, `minoccsec` - Minimum occupancy settings

**Coverage**: 100% of documented commands ✅

---

## 3. Missing System-Level Features

### 3.1 System Commands (`src/pyrocrail/pyrocrail.py:53`)

**✅ Implemented**:
- `go` - Power on (power_on)
- `stop` - Power off (power_off)
- `ebreak` - Emergency stop (emergency_stop)
- `reset` - Reset system

**✅ Implemented - Auto Mode**:
- `auto on` - Enable automatic mode (auto_on)
- `auto off` - Disable automatic mode (auto_off)

**❌ Missing**:
- `locliste` - Request locomotive list
- `save` - Save Rocrail plan to disk
- `shutdown` - Shutdown Rocrail server
- `query` - Query server capabilities
- `sod` - Start of day operations
- `eod` - End of day operations
- `updateini` - Update configuration
- `clock` - Clock control commands
- `event` - Fire custom events
- `opendlg` - Open dialog (GUI control)

**Priority**: HIGH (save, shutdown commonly used)

---

### 3.2 Model Queries (`src/pyrocrail/model.py:40`)

**✅ Implemented**:
- `<model cmd="plan"/>` - Get complete plan

**❌ Missing**:
- `<model cmd="lcprops" val="locoID"/>` - Get locomotive properties
- `<model cmd="lclist"/>` - Get locomotive list
- `<model cmd="merge"/>` - Merge plan updates
- `<model cmd="add"/>` - Add object dynamically
- `<model cmd="remove"/>` - Remove object
- `<model cmd="modify"/>` - Modify object properties
- `<model cmd="swlist"/>` - Get switch list
- `<model cmd="fblist"/>` - Get feedback list

**Priority**: HIGH (dynamic object management essential)

---

## 4. Event/State Handling

### 4.1 Inbound State Updates ✅ COMPLETE

**✅ Implemented** (2025-10-17):
- ✅ Locomotive state updates - Speed, direction, position, block, mode
- ✅ Block occupancy updates - Reserved, occupied, entering, locid
- ✅ Feedback sensor state changes - On/off state
- ✅ Switch position updates - Straight/turnout/left/right
- ✅ Signal aspect changes - Current aspect from automatic mode
- ✅ Route state updates - Free/locked/set status
- ✅ Car state updates - Status, location, waybill ✨ NEW
- ✅ Operator state updates - Locomotive, cars, cargo ✨ NEW
- ✅ Schedule state updates - All attributes, entry list ✨ NEW
- ✅ Stage block state updates - State, entering, reserved, occupancy ✨ NEW

**Result**: 10 object types with complete state update handling

**PCAP Test Results**: 89.9% of messages handled (2396 of 2666 messages)

**✅ Callback Support**:
- `model.change_callback` - Notifies on object state changes
- Provides object type, ID, and updated object reference

**❌ Still Missing**:
- Exception/error event parsing (330 messages in PCAP)
- Power state tracking
- Auto mode state updates

---

### 4.2 Event-Based Actions

**Current State**: Framework exists (`src/pyrocrail/pyrocrail.py:30`) but untested

**Missing**:
- Event registration for specific objects
- Event filtering by type
- Event condition evaluation
- Event-triggered script execution

**Priority**: HIGH (needed for automation)

---

### 4.3 Exception Handling

**Missing**:
- `<exception>` tag parsing
- Short circuit events
- Communication errors
- Timeout handling
- Decoder programming errors

**Priority**: MEDIUM (important for robustness)

---

### 4.4 System State Tracking

**Missing**:
- `<state power="true|false"/>` - Power state tracking
- `<auto cmd="on|off"/>` - Auto mode tracking
- Clock synchronization improvements
- Server version/capability tracking

**Priority**: MEDIUM (useful for monitoring)

---

## 5. Statistics Summary

| Category | Before | After | Coverage |
|----------|--------|-------|----------|
| **Object Types** | 7 | 11 | 50% (11 missing) |
| **Locomotive Commands** | 7 | 11 | ✅ 11 verified |
| **Block Commands** | 7 | 7 | ✅ 100% |
| **Switch Commands** | 5 | 7 | ✅ 100% |
| **Signal Commands** | 7 | 10 | ✅ 100% |
| **Route Commands** | 5 | 5 | ✅ 100% + parsing |
| **Output Commands** | 2 | 4 | ✅ 100% |
| **Feedback Commands** | 4 | 4 | ✅ 100% |
| **Car Commands** | 0 | 5 | ✅ 100% ✨ NEW |
| **Operator Commands** | 0 | 4 | ✅ 100% ✨ NEW |
| **Schedule Commands** | 0 | 3 | ⚠️ UNVERIFIED ✨ NEW |
| **Stage Commands** | 0 | 6 | ✅ 100% ✨ NEW |
| **State Updates** | 0% | 100% | ✅ 10 object types |
| **System Commands** | 6 | 6 | ~40% (10+ missing) |
| **Model Queries** | 1 | 1 | ~11% (8+ missing) |

**Overall Improvement**:
- Commands: 39 → 66 (+27 commands, +69%)
- Object types: 7 → 11 (+4 new types)
- State updates: 0% → 100% (10 object types)
- Objects with 100% verified command coverage: 0 → 8
- Objects with structure + unverified commands: 1 (Schedule)

---

## 6. Recommended Implementation Priority

### ✅ Phase 1 - COMPLETE (2025-10-17)
1. ✅ **State update handling** - All 10 object types implemented
2. ✅ **Route child elements** - Switch/output/permission parsing complete
3. ✅ **Command verification** - All commands verified against XMLScript docs

### ✅ Phase 2 - COMPLETE (2025-10-17)
1. ✅ **Car** - Rolling stock management (630 objects, 5 commands) ✨ NEW
2. ✅ **Operator** - Train compositions (90 objects, 4 commands) ✨ NEW

### ⚠️  Phase 3 - PARTIALLY COMPLETE (2025-10-17)
1. ⚠️ **Schedule** - Timetable operations (structure complete, 3 UNVERIFIED commands) ✨ NEW
   - Full entry parsing and state updates implemented
   - Commands (start/stop/reset) NOT documented in XMLScript
   - Needs testing with real Rocrail server to verify commands

### ✅ Phase 4 - COMPLETE (2025-10-17)
1. ✅ **Stage** - Staging yard management (6 commands) ✨ NEW
   - compress/expand for train management
   - open/close/free/go for state control
   - Full state update support

### Phase 5 - Remaining High Priority Objects (CURRENT PRIORITY)
1. **Turntable** - Engine facilities, common in layouts (waiting for command documentation)

### Phase 6 - System Management
2. **Model queries** - lcprops, add, remove, modify
3. **System commands** - save, shutdown, sod, eod
4. **Exception handling** - Parse <exception> messages (330 in PCAP)

### Phase 7 - Specialized Objects
5. **Text** - Information displays
6. **Analyser** - Decoder programming
7. **Booster** - Power management
8. **Variable** - Global variables

### Phase 8 - Advanced Features
9. **Tour** - Demo mode
10. **Weather** - Atmospheric effects
11. **Link** - Object relationships
12. **Selector Table** - Complex routing
13. **Location** - Geographic tracking

---

## 7. Testing Requirements

See [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) for comprehensive testing approach.

Key testing needs:
- Unit tests for all object methods
- Integration tests with mock Rocrail server
- State update verification
- Event handling tests
- Concurrent operation tests
- Optional E2E tests with real Rocrail

---

## References

- [Rocrail RCP Protocol](https://wiki.rocrail.net/doku.php?id=develop:cs-protocol-en)
- [Rocrail XML Structure](https://wiki.rocrail.net/rocrail-snapshot/rocrail/wrapper-en.html#rocrail)
- [XML Scripting](https://wiki.rocrail.net/doku.php?id=xmlscripting-en) (to be replaced by Python)
- [Rocrail Wiki](https://wiki.rocrail.net/doku.php?id=start)
