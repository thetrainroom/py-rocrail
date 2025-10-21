# Emergency Disconnect Handling

## Overview

When Rocrail crashes or network connection fails during live operation, trains continue running with their last DCC commands. This can cause **collisions and chaos**.

PyRocrail provides automatic disconnect detection and callbacks to:
1. **Cut power immediately** (hardware relay)
2. **Save layout state** for recovery
3. **Alert operator**

## Quick Start

```python
from pyrocrail import PyRocrail
import json

def emergency_handler(model):
    """Called when connection to Rocrail is lost"""

    # 1. CUT POWER - Hardware relay (CRITICAL!)
    import RPi.GPIO as GPIO
    GPIO.output(EMERGENCY_STOP_PIN, GPIO.HIGH)  # Your relay pin

    # 2. Save state for recovery
    state = model.export_state()
    with open('emergency_state.json', 'w') as f:
        json.dump(state, f, indent=2)

    # 3. Alert operator
    print("EMERGENCY: Rocrail disconnected, power cut!")
    # send_sms("EMERGENCY: Check layout immediately")

# Register handler
pr = PyRocrail(
    "localhost", 8051,
    on_disconnect=emergency_handler  # <-- Your safety net
)

pr.start()
# ... normal operation ...
```

## Why This Matters

**Without emergency handling:**
- ❌ Trains keep running when Rocrail crashes
- ❌ No automatic power cutoff
- ❌ No state preservation
- ❌ Hours of manual resynchronization
- ❌ Risk of collisions and damage

**With emergency handling:**
- ✅ Automatic connection loss detection
- ✅ **Distinguishes crash from graceful shutdown**
- ✅ Immediate power cutoff (via your hardware)
- ✅ Complete state snapshot saved
- ✅ Operator alerted instantly
- ✅ Minutes to recover (not hours)

## Graceful Shutdown vs Crash Detection

PyRocrail automatically distinguishes between:

**Graceful Shutdown** (Rocrail sends `<sys cmd="shutdown"/>`):
- User closes Rocrail properly (File → Exit)
- Emergency handler **NOT called** ✅
- No unnecessary alarms
- Normal shutdown sequence

**Unexpected Disconnect** (No shutdown message):
- Rocrail crashes ⚠️
- Network failure ⚠️
- Process killed ⚠️
- Power loss ⚠️
- Emergency handler **IS called** 🚨
- Track power cut
- State saved
- Operator alerted

This prevents false alarms while ensuring safety during actual emergencies.

## Hardware Power Cutoff

**CRITICAL:** You CANNOT send DCC commands when Rocrail is down!
You MUST use **hardware-level emergency stop**.

### Option 1: Raspberry Pi GPIO Relay

```python
import RPi.GPIO as GPIO

EMERGENCY_STOP_PIN = 17  # BCM GPIO 17

def emergency_handler(model):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(EMERGENCY_STOP_PIN, GPIO.OUT)
    GPIO.output(EMERGENCY_STOP_PIN, GPIO.HIGH)  # Cut power

    # Save state...
```

**Wiring:**
- GPIO Pin → Relay IN
- Relay NO/NC → Track power supply

### Option 2: Serial Relay Board

```python
import serial

def emergency_handler(model):
    relay = serial.Serial('/dev/ttyUSB0', 9600)
    relay.write(b'RELAY_OFF\n')  # Command depends on your board

    # Save state...
```

### Option 3: Network-Controlled Relay

```python
import requests

def emergency_handler(model):
    requests.post('http://192.168.1.100/power/off', timeout=2)

    # Save state...
```

### Option 4: Industrial Circuit Breaker

For professional installations, integrate with your existing emergency stop system via:
- Modbus TCP/RTU
- MQTT
- OPC UA
- Digital I/O cards

## State Recovery

The `model.export_state()` method provides:

```python
{
    "timestamp": 1678901234.567,
    "clock": {
        "hour": 14,
        "minute": 30,
        "divider": 5,
        "freeze": false
    },
    "locomotives": [
        {
            "id": "BR_185",
            "speed": 75,
            "direction": true,
            "block": "bk_main_01",
            "destblock": "bk_station_03",
            "mode": "auto",
            "functions": [true, false, true, ...]
        }
    ],
    "blocks": [
        {
            "id": "bk_main_01",
            "occupied": true,
            "reserved": true,
            "loco_id": "BR_185",
            "state": "occupied"
        }
    ],
    "switches": [...],
    "signals": [...],
    "routes": [...],
    "feedbacks": [...]
}
```

## Recovery Workflow

1. **Disconnect detected** → Handler called automatically
2. **Power cut** → Trains stop immediately (hardware relay)
3. **State saved** → All positions/states in `emergency_state.json`
4. **Operator alerted** → SMS/email/alarm
5. **Manual steps:**
   - Verify track power is OFF
   - Restart Rocrail
   - Load `emergency_state.json`
   - Compare with actual layout
   - Update Rocrail to match reality
   - Verify all positions correct
   - Resume operations

## Example: Complete Safety System

See `examples/05_emergency_disconnect.py` for a complete working example including:
- Multiple hardware relay options
- State saving with metadata
- Recovery information display
- Operator guidance
- Alert integration points

## Testing

**Simulate connection loss:**
1. Run your PyRocrail script with `on_disconnect` handler
2. Stop Rocrail server
3. Verify:
   - Handler called automatically
   - Power cut (if hardware connected)
   - State saved to file
   - Alerts sent

**Important:** Test this BEFORE your live event!

## Best Practices

1. **Always use hardware emergency stop** - Never rely on software alone
2. **Test your relay control** - Verify it actually cuts power
3. **Save state to persistent storage** - Not RAM/temp files
4. **Alert multiple channels** - SMS + Email + Visual alarm
5. **Document recovery procedure** - Train operators how to resync
6. **Test regularly** - Practice disconnect scenarios
7. **Have manual E-stop** - Physical button for ultimate failsafe

## Integration with Train Show Systems

For professional train shows and museums:

```python
def show_emergency_handler(model):
    # 1. Hardware - Multiple safety layers
    emergency_relay.cut_all_power()
    sound_alarm()
    flash_warning_lights()

    # 2. State preservation
    state = model.export_state()

    # Add show metadata
    state['show_name'] = 'Annual Exhibition 2024'
    state['operator'] = os.environ['OPERATOR_NAME']
    state['session_start'] = session_start_time

    # Save with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'/var/rocrail/emergency_{timestamp}.json', 'w') as f:
        json.dump(state, f, indent=2)

    # 3. Alert team
    send_sms_to_team("EMERGENCY: Rocrail disconnected")
    post_to_slack("#operations", "System down - check layout!")
    log_incident_to_database(state)

    # 4. Display for visitors
    show_message_on_displays(
        "Technical difficulty - trains paused for safety"
    )

pr = PyRocrail(on_disconnect=show_emergency_handler)
```

## Troubleshooting

**Handler not called?**
- Check: Is connection loss unexpected? (Normal shutdown doesn't trigger it)
- Check: Is model loaded? (Handler only called if model exists)
- Check: Handler exceptions? (Check verbose mode output)

**Power doesn't cut?**
- Verify hardware wiring
- Test relay independently
- Check GPIO permissions (may need sudo/gpio group)
- Add error logging to handler

**State file not saved?**
- Check write permissions
- Check disk space
- Verify path exists
- Add try/except with logging

## See Also

- `examples/05_emergency_disconnect.py` - Complete working example
- [OBJECTS.md](OBJECTS.md) - Model object reference
- [TRIGGERS.md](TRIGGERS.md) - Automation and monitoring
