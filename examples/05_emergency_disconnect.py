#!/usr/bin/env python3
"""
Emergency Disconnect Handling Example

This example demonstrates how to handle Rocrail connection loss:
1. Automatic detection when Rocrail crashes or network fails
2. Hardware emergency stop (cut power to prevent collisions)
3. State preservation for manual recovery

Requirements:
- Rocrail server running on localhost:8051
- Hardware relay for emergency power cutoff (optional but recommended for safety)
- Write permissions for state file

CRITICAL SAFETY NOTE:
When Rocrail crashes, you CANNOT send DCC commands through it!
You MUST use hardware-level emergency stop (relay, circuit breaker, etc.)
"""

import time
import json
from datetime import datetime
from pyrocrail.pyrocrail import PyRocrail


def emergency_disconnect_handler(model):
    """
    Called automatically when connection to Rocrail is lost.

    This is your safety net - use it to:
    1. CUT POWER IMMEDIATELY (hardware relay)
    2. Save layout state for recovery
    3. Alert operator

    Args:
        model: Last known Model state snapshot
    """
    print("\n" + "=" * 80)
    print("!!! EMERGENCY: CONNECTION TO ROCRAIL LOST !!!")
    print("=" * 80)

    # ==========================================================================
    # STEP 1: HARDWARE EMERGENCY STOP - CUT POWER TO TRACKS
    # ==========================================================================
    print("\n[1/3] Activating hardware emergency stop...")

    # TODO: Replace with your actual hardware control
    # Example options:

    # Option A: Raspberry Pi GPIO relay
    # try:
    #     import RPi.GPIO as GPIO
    #     EMERGENCY_STOP_PIN = 17  # GPIO pin connected to relay
    #     GPIO.setmode(GPIO.BCM)
    #     GPIO.setup(EMERGENCY_STOP_PIN, GPIO.OUT)
    #     GPIO.output(EMERGENCY_STOP_PIN, GPIO.HIGH)  # Cut power
    #     print("  ✓ Track power cut via GPIO relay")
    # except Exception as e:
    #     print(f"  ✗ GPIO relay control failed: {e}")

    # Option B: Serial relay board
    # try:
    #     import serial
    #     relay = serial.Serial('/dev/ttyUSB0', 9600)
    #     relay.write(b'RELAY1_OFF\n')  # Command depends on your relay board
    #     print("  ✓ Track power cut via serial relay")
    # except Exception as e:
    #     print(f"  ✗ Serial relay control failed: {e}")

    # Option C: Network-controlled relay (HTTP, MQTT, etc.)
    # try:
    #     import requests
    #     requests.post('http://192.168.1.100/relay/off', timeout=2)
    #     print("  ✓ Track power cut via network relay")
    # except Exception as e:
    #     print(f"  ✗ Network relay control failed: {e}")

    # For this example (no hardware), just print warning
    print("  ! WARNING: No hardware relay configured - trains may continue running!")
    print("  ! Add your hardware control code above to enable automatic power cutoff")

    # ==========================================================================
    # STEP 2: SAVE LAYOUT STATE FOR RECOVERY
    # ==========================================================================
    print("\n[2/3] Saving layout state...")

    state = model.export_state()

    # Add metadata
    state["disconnect_time"] = datetime.now().isoformat()
    state["disconnect_reason"] = "Rocrail connection lost"

    # Save to file
    state_file = "emergency_state.json"
    try:
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
        print(f"  ✓ State saved to {state_file}")
    except Exception as e:
        print(f"  ✗ Failed to save state: {e}")

    # ==========================================================================
    # STEP 3: DISPLAY RECOVERY INFORMATION
    # ==========================================================================
    print("\n[3/3] Recovery information:")

    # Show critical state for operator
    print("\n  LAST KNOWN LOCOMOTIVE POSITIONS:")
    print("  " + "-" * 76)
    for loco in state["locomotives"]:
        if loco["speed"] > 0:  # Only show moving trains
            print(f"    {loco['id']:15s} | Block: {loco['block'] or 'UNKNOWN':15s} | "
                  f"Speed: {loco['speed']:3d} | Direction: {'FWD' if loco['direction'] else 'REV'}")

    print("\n  OCCUPIED BLOCKS:")
    print("  " + "-" * 76)
    for block in state["blocks"]:
        if block["occupied"]:
            print(f"    {block['id']:15s} | Loco: {block['loco_id'] or 'UNKNOWN'}")

    print("\n  SWITCH POSITIONS:")
    print("  " + "-" * 76)
    for switch in state["switches"][:10]:  # Show first 10
        print(f"    {switch['id']:15s} | State: {switch['state']}")

    # Alert options
    print("\n  RECOMMENDED ACTIONS:")
    print("    1. Verify track power is OFF")
    print("    2. Review saved state in emergency_state.json")
    print("    3. Restart Rocrail")
    print("    4. Manually verify train positions match saved state")
    print("    5. Update Rocrail to reflect actual layout state")
    print("    6. Resume operations when safe")

    # Optional: Send alerts
    # send_sms("EMERGENCY: Rocrail disconnected, power cut")
    # send_email("Rocrail Emergency", "Connection lost, check layout")
    # trigger_alarm_sound()

    print("\n" + "=" * 80)


def main():
    print("=" * 80)
    print("EMERGENCY DISCONNECT HANDLING EXAMPLE")
    print("=" * 80)
    print("\nThis example demonstrates connection loss handling.")
    print("To test: Stop Rocrail server while this script is running")
    print()

    try:
        # Create PyRocrail with emergency disconnect handler
        pr = PyRocrail(
            "localhost",
            8051,
            verbose=True,  # Enable verbose logging to see connection events
            on_disconnect=emergency_disconnect_handler,  # Register emergency handler
        )

        # Connect
        pr.start()
        print("\n✓ Connected to Rocrail")
        time.sleep(2)

        # Display current state
        print("\nCurrent layout state:")
        print(f"  Locomotives: {len(pr.model.get_locomotives())}")
        print(f"  Blocks: {len(pr.model.get_blocks())}")
        print(f"  Switches: {len(pr.model.get_switches())}")
        print(f"  Clock: {pr.model.clock.hour:02d}:{pr.model.clock.minute:02d}")

        # Monitor connection
        print("\n" + "-" * 80)
        print("MONITORING CONNECTION")
        print("-" * 80)
        print("Stop Rocrail server now to trigger emergency disconnect handler")
        print("Or press Ctrl+C to exit normally")
        print()

        # Keep running until disconnected or interrupted
        while True:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected, "
                  f"{len([lc for lc in pr.model.get_locomotives().values() if getattr(lc, 'V', 0) > 0])} trains moving",
                  end="\r")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nNormal shutdown (Ctrl+C)")
        pr.stop()
        print("✓ Disconnected normally")

    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        pr.stop()


if __name__ == "__main__":
    main()
