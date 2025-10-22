#!/usr/bin/env python3
"""
Event-Based Triggers Example

This example shows how to execute actions based on layout events:
- Feedback sensors (block entry/exit)
- Block occupation changes
- Locomotive state changes

Requirements:
- Rocrail server running on localhost:8051
- At least one feedback sensor or block in your layout
- Optionally: moving trains to trigger events
"""

import time
import logging  # noqa: F401 - Imported for user to configure if needed
from pyrocrail.pyrocrail import PyRocrail, Action, Trigger

# Optional: Configure logging to see PyRocrail internal messages
# logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def on_sensor_activated(model):
    """Execute when ANY feedback sensor is activated"""
    print("\n[EVENT] Feedback sensor activated!")
    # Find which sensors are active
    active_sensors = [fb_id for fb_id, fb in model.get_feedbacks().items() if fb.state]
    print(f"  Active sensors: {', '.join(active_sensors[:5])}")  # Show first 5


def on_block_occupied(model):
    """Execute when ANY block becomes occupied"""
    print("\n[EVENT] Block occupied!")
    # Find occupied blocks
    occupied = [bk_id for bk_id, bk in model.get_blocks().items() if getattr(bk, "occ", False)]
    print(f"  Occupied blocks: {', '.join(occupied)}")


def on_locomotive_enters_station(model):
    """Execute when a locomotive enters a specific block"""
    # Example: block 'station1' becomes occupied
    try:
        station = model.get_bk("station1")
        if getattr(station, "occ", False):
            loco_id = getattr(station, "locid", "unknown")
            print(f"\n[EVENT] Locomotive {loco_id} arrived at station!")
            # Could trigger station announcement, lights, etc.
    except KeyError:
        pass  # Block 'station1' doesn't exist


def on_switch_changed(model):
    """Execute when ANY switch position changes"""
    print("\n[EVENT] Switch position changed!")


def count_active_trains(model):
    """Count how many locomotives are currently moving"""
    moving = sum(1 for lc in model.get_locomotives().values() if getattr(lc, "V", 0) > 0)
    if moving > 0:
        print(f"\n[INFO] {moving} train(s) currently moving")


def main():
    print("=" * 80)
    print("EVENT-BASED TRIGGERS EXAMPLE")
    print("=" * 80)

    pr = PyRocrail("localhost", 8051)

    try:
        # Connect
        pr.start()
        print("\nConnected to Rocrail")
        time.sleep(2)

        print("\nLayout objects:")
        print(f"  Feedback sensors: {len(pr.model.get_feedbacks())}")
        print(f"  Blocks: {len(pr.model.get_blocks())}")
        print(f"  Switches: {len(pr.model.get_switches())}")
        print(f"  Locomotives: {len(pr.model.get_locomotives())}")

        # Register event-based actions
        print("\nRegistering event-based actions...")

        # Feedback sensor events (any sensor that becomes active)
        # Using helper function: is_active(obj_id)
        pr.add(Action(
            script=on_sensor_activated,
            trigger_type=Trigger.EVENT,
            trigger="fb*",  # Match all feedback sensors
            condition="is_active(obj_id)"  # Helper function - cleaner!
        ))
        print("  ✓ Sensor activation monitor (using is_active helper)")

        # Block occupation events (any block that becomes occupied)
        # Using helper function: is_occupied(obj_id)
        pr.add(Action(
            script=on_block_occupied,
            trigger_type=Trigger.EVENT,
            trigger="bk*",  # Match all blocks
            condition="is_occupied(obj_id)"  # Helper function - much cleaner!
        ))
        print("  ✓ Block occupation monitor (using is_occupied helper)")

        # Switch events (any switch that changes position)
        pr.add(Action(
            script=on_switch_changed,
            trigger_type=Trigger.EVENT,
            trigger="sw*"  # Match all switches
        ))
        print("  ✓ Switch change monitor")

        # Specific block event (if 'station1' exists)
        # Combining helpers with AND logic
        pr.add(Action(
            script=on_locomotive_enters_station,
            trigger_type=Trigger.EVENT,
            trigger="station1",  # Specific block ID
            condition="is_occupied(obj_id) and count_moving() > 0"  # Multiple helpers!
        ))
        print("  ✓ Station arrival monitor with helper conditions")

        # Time-based check combined with events
        pr.add(Action(
            script=count_active_trains,
            trigger_type=Trigger.TIME,
            trigger="*:*/5"  # Every 5 minutes
        ))
        print("  ✓ Active trains check every 5 minutes")

        # Run and monitor events
        print("\nMonitoring layout events for 60 seconds...")
        print("(Trigger events by moving trains or switching turnouts in Rocrail)")
        print("(Press Ctrl+C to stop early)\n")

        for i in range(60):
            print(f"[{i+1}/60] Monitoring...", end="\r")
            time.sleep(1)

        print("\n\nEvent triggers demo complete!")

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
