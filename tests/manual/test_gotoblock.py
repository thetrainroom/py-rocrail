#!/usr/bin/env python3
"""
Manual Test: Verify gotoblock() command works with RCP interface

This test verifies that the gotoblock() command works correctly via the
RCP (XML-over-TCP) interface, not just XML scripting.

Expected behavior:
- Command is sent with correct XML format
- Locomotive receives destination block assignment
- No errors from Rocrail server

Instructions:
1. Start Rocrail server with your layout
2. Ensure you have at least one locomotive and multiple blocks
3. Run this script
4. Observe locomotive receives gotoblock command
5. Check Rocrail trace/log for command processing
"""

from pyrocrail.pyrocrail import PyRocrail
import time
import logging

# Enable verbose logging to see commands being sent
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def main():
    print("=" * 80)
    print("GOTOBLOCK COMMAND TEST (RCP Interface)")
    print("=" * 80)
    print()
    print("This test verifies the gotoblock() command works via RCP protocol")
    print()

    try:
        with PyRocrail("localhost", 8051, verbose=True) as pr:
            print("✓ Connected to Rocrail")
            time.sleep(2)  # Wait for model to fully load

            # Check available locomotives and blocks
            locos = pr.model.get_locomotives()
            blocks = pr.model.get_blocks()

            if not locos:
                print("\n❌ ERROR: No locomotives found in layout!")
                print("Please add at least one locomotive to your Rocrail plan")
                return

            if len(blocks) < 2:
                print("\n❌ ERROR: Need at least 2 blocks for testing!")
                print(f"Found only {len(blocks)} block(s)")
                return

            print(f"\n✓ Found {len(locos)} locomotive(s)")
            print(f"✓ Found {len(blocks)} block(s)")

            # List available locomotives and blocks
            print("\nAvailable locomotives:")
            for loco_id, loco in locos.items():
                block = getattr(loco, "blockid", "unknown")
                print(f"  - {loco_id} (currently in: {block})")

            print("\nAvailable blocks:")
            for block_id in list(blocks.keys())[:10]:  # Show first 10
                print(f"  - {block_id}")

            # Get first locomotive
            loco_id = list(locos.keys())[0]
            loco = pr.model.get_lc(loco_id)
            current_block = getattr(loco, "blockid", "unknown")

            print(f"\nTest locomotive: {loco_id}")
            print(f"Current block: {current_block}")

            # Find adjacent block via routes
            routes = pr.model.get_routes()
            print(f"\nSearching for valid routes from {current_block}...")

            target_block = None
            target_route = None

            for route_id, route in routes.items():
                # Find routes starting from current block
                if route.bka == current_block:
                    dest_block_id = route.bkb
                    if dest_block_id in blocks:
                        dest_block = blocks[dest_block_id]
                        # Check if destination block is free
                        is_free = (not getattr(dest_block, 'reserved', False) and
                                  not getattr(dest_block, 'occ', False) and
                                  getattr(dest_block, 'state', 'closed') != 'closed')

                        status = "FREE ✓" if is_free else "OCCUPIED/RESERVED ✗"
                        print(f"  Route {route_id}: {current_block} → {dest_block_id} [{status}]")

                        if is_free and not target_block:
                            target_block = dest_block_id
                            target_route = route_id

            if not target_block:
                print("\n❌ ERROR: No free adjacent blocks found!")
                print("Please ensure there are routes from the current block to free blocks")
                return

            print(f"\n✓ Selected route: {target_route}")
            print(f"✓ Target block: {target_block}")

            # Enable power and automode
            print(f"\n{'=' * 80}")
            print(f"ENABLING AUTOMODE")
            print(f"{'=' * 80}")
            print("Turning power ON...")
            pr.power_on()
            time.sleep(1)

            print("Enabling auto mode...")
            pr.auto_on()
            time.sleep(1)
            print("✓ Automode enabled!")

            print(f"\n{'=' * 80}")
            print(f"SENDING GOTOBLOCK COMMAND")
            print(f"{'=' * 80}")
            print(f"Locomotive: {loco_id}")
            print(f"Current block: {current_block}")
            print(f"Target block: {target_block} (via route {target_route})")
            print(f"Command: <lc id=\"{loco_id}\" cmd=\"gotoblock\" blockid=\"{target_block}\"/>")
            print()

            # Send the gotoblock command
            print("Sending gotoblock command...")
            loco.gotoblock(target_block)
            print("✓ Destination set!")

            time.sleep(1)

            print("\nSending go() command to start locomotive...")
            loco.go()
            print("✓ Go command sent!")

            # Wait longer to see block reservations and movement
            print("\nWaiting 15 seconds to observe block reservations and movement...")
            print("Watch for:")
            print("  - Block reservations in the route")
            print("  - Locomotive speed changes")
            print("  - Block transitions")
            print()

            for i in range(15):
                time.sleep(1)
                # Check locomotive state
                current = getattr(loco, "blockid", "unknown")
                dest = getattr(loco, "destblockid", "unknown")
                speed = getattr(loco, "V", 0)
                mode = getattr(loco, "mode", "unknown")

                # Check target block state
                if target_block in blocks:
                    tgt_block = blocks[target_block]
                    tgt_reserved = getattr(tgt_block, "reserved", False)
                    tgt_occ = getattr(tgt_block, "occ", False)
                    tgt_state = f"[R]" if tgt_reserved else "[F]"
                    tgt_state += f"[O]" if tgt_occ else ""
                else:
                    tgt_state = "[?]"

                print(f"  [{i+1:2d}s] Loco: {current} → {dest} | Speed: {speed:3d} | Mode: {mode:10s} | Target {target_block}: {tgt_state}")

            # Check if destination was updated
            updated_dest = getattr(loco, "destblockid", None)
            if updated_dest:
                print(f"\n✓ Destination block updated: {updated_dest}")
            else:
                print("\nℹ Destination block attribute not updated")
                print("  (This is normal - check Rocrail trace for command processing)")

            print(f"\n{'=' * 80}")
            print("TEST COMPLETED")
            print(f"{'=' * 80}")
            print("\nResults:")
            print("  1. Command sent successfully")
            print("  2. Automode enabled - locomotive should have moved")
            print("  3. Block reservations should be visible in log")
            print(f"  4. Final block: {getattr(loco, 'blockid', 'unknown')}")
            print(f"  5. Final destination: {getattr(loco, 'destblockid', 'unknown')}")
            print()
            print("Cleanup: Stopping automode and power...")
            pr.auto_off()
            time.sleep(0.5)
            pr.power_off()
            print("✓ Cleanup complete")
            print()

            # Test with variable reference (if variables exist)
            variables = pr.model.get_variables() if hasattr(pr.model, 'get_variables') else {}
            if variables:
                var_id = list(variables.keys())[0]
                print(f"\nBonus test: Variable reference")
                print(f"Command: loco.gotoblock('@{var_id}')")
                loco.gotoblock(f"@{var_id}")
                print("✓ Variable reference command sent!")
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nTest cancelled (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
