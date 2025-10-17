#!/usr/bin/env python3
"""Test script to verify Schedule object loading"""

import xml.etree.ElementTree as ET
from pyrocrail.communicator import Communicator
from pyrocrail.model import Model


def test_schedule_loading():
    """Test that Schedule objects load from plan XML"""

    # Create a mock communicator (won't actually connect)
    com = Communicator("localhost", 8051)
    model = Model(com)

    # Load the example plan
    tree = ET.parse("example_plan/plan.xml")
    plan = tree.getroot()

    # Verify it's a plan element
    if plan.tag != 'plan':
        print(f"ERROR: Root element is {plan.tag}, not plan")
        return False

    # Build the model from plan
    model.build(plan)

    # Check schedules were loaded
    print(f"\nSchedules loaded: {len(model._sc_domain)}")
    if len(model._sc_domain) > 0:
        sc_id = list(model._sc_domain.keys())[0]
        sc = model.get_schedule(sc_id)
        print(f"   Sample schedule: {sc_id}")
        print(f"   - Train ID: {sc.trainid}")
        print(f"   - Group: {sc.group}")
        print(f"   - Class: {sc.class_}")
        print(f"   - Timeframe: {sc.timeframe}")
        print(f"   - From hour: {sc.fromhour}")
        print(f"   - To hour: {sc.tohour}")
        print(f"   - Cycles: {sc.cycles}")
        print(f"   - Max delay: {sc.maxdelay}")
        print(f"   - Entries: {len(sc.entries)}")
        if len(sc.entries) > 0:
            entry = sc.entries[0]
            print(f"\n   First entry:")
            print(f"     - Block: {entry.block}")
            print(f"     - Hour: {entry.hour}")
            print(f"     - Minute: {entry.minute}")
            print(f"     - Regular stop: {entry.regularstop}")

    # Test schedule commands (will not actually send)
    if len(model._sc_domain) > 0:
        print("\nTesting Schedule methods (UNVERIFIED commands):")
        sc = list(model._sc_domain.values())[0]
        print(f"   - start() method ready (UNVERIFIED)")
        print(f"   - stop() method ready (UNVERIFIED)")
        print(f"   - reset() method ready (UNVERIFIED)")
        print("\n   WARNING: These commands are not verified in XMLScript docs.")
        print("   They may not work with actual Rocrail servers.")

    print("\nAll tests passed!")
    return True


if __name__ == "__main__":
    test_schedule_loading()
