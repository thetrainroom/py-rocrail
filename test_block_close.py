#!/usr/bin/env python3
"""Test block close command"""

from pyrocrail.pyrocrail import PyRocrail
import time

def test_block_close():
    print("=" * 80)
    print("BLOCK CLOSE COMMAND TEST")
    print("=" * 80)

    pr = PyRocrail("localhost", 8051)
    pr.start()
    time.sleep(1)

    # Test with cb1 and cb2
    print("\nChecking initial state of cb1 and cb2:")
    for bk_id in ['cb1', 'cb2']:
        if bk_id in pr.model._bk_domain:
            bk = pr.model._bk_domain[bk_id]
            print(f"{bk_id}:")
            print(f"  state: {getattr(bk, 'state', 'unknown')}")
            print(f"  local is_closed(): {bk.is_closed()}")

    # Close cb1
    print("\n" + "=" * 80)
    print("Sending CLOSE command to cb1")
    print("=" * 80)
    pr.model._bk_domain['cb1'].close()

    print("\nImmediate state (local):")
    bk = pr.model._bk_domain['cb1']
    print(f"cb1 state: {getattr(bk, 'state', 'unknown')}")
    print(f"cb1 is_closed(): {bk.is_closed()}")

    # Wait for server response
    print("\nWaiting 2 seconds for server response...")
    time.sleep(2)

    print("\nState after 2 seconds (should reflect server update):")
    print(f"cb1 state: {getattr(bk, 'state', 'unknown')}")
    print(f"cb1 is_closed(): {bk.is_closed()}")

    # Close cb2
    print("\n" + "=" * 80)
    print("Sending CLOSE command to cb2")
    print("=" * 80)
    pr.model._bk_domain['cb2'].close()

    time.sleep(2)

    # Check both blocks
    print("\n" + "=" * 80)
    print("Final state check")
    print("=" * 80)
    for bk_id in ['cb1', 'cb2']:
        if bk_id in pr.model._bk_domain:
            bk = pr.model._bk_domain[bk_id]
            print(f"{bk_id}:")
            print(f"  state: {getattr(bk, 'state', 'unknown')}")
            print(f"  is_closed(): {bk.is_closed()}")

    # Try to open cb1
    print("\n" + "=" * 80)
    print("Sending OPEN command to cb1")
    print("=" * 80)
    pr.model._bk_domain['cb1'].open()
    time.sleep(2)

    bk = pr.model._bk_domain['cb1']
    print(f"\ncb1 after OPEN:")
    print(f"  state: {getattr(bk, 'state', 'unknown')}")
    print(f"  is_closed(): {bk.is_closed()}")

    pr.stop()

    print("\n(OK) Test complete!")
    print("\nCheck in Rocrail viewer if cb1 and cb2 actually showed as closed")


if __name__ == "__main__":
    try:
        test_block_close()
    except KeyboardInterrupt:
        print("\n\nInterrupted")
    except Exception as e:
        print(f"\n(ERROR) {e}")
        import traceback
        traceback.print_exc()
