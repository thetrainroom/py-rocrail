#!/usr/bin/env python3
"""
Time-Based Triggers Example

This example shows how to execute actions based on the Rocrail clock time.
Time triggers allow you to schedule automated tasks at specific times.

Requirements:
- Rocrail server running on localhost:8051
- Rocrail clock should be running (can be frozen or real-time)
"""

import time
import logging  # noqa: F401 - Imported for user to configure if needed
from pyrocrail.pyrocrail import PyRocrail, Action, Trigger

# Optional: Configure logging to see PyRocrail internal messages
# logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def hourly_report(model):
    """Execute every hour (e.g., at 08:00, 09:00, 10:00, etc.)"""
    hour = model.clock.hour
    minute = model.clock.minute
    print(f"\n[{hour:02d}:{minute:02d}] === Hourly Report ===")
    print(f"  Locomotives: {len(model.get_locomotives())}")
    print(f"  Active blocks: {sum(1 for b in model.get_blocks().values() if getattr(b, 'occ', False))}")


def morning_startup(model):
    """Execute at 08:00 - Morning startup routine"""
    print("\n[08:00] Good morning! Starting morning operations...")
    # Turn on station lights (example)
    for output_id in ["station_lights", "platform_lights"]:
        try:
            output = model.get_co(output_id)
            output.on()
            print(f"  Turned on: {output_id}")
        except KeyError:
            pass  # Output doesn't exist in this layout


def evening_shutdown(model):
    """Execute at 20:00 - Evening shutdown routine"""
    print("\n[20:00] Good evening! Starting shutdown sequence...")
    # Turn off station lights
    for output_id in ["station_lights", "platform_lights"]:
        try:
            output = model.get_co(output_id)
            output.off()
            print(f"  Turned off: {output_id}")
        except KeyError:
            pass


def every_15_minutes(model):
    """Execute every 15 minutes (e.g., 08:00, 08:15, 08:30, 08:45, etc.)"""
    hour = model.clock.hour
    minute = model.clock.minute
    print(f"[{hour:02d}:{minute:02d}] Quarter-hour check...")


def main():
    print("=" * 80)
    print("TIME-BASED TRIGGERS EXAMPLE")
    print("=" * 80)

    pr = PyRocrail("localhost", 8051)

    try:
        # Connect
        pr.start()
        print("\nConnected to Rocrail")
        time.sleep(2)

        # Display current clock
        print(f"\nCurrent Rocrail time: {pr.model.clock.hour:02d}:{pr.model.clock.minute:02d}")
        print(f"Clock divider: {pr.model.clock.divider}x")
        print(f"Clock frozen: {pr.model.clock.freeze}")

        # Register time-based actions
        print("\nRegistering time-based actions...")

        # Every hour at minute 00
        pr.add(Action(
            script=hourly_report,
            trigger_type=Trigger.TIME,
            trigger="*:0"  # XX:00 - every hour at minute 00
        ))
        print("  ✓ Hourly report at XX:00")

        # Specific time: 08:00
        pr.add(Action(
            script=morning_startup,
            trigger_type=Trigger.TIME,
            trigger="8:0"  # 08:00 exactly
        ))
        print("  ✓ Morning startup at 08:00")

        # Specific time: 20:00
        pr.add(Action(
            script=evening_shutdown,
            trigger_type=Trigger.TIME,
            trigger="20:0"  # 20:00 exactly
        ))
        print("  ✓ Evening shutdown at 20:00")

        # Every 15 minutes
        pr.add(Action(
            script=every_15_minutes,
            trigger_type=Trigger.TIME,
            trigger="*:*/15"  # Every 15 minutes
        ))
        print("  ✓ Quarter-hour check every 15 minutes")

        # Optional: Speed up the clock for testing
        print("\nSpeeding up clock to 10x for demo...")
        pr.set_clock(divider=10)
        time.sleep(1)

        # Run for a while to let triggers fire
        print("\nRunning for 60 seconds...")
        print("(Watch for time-based actions to execute)")
        print("(Press Ctrl+C to stop early)\n")

        for i in range(60):
            current_time = f"{pr.model.clock.hour:02d}:{pr.model.clock.minute:02d}"
            print(f"[{i+1}/60] Clock: {current_time}", end="\r")
            time.sleep(1)

        print("\n\nTime triggers demo complete!")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pr.stop()
        print("\nDisconnected from Rocrail")


if __name__ == "__main__":
    main()
