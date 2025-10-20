#!/usr/bin/env python3
"""Automode test with multiple moves and stop command"""

from pyrocrail.pyrocrail import PyRocrail
import time

def wait_for_destination(loco, timeout=10, poll_interval=0.2):
    """Wait for locomotive to get a destination, with timeout"""
    elapsed = 0
    while elapsed < timeout:
        dest = getattr(loco, 'destblockid', '')
        if dest:
            return dest
        time.sleep(poll_interval)
        elapsed += poll_interval
    return ''

def test_automode_multi():
    print("=" * 80)
    print("AUTOMODE TEST - MULTIPLE MOVES")
    print("=" * 80)

    pr = PyRocrail("localhost", 8051)
    pr.start()
    time.sleep(1)

    # Find locomotive
    loco = None
    for lc_id, lc in pr.model._lc_domain.items():
        if getattr(lc, 'blockid', None):
            loco = lc
            break

    start_block = getattr(loco, 'blockid')
    print(f"\nLocomotive: {loco.idx}")
    print(f"Starting block: {start_block}")

    # Soft reset locomotive FIRST to clear automode state from previous runs
    print("\n" + "=" * 80)
    print("STEP 1: Soft Reset (clear previous automode state)")
    print("=" * 80)
    loco.softreset()
    time.sleep(1)

    # Set source block sensor ON
    start_in = f"{start_block}i"
    if start_in in pr.model._fb_domain:
        pr.model._fb_domain[start_in].on()
        time.sleep(0.3)

    # Power ON
    print("\n" + "=" * 80)
    print("STEP 2: Power ON")
    print("=" * 80)
    pr.power_on()
    time.sleep(0.5)

    # Automode ON
    print("\n" + "=" * 80)
    print("STEP 3: Automode ON")
    print("=" * 80)
    pr.auto_on()
    time.sleep(1)

    # Soft reset again before starting
    print("\n" + "=" * 80)
    print("STEP 4: Soft Reset (prepare for automode)")
    print("=" * 80)
    loco.softreset()
    time.sleep(0.5)

    # Start locomotive
    print("\n" + "=" * 80)
    print("STEP 5: Start Locomotive (go)")
    print("=" * 80)
    loco.go()
    time.sleep(1)

    current_block = start_block

    # MOVE 1
    print("\n" + "=" * 80)
    print("MOVE 1")
    print("=" * 80)

    print("Waiting for destination...")
    dest = wait_for_destination(loco, timeout=5)
    print(f"{current_block} -> {dest}")

    if dest:
        dest_e = f"{dest}e"
        dest_i = f"{dest}i"
        current_i = f"{current_block}i"

        time.sleep(3)

        print(f"Trigger {dest_e} ON")
        pr.model._fb_domain[dest_e].on()
        time.sleep(1.5)

        print(f"Trigger {current_i} OFF")
        pr.model._fb_domain[current_i].off()
        time.sleep(1.5)

        print(f"Trigger {dest_i} ON")
        pr.model._fb_domain[dest_i].on()
        time.sleep(0.5)

        print(f"Trigger {dest_e} OFF")
        pr.model._fb_domain[dest_e].off()
        time.sleep(1.5)

        new_block = getattr(loco, 'blockid')
        print(f"Result: {current_block} -> {new_block}")
        current_block = new_block

    # Wait for system to settle before next move
    time.sleep(2)

    # MOVE 2
    print("\n" + "=" * 80)
    print("MOVE 2")
    print("=" * 80)

    print("Waiting for destination...")
    dest = wait_for_destination(loco, timeout=10)
    print(f"{current_block} -> {dest}")

    if dest:
        dest_e = f"{dest}e"
        dest_i = f"{dest}i"
        current_i = f"{current_block}i"

        time.sleep(3)

        print(f"Trigger {dest_e} ON")
        pr.model._fb_domain[dest_e].on()
        time.sleep(1.5)

        print(f"Trigger {current_i} OFF")
        pr.model._fb_domain[current_i].off()
        time.sleep(1.5)

        print(f"Trigger {dest_i} ON")
        pr.model._fb_domain[dest_i].on()
        time.sleep(0.5)

        print(f"Trigger {dest_e} OFF")
        pr.model._fb_domain[dest_e].off()
        time.sleep(1.5)

        new_block = getattr(loco, 'blockid')
        print(f"Result: {current_block} -> {new_block}")
        current_block = new_block

    # Wait for system to settle before next move
    time.sleep(2)

    # MOVE 3 - STOP BEFORE ENTERING
    print("\n" + "=" * 80)
    print("MOVE 3 - STOP BEFORE ENTERING BLOCK")
    print("=" * 80)

    print("Waiting for destination...")
    dest = wait_for_destination(loco, timeout=10)
    print(f"{current_block} -> {dest}")

    if dest:
        dest_e = f"{dest}e"
        dest_i = f"{dest}i"
        current_i = f"{current_block}i"

        time.sleep(3)

        print(f"Trigger {dest_e} ON (loco approaching)")
        pr.model._fb_domain[dest_e].on()
        time.sleep(0.5)

        print(f"STOP COMMAND - before entering destination block")
        loco.stop()
        time.sleep(1)

        final_block = getattr(loco, 'blockid')
        final_speed = getattr(loco, 'V')
        final_mode = getattr(loco, 'mode')

        print(f"\nState after stop:")
        print(f"  Block: {final_block} (should still be {current_block})")
        print(f"  Speed: {final_speed} (should be 0)")
        print(f"  Mode: {final_mode}")

        if final_block == current_block:
            print(f"*** SUCCESS! Locomotive stopped before entering {dest} ***")
        else:
            print(f"(INFO) Locomotive ended up in {final_block}")

        # Complete the movement by triggering IN sensor
        print(f"\nCompleting movement to finish the run...")
        print(f"Trigger {current_i} OFF")
        pr.model._fb_domain[current_i].off()
        time.sleep(0.5)

        print(f"Trigger {dest_i} ON")
        pr.model._fb_domain[dest_i].on()
        time.sleep(0.5)

        print(f"Trigger {dest_e} OFF")
        pr.model._fb_domain[dest_e].off()
        time.sleep(1)

        final_block = getattr(loco, 'blockid')
        print(f"\nFinal block after completing movement: {final_block}")
        current_block = final_block

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Started in: {start_block}")
    print(f"Final block: {getattr(loco, 'blockid')}")
    print(f"Speed: {getattr(loco, 'V')}")
    print(f"Mode: {getattr(loco, 'mode')}")

    # Cleanup
    print("\n" + "=" * 80)
    print("CLEANUP")
    print("=" * 80)

    # Turn off all sensors
    for fb_id in pr.model._fb_domain.keys():
        fb = pr.model._fb_domain[fb_id]
        if fb.state:
            fb.off()
            time.sleep(0.1)

    pr.auto_off()
    time.sleep(0.5)
    pr.power_off()
    pr.stop()

    print("\n(OK) Test complete!")


if __name__ == "__main__":
    try:
        test_automode_multi()
    except KeyboardInterrupt:
        print("\n\nInterrupted")
    except Exception as e:
        print(f"\n(ERROR) {e}")
        import traceback
        traceback.print_exc()
