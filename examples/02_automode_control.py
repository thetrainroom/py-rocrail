#!/usr/bin/env python3
"""
Automode Control Example

This example demonstrates how to control locomotives in automatic mode.
In automode, Rocrail calculates routes and moves trains automatically.

Requirements:
- Rocrail server running on localhost:8051
- At least one locomotive placed in a block
- Blocks configured with routes between them
- Virtual Command Station (VCS) or real hardware interface
"""

import time
from pyrocrail.pyrocrail import PyRocrail


def main():
    print("=" * 80)
    print("AUTOMODE CONTROL EXAMPLE")
    print("=" * 80)

    try:
        with PyRocrail("localhost", 8051) as pr:
            print("\nConnected to Rocrail")
            time.sleep(2)

            # Find a locomotive that's in a block
            loco = None
            for loco_id, lc in pr.model.get_locomotives().items():
                if getattr(lc, "blockid", None):
                    loco = lc
                    break

            if not loco:
                print("\nNo locomotive found in a block!")
                print("Please place a locomotive in a block in Rocrail")
                return

            print(f"\nUsing locomotive: {loco.idx}")
            print(f"Current block: {getattr(loco, 'blockid', 'unknown')}")

            # Step 1: Reset locomotive state
            print("\nStep 1: Resetting locomotive...")
            loco.softreset()
            time.sleep(1)

            # Step 2: Turn on power
            print("Step 2: Turning power ON...")
            pr.power_on()
            time.sleep(1)

            # Step 3: Enable automatic mode
            print("Step 3: Enabling automatic mode...")
            pr.auto_on()
            time.sleep(1)

            # Step 4: Prepare locomotive for automode
            print("Step 4: Preparing locomotive for automode...")
            loco.softreset()
            time.sleep(1)

            # Step 5: Start locomotive in automatic mode
            print("Step 5: Starting locomotive (go command)...")
            loco.go()
            time.sleep(2)

            # Monitor the locomotive
            print("\nMonitoring locomotive for 10 seconds...")
            print("(Rocrail will calculate routes and move the train automatically)")

            for i in range(10):
                block = getattr(loco, "blockid", "unknown")
                dest = getattr(loco, "destblockid", "none")
                speed = getattr(loco, "V", 0)
                mode = getattr(loco, "mode", "unknown")

                print(f"  [{i+1}/10] Block: {block}, Destination: {dest}, Speed: {speed}, Mode: {mode}")
                time.sleep(1)

            # Stop the locomotive
            print("\nStopping locomotive...")
            loco.stop()
            time.sleep(1)

            # Turn off automode and power
            print("Disabling automode...")
            pr.auto_off()
            time.sleep(1)

            print("Turning power OFF...")
            pr.power_off()

            print("\nAutomode demo complete!")

        print("\nDisconnected from Rocrail")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
