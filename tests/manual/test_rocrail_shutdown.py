#!/usr/bin/env python3
"""
Manual Test: Verify graceful shutdown detection vs crash detection

This test verifies that PyRocrail can distinguish between:
1. Graceful shutdown: Rocrail sends <sys cmd="shutdown"/> then closes
2. Crash/unexpected: Socket closes without shutdown message

Expected behavior:
- Graceful shutdown: Emergency handler NOT called
- Crash/network failure: Emergency handler IS called

Instructions:
1. Start Rocrail server
2. Run this script
3. Test BOTH scenarios:
   a) Properly shutdown Rocrail from GUI (File → Exit)
      → Should see: "Server shutdown was graceful"
      → Emergency handler NOT called
   b) Kill Rocrail process or disconnect network
      → Should see: "Unexpected disconnect - calling emergency handler"
      → Emergency handler IS called
"""

from pyrocrail.pyrocrail import PyRocrail
import time


def emergency_disconnect_handler(model):
    """Called ONLY when connection lost unexpectedly (crash, not graceful shutdown)"""
    print("\n" + "=" * 80)
    print("!!! EMERGENCY DISCONNECT HANDLER CALLED !!!")
    print("=" * 80)
    print("This means: Connection lost WITHOUT graceful shutdown message")
    print("Reason: Rocrail crashed, network failed, or process killed")
    print()
    print("In production, this would:")
    print("  1. Cut track power (hardware relay)")
    print("  2. Save layout state")
    print("  3. Alert operator")
    print("=" * 80)


def main():
    print("=" * 80)
    print("GRACEFUL SHUTDOWN vs CRASH DETECTION TEST")
    print("=" * 80)
    print()
    print("This test verifies PyRocrail distinguishes:")
    print("  • Graceful shutdown (Rocrail sends <sys cmd=\"shutdown\"/>)")
    print("  • Unexpected disconnect (crash, network failure)")
    print()
    print("Test both scenarios:")
    print("  1. Graceful: File → Exit in Rocrail GUI")
    print("     → Emergency handler should NOT be called")
    print()
    print("  2. Crash: Kill Rocrail process or disconnect network")
    print("     → Emergency handler SHOULD be called")
    print()
    input("Press ENTER to connect...")

    try:
        pr = PyRocrail(
            "localhost",
            8051,
            verbose=True,  # IMPORTANT: See all messages
            on_disconnect=emergency_disconnect_handler,
        )

        pr.start()
        print("\n✓ Connected to Rocrail")
        print()
        print("Now test one of:")
        print("  1. File → Exit (graceful shutdown)")
        print("  2. Kill process/disconnect network (crash)")
        print()
        print("Watching for shutdown message and handler behavior...\n")

        # Wait forever until disconnected
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nTest cancelled (Ctrl+C)")
        pr.stop()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
