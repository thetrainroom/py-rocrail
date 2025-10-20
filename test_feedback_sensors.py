#!/usr/bin/env python3
"""Test feedback sensor commands and state updates"""

from pyrocrail.pyrocrail import PyRocrail
import time

def test_feedback_sensors():
    print("=" * 80)
    print("FEEDBACK SENSOR COMMAND TEST")
    print("=" * 80)

    pr = PyRocrail("localhost", 8051)
    pr.start()
    time.sleep(2)

    print(f"\nTotal feedback sensors: {len(pr.model._fb_domain)}")

    # Get a few sensors to test
    test_sensors = list(pr.model._fb_domain.keys())[:5]
    print(f"\nTesting sensors: {', '.join(test_sensors)}")

    # STEP 1: Check initial state
    print("\n" + "=" * 80)
    print("STEP 1: Check Initial State")
    print("=" * 80)

    for fb_id in test_sensors:
        fb = pr.model._fb_domain[fb_id]
        print(f"{fb_id}: state={fb.state}")

    # STEP 2: Turn all test sensors ON
    print("\n" + "=" * 80)
    print("STEP 2: Turn All Sensors ON")
    print("=" * 80)

    for fb_id in test_sensors:
        fb = pr.model._fb_domain[fb_id]
        print(f"Sending ON command to {fb_id}...")
        fb.on()

    print("\nImmediate state (local, before server response):")
    for fb_id in test_sensors:
        fb = pr.model._fb_domain[fb_id]
        print(f"  {fb_id}: state={fb.state}")

    # STEP 3: Wait for server response
    print("\n" + "=" * 80)
    print("STEP 3: Wait 2 Seconds for Server Response")
    print("=" * 80)
    time.sleep(2)

    print("\nState after 2 seconds (should reflect server updates):")
    for fb_id in test_sensors:
        fb = pr.model._fb_domain[fb_id]
        print(f"  {fb_id}: state={fb.state}")

    # STEP 4: Turn all sensors OFF
    print("\n" + "=" * 80)
    print("STEP 4: Turn All Sensors OFF")
    print("=" * 80)

    for fb_id in test_sensors:
        fb = pr.model._fb_domain[fb_id]
        print(f"Sending OFF command to {fb_id}...")
        fb.off()

    print("\nImmediate state (local, before server response):")
    for fb_id in test_sensors:
        fb = pr.model._fb_domain[fb_id]
        print(f"  {fb_id}: state={fb.state}")

    # STEP 5: Wait for server response
    print("\n" + "=" * 80)
    print("STEP 5: Wait 2 Seconds for Server Response")
    print("=" * 80)
    time.sleep(2)

    print("\nState after 2 seconds (should reflect server updates):")
    for fb_id in test_sensors:
        fb = pr.model._fb_domain[fb_id]
        print(f"  {fb_id}: state={fb.state}")

    # STEP 6: Test calling ON twice in a row
    print("\n" + "=" * 80)
    print("STEP 6: Test Calling ON Twice (Bug Check)")
    print("=" * 80)

    test_fb_id = test_sensors[0]
    test_fb = pr.model._fb_domain[test_fb_id]

    print(f"\nBefore: {test_fb_id} state={test_fb.state}")

    print(f"Calling .on() first time...")
    test_fb.on()
    print(f"After first call: state={test_fb.state}")

    print(f"Calling .on() second time immediately...")
    test_fb.on()
    print(f"After second call: state={test_fb.state}")
    print("(Note: Second call won't send command because state is already True)")

    time.sleep(2)

    print(f"\nAfter 2 seconds: {test_fb_id} state={test_fb.state}")

    # Cleanup
    print("\n" + "=" * 80)
    print("CLEANUP: Turn all sensors OFF")
    print("=" * 80)

    for fb_id in test_sensors:
        fb = pr.model._fb_domain[fb_id]
        fb.off()

    time.sleep(1)

    pr.stop()

    print("\n(OK) Test complete!")
    print("\nCONCLUSION:")
    print("- We update self.state IMMEDIATELY when sending commands")
    print("- We do NOT wait for server confirmation")
    print("- Check if state values matched what you saw in Rocrail viewer")


if __name__ == "__main__":
    try:
        test_feedback_sensors()
    except KeyboardInterrupt:
        print("\n\nInterrupted")
    except Exception as e:
        print(f"\n(ERROR) {e}")
        import traceback
        traceback.print_exc()
