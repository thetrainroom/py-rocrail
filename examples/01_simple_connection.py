#!/usr/bin/env python3
"""
Simple Connection Example

This example shows the most basic usage: connecting to Rocrail,
getting the model, and accessing some objects.

Requirements:
- Rocrail server running on localhost:8051
- At least one locomotive in your layout
"""

import time
import logging  # noqa: F401 - Imported for user to configure if needed
from pyrocrail.pyrocrail import PyRocrail

# Optional: Configure logging to see PyRocrail internal messages
# logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def main():
    print("=" * 80)
    print("SIMPLE ROCRAIL CONNECTION EXAMPLE")
    print("=" * 80)

    # Connect to Rocrail using context manager (automatic cleanup)
    # Context manager automatically calls pr.start() on entry and pr.stop() on exit
    try:
        with PyRocrail("localhost", 8051) as pr:
            print("\nConnected to Rocrail!")
            time.sleep(2)  # Wait for model to fully load

            # Check what's in the model
            print("\nModel loaded:")
            print(f"  Locomotives: {len(pr.model.get_locomotives())}")
            print(f"  Blocks: {len(pr.model.get_blocks())}")
            print(f"  Switches: {len(pr.model.get_switches())}")
            print(f"  Signals: {len(pr.model.get_signals())}")
            print(f"  Feedback sensors: {len(pr.model.get_feedbacks())}")

            # List all locomotives
            if pr.model.get_locomotives():
                print("\nLocomotives in your layout:")
                for loco_id, loco in pr.model.get_locomotives().items():
                    block = getattr(loco, "blockid", "unknown")
                    print(f"  - {loco_id} (in block: {block})")

                # Get first locomotive
                first_loco_id = list(pr.model.get_locomotives().keys())[0]
                loco = pr.model.get_lc(first_loco_id)
                print(f"\nExample locomotive: {first_loco_id}")
                print(f"  Current speed: {getattr(loco, 'V', 0)}")
                print(f"  Direction: {'forward' if getattr(loco, 'dir', True) else 'reverse'}")
                print(f"  Block: {getattr(loco, 'blockid', 'unknown')}")

            # Power control
            print("\nTurning power ON...")
            pr.power_on()
            time.sleep(1)

            print("Turning power OFF...")
            pr.power_off()

            print("\nConnection test successful!")

        # Automatically cleaned up here
        print("\nDisconnected from Rocrail")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
