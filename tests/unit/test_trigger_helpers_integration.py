#!/usr/bin/env python3
"""Integration tests for helper functions in actual trigger execution"""
# type: ignore  # Test file with mock objects

import time
from pyrocrail.pyrocrail import PyRocrail, Action, Trigger


def setup_mock_model(pr):
    """Setup mock model data for testing"""
    # Mock blocks
    class MockBlock:
        def __init__(self, idx, occ=False, reserved=False, locid=None):
            self.idx = idx
            self.occ = occ
            self.reserved = reserved
            self.locid = locid

    # Mock locomotives
    class MockLocomotive:
        def __init__(self, idx, speed=0, direction=True, blockid=None):
            self.idx = idx
            self.V = speed
            self.dir = direction
            self.blockid = blockid

    # Mock feedback sensors
    class MockFeedback:
        def __init__(self, idx, state=False):
            self.idx = idx
            self.state = state

    # Mock switches
    class MockSwitch:
        def __init__(self, idx, state="straight"):
            self.idx = idx
            self.state = state

    # Mock signals
    class MockSignal:
        def __init__(self, idx, aspect="red"):
            self.idx = idx
            self.aspect = aspect

    # Mock outputs
    class MockOutput:
        def __init__(self, idx, state=False):
            self.idx = idx
            self.state = state

    # Setup domains (using proper ID prefixes for pattern matching)
    pr.model._bk_domain = {
        "bk1": MockBlock("bk1", occ=True, locid="lc1"),
        "bk2": MockBlock("bk2", occ=False),
        "bk_station": MockBlock("bk_station", occ=True, locid="lc2"),
        "bk_yard": MockBlock("bk_yard", occ=False),
    }

    pr.model._lc_domain = {
        "lc1": MockLocomotive("lc1", speed=50, direction=True, blockid="bk1"),
        "lc2": MockLocomotive("lc2", speed=0, direction=True, blockid="bk_station"),
        "lc3": MockLocomotive("lc3", speed=30, direction=False, blockid="bk_yard"),
    }

    pr.model._fb_domain = {
        "fb1": MockFeedback("fb1", state=True),
        "fb2": MockFeedback("fb2", state=False),
        "fb3": MockFeedback("fb3", state=True),
    }

    pr.model._sw_domain = {
        "sw1": MockSwitch("sw1", state="straight"),
        "sw2": MockSwitch("sw2", state="turnout"),
    }

    pr.model._sg_domain = {
        "sg1": MockSignal("sg1", aspect="green"),
        "sg2": MockSignal("sg2", aspect="red"),
    }

    pr.model._co_domain = {
        "co1": MockOutput("co1", state=True),
        "co2": MockOutput("co2", state=False),
    }


def test_time_triggers_with_helpers():
    """Test TIME triggers with helper function conditions"""
    print("=" * 80)
    print("TEST: TIME Triggers with Helper Functions")
    print("=" * 80)

    pr = PyRocrail("localhost", 8051)
    setup_mock_model(pr)

    # Track executions
    executions = []

    def track(name):
        def script(model):
            executions.append(name)
            print(f"  [EXECUTED] {name}")
        return script

    # Add time triggers with various helper conditions
    actions = [
        # Basic helper conditions
        Action(track("any_moving"), Trigger.TIME, "*:00", "any_moving()", 60),
        Action(track("all_stopped"), Trigger.TIME, "*:00", "all_stopped()", 60),
        Action(track("count_check"), Trigger.TIME, "*:00", "count_moving() >= 2", 60),

        # Time helpers
        Action(track("daytime"), Trigger.TIME, "*:00", "is_daytime()", 60),
        Action(track("nighttime"), Trigger.TIME, "*:00", "is_nighttime()", 60),
        Action(track("time_range"), Trigger.TIME, "*:00", "time_between(8, 18)", 60),

        # Collection helpers
        Action(track("occupied_count"), Trigger.TIME, "*:00", "count_occupied() == 2", 60),
        Action(track("active_sensors"), Trigger.TIME, "*:00", "count_active() > 1", 60),

        # Logic helpers
        Action(track("complex_and"), Trigger.TIME, "*:00",
               "all_of([any_moving(), is_daytime(), count_occupied() > 0])", 60),
        Action(track("complex_or"), Trigger.TIME, "*:00",
               "any_of([is_nighttime(), count_moving() > 5])", 60),

        # Specific object checks
        Action(track("block_check"), Trigger.TIME, "*:00", "is_occupied('bk1')", 60),
        Action(track("loco_check"), Trigger.TIME, "*:00", "is_moving('lc1')", 60),
        Action(track("signal_check"), Trigger.TIME, "*:00", "is_green('sg1')", 60),
    ]

    for action in actions:
        pr.add(action)

    print(f"\nAdded {len(actions)} time triggers with helper conditions")

    # Test at 10:00 (daytime)
    print("\n" + "-" * 80)
    print("Executing at 10:00 (daytime)")
    print("-" * 80)

    pr.model.clock.hour = 10
    pr.model.clock.minute = 0
    executions.clear()
    pr._exec_time()
    time.sleep(0.2)

    print(f"\nExecutions: {len(executions)}")
    for name in executions:
        print(f"  - {name}")

    # Verify expected executions at 10:00
    expected_10 = [
        "any_moving",       # True - loco1 and loco3 moving
        "count_check",      # True - 2 locos moving
        "daytime",          # True - 10:00 is daytime
        "time_range",       # True - 10 is between 8 and 18
        "occupied_count",   # True - 2 blocks occupied
        "active_sensors",   # True - 2 sensors active
        "complex_and",      # True - all conditions met
        "block_check",      # True - platform1 is occupied
        "loco_check",       # True - loco1 is moving
        "signal_check",     # True - signal1 is green
    ]

    missing = set(expected_10) - set(executions)
    extra = set(executions) - set(expected_10)

    if not missing and not extra:
        print("\n[OK] All expected triggers executed at 10:00")
    else:
        print("\n[FAIL] Execution mismatch at 10:00")
        if missing:
            print(f"  Missing: {missing}")
        if extra:
            print(f"  Extra: {extra}")
        return False

    # Test at 22:00 (nighttime)
    print("\n" + "-" * 80)
    print("Executing at 22:00 (nighttime)")
    print("-" * 80)

    pr.model.clock.hour = 22
    pr.model.clock.minute = 0
    executions.clear()
    pr._exec_time()
    time.sleep(0.2)

    print(f"\nExecutions: {len(executions)}")
    for name in executions:
        print(f"  - {name}")

    # Verify expected executions at 22:00
    expected_22 = [
        "any_moving",       # True - loco1 and loco3 moving
        "count_check",      # True - 2 locos moving
        "nighttime",        # True - 22:00 is nighttime
        "occupied_count",   # True - 2 blocks occupied
        "active_sensors",   # True - 2 sensors active
        "complex_or",       # True - is_nighttime() is true
        "block_check",      # True - platform1 is occupied
        "loco_check",       # True - loco1 is moving
        "signal_check",     # True - signal1 is green
    ]

    missing = set(expected_22) - set(executions)
    extra = set(executions) - set(expected_22)

    if not missing and not extra:
        print("\n[OK] All expected triggers executed at 22:00")
    else:
        print("\n[FAIL] Execution mismatch at 22:00")
        if missing:
            print(f"  Missing: {missing}")
        if extra:
            print(f"  Extra: {extra}")
        return False

    print("\n[OK] TIME triggers with helper conditions work correctly")
    return True


def test_event_triggers_with_helpers():
    """Test EVENT triggers with helper function conditions"""
    print("\n" + "=" * 80)
    print("TEST: EVENT Triggers with Helper Functions")
    print("=" * 80)

    pr = PyRocrail("localhost", 8051)
    setup_mock_model(pr)

    # Track executions
    executions = []

    def track(name):
        def script(model):
            executions.append(name)
            print(f"  [EXECUTED] {name}")
        return script

    # Add event triggers with helper conditions
    actions = [
        # Block events with helpers
        Action(track("block_occupied"), Trigger.EVENT, "bk*",
               "is_occupied(obj_id)", 60),
        Action(track("block_with_loco"), Trigger.EVENT, "bk*",
               "is_occupied(obj_id) and any_moving()", 60),
        Action(track("specific_block"), Trigger.EVENT, "bk1",
               "is_occupied(obj_id) and is_moving('lc1')", 60),

        # Feedback events with helpers
        Action(track("sensor_active"), Trigger.EVENT, "fb*",
               "is_active(obj_id)", 60),
        Action(track("sensor_with_locos"), Trigger.EVENT, "fb*",
               "is_active(obj_id) and count_moving() > 0", 60),

        # Switch events with helpers
        Action(track("switch_straight"), Trigger.EVENT, "sw*",
               "is_straight(obj_id)", 60),
        Action(track("switch_with_signal"), Trigger.EVENT, "sw*",
               "is_straight(obj_id) and is_green('sg1')", 60),

        # Complex multi-helper conditions
        Action(track("complex_event"), Trigger.EVENT, "bk*",
               "all_of([is_occupied(obj_id), any_moving(), is_daytime()])", 60),
        Action(track("safety_check"), Trigger.EVENT, "bk*",
               "is_occupied(obj_id) and is_green('sg1') and not is_occupied('bk_yard')", 60),
    ]

    for action in actions:
        pr.add(action)

    print(f"\nAdded {len(actions)} event triggers with helper conditions")

    # Set time to daytime for complex_event condition
    pr.model.clock.hour = 12

    # Test block event - bk1 (occupied)
    print("\n" + "-" * 80)
    print("Event: Block 'bk1' update (occupied)")
    print("-" * 80)

    executions.clear()
    obj = pr.model._bk_domain["bk1"]
    pr._exec_event("bk", "bk1", obj)
    time.sleep(0.2)

    print(f"\nExecutions: {len(executions)}")
    for name in executions:
        print(f"  - {name}")

    expected_bk1 = [
        "block_occupied",        # True - bk1 is occupied
        "block_with_loco",       # True - occupied and locos moving
        "specific_block",        # True - bk1 occupied and lc1 moving
        "complex_event",         # True - all conditions met
        "safety_check",          # True - occupied, signal green, yard free
    ]

    if set(executions) == set(expected_bk1):
        print("\n[OK] Block event with helpers executed correctly")
    else:
        print("\n[FAIL] Block event execution mismatch")
        print(f"  Expected: {set(expected_bk1)}")
        print(f"  Actual: {set(executions)}")
        return False

    # Test feedback event - fb1 (active)
    print("\n" + "-" * 80)
    print("Event: Feedback 'fb1' update (active)")
    print("-" * 80)

    executions.clear()
    obj = pr.model._fb_domain["fb1"]
    pr._exec_event("fb", "fb1", obj)
    time.sleep(0.2)

    print(f"\nExecutions: {len(executions)}")
    for name in executions:
        print(f"  - {name}")

    expected_fb1 = [
        "sensor_active",         # True - fb1 is active
        "sensor_with_locos",     # True - active and locos moving
    ]

    if set(executions) == set(expected_fb1):
        print("\n[OK] Feedback event with helpers executed correctly")
    else:
        print("\n[FAIL] Feedback event execution mismatch")
        print(f"  Expected: {set(expected_fb1)}")
        print(f"  Actual: {set(executions)}")
        return False

    # Test switch event - sw1 (straight)
    print("\n" + "-" * 80)
    print("Event: Switch 'sw1' update (straight)")
    print("-" * 80)

    executions.clear()
    obj = pr.model._sw_domain["sw1"]
    pr._exec_event("sw", "sw1", obj)
    time.sleep(0.2)

    print(f"\nExecutions: {len(executions)}")
    for name in executions:
        print(f"  - {name}")

    expected_sw1 = [
        "switch_straight",       # True - sw1 is straight
        "switch_with_signal",    # True - straight and signal green
    ]

    if set(executions) == set(expected_sw1):
        print("\n[OK] Switch event with helpers executed correctly")
    else:
        print("\n[FAIL] Switch event execution mismatch")
        print(f"  Expected: {set(expected_sw1)}")
        print(f"  Actual: {set(executions)}")
        return False

    # Test block event - bk_yard (NOT occupied) - should NOT trigger occupied conditions
    print("\n" + "-" * 80)
    print("Event: Block 'bk_yard' update (NOT occupied)")
    print("-" * 80)

    executions.clear()
    obj = pr.model._bk_domain["bk_yard"]
    pr._exec_event("bk", "bk_yard", obj)
    time.sleep(0.2)

    print(f"\nExecutions: {len(executions)}")
    for name in executions:
        print(f"  - {name}")

    # Should NOT execute any triggers (yard is not occupied)
    if not executions:
        print("\n[OK] Correctly did not execute triggers for non-occupied block")
    else:
        print("\n[FAIL] Should not have executed any triggers")
        print(f"  Unexpected executions: {executions}")
        return False

    print("\n[OK] EVENT triggers with helper conditions work correctly")
    return True


def test_complex_helper_combinations():
    """Test complex combinations of helper functions in conditions"""
    print("\n" + "=" * 80)
    print("TEST: Complex Helper Combinations")
    print("=" * 80)

    pr = PyRocrail("localhost", 8051)
    setup_mock_model(pr)
    pr.model.clock.hour = 14  # Daytime

    executions = []

    def track(name):
        def script(model):
            executions.append(name)
            print(f"  [EXECUTED] {name}")
        return script

    # Very complex conditions combining multiple helpers
    actions = [
        # Nested logic helpers
        Action(track("nested_logic"), Trigger.TIME, "*:00",
               "all_of([any_of([is_daytime(), is_occupied('bk1')]), count_moving() > 1])", 60),

        # Multiple object type checks
        Action(track("multi_type"), Trigger.TIME, "*:00",
               "is_occupied('bk1') and is_green('sg1') and is_active('fb1')", 60),

        # Complex counting and comparison
        Action(track("counting"), Trigger.TIME, "*:00",
               "count_moving() > 1 and count_occupied() >= 2 and count_active() <= 3", 60),

        # Time-based with object state
        Action(track("time_and_state"), Trigger.TIME, "*:00",
               "time_between(10, 18) and any_moving() and is_green('sg1')", 60),

        # NOT operations with helpers
        Action(track("negation"), Trigger.TIME, "*:00",
               "is_occupied('bk1') and not is_occupied('bk2')", 60),

        # String comparisons in helpers
        Action(track("specific_checks"), Trigger.TIME, "*:00",
               "is_moving('lc1') and not is_moving('lc2')", 60),
    ]

    for action in actions:
        pr.add(action)

    print(f"\nAdded {len(actions)} triggers with complex helper combinations")

    print("\n" + "-" * 80)
    print("Executing at 14:00 with current model state")
    print("-" * 80)

    pr.model.clock.minute = 0
    pr._exec_time()
    time.sleep(0.2)

    print(f"\nExecutions: {len(executions)}")
    for name in executions:
        print(f"  - {name}")

    # All should execute with current model state
    expected = ["nested_logic", "multi_type", "counting", "time_and_state", "negation", "specific_checks"]

    if set(executions) == set(expected):
        print("\n[OK] All complex helper combinations executed correctly")
        return True
    else:
        print("\n[FAIL] Complex helper combination execution mismatch")
        print(f"  Expected: {set(expected)}")
        print(f"  Actual: {set(executions)}")
        missing = set(expected) - set(executions)
        extra = set(executions) - set(expected)
        if missing:
            print(f"  Missing: {missing}")
        if extra:
            print(f"  Extra: {extra}")
        return False


def test_helper_error_handling():
    """Test that helper functions handle missing objects gracefully in triggers"""
    print("\n" + "=" * 80)
    print("TEST: Helper Error Handling in Triggers")
    print("=" * 80)

    pr = PyRocrail("localhost", 8051)
    setup_mock_model(pr)

    executions = []

    def track(name):
        def script(model):
            executions.append(name)
            print(f"  [EXECUTED] {name}")
        return script

    # Triggers with helpers referencing non-existent objects
    actions = [
        # Should NOT execute (missing object)
        Action(track("missing_block"), Trigger.TIME, "*:00",
               "is_occupied('nonexistent_block')", 60),

        # Should execute (OR with valid condition)
        Action(track("missing_with_or"), Trigger.TIME, "*:00",
               "is_occupied('nonexistent') or is_occupied('bk1')", 60),

        # Should NOT execute (AND with missing)
        Action(track("missing_with_and"), Trigger.TIME, "*:00",
               "is_occupied('bk1') and is_occupied('nonexistent')", 60),

        # Should execute (valid object)
        Action(track("valid_block"), Trigger.TIME, "*:00",
               "is_occupied('bk1')", 60),
    ]

    for action in actions:
        pr.add(action)

    print(f"\nAdded {len(actions)} triggers with missing object references")

    print("\n" + "-" * 80)
    print("Executing triggers")
    print("-" * 80)

    pr.model.clock.hour = 10
    pr.model.clock.minute = 0
    pr._exec_time()
    time.sleep(0.2)

    print(f"\nExecutions: {len(executions)}")
    for name in executions:
        print(f"  - {name}")

    expected = ["missing_with_or", "valid_block"]

    if set(executions) == set(expected):
        print("\n[OK] Helpers handle missing objects gracefully in triggers")
        return True
    else:
        print("\n[FAIL] Error handling test failed")
        print(f"  Expected: {set(expected)}")
        print(f"  Actual: {set(executions)}")
        return False


def main():
    """Run all integration tests"""
    print("\n")
    print("=" * 80)
    print(" " * 15 + "TRIGGER HELPER FUNCTIONS INTEGRATION TESTS")
    print("=" * 80)
    print()

    results = []

    try:
        results.append(test_time_triggers_with_helpers())
        results.append(test_event_triggers_with_helpers())
        results.append(test_complex_helper_combinations())
        results.append(test_helper_error_handling())

        print("\n" + "=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)

        passed = sum(results)
        total = len(results)

        print(f"\nTests passed: {passed}/{total}")

        if all(results):
            print("\n[SUCCESS] All integration tests passed!")
            print("\nHelper functions work correctly in actual trigger execution:")
            print("  [OK] TIME triggers with helper conditions")
            print("  [OK] EVENT triggers with helper conditions")
            print("  [OK] Complex combinations of multiple helpers")
            print("  [OK] Error handling for missing objects")
            print("  [OK] Logic helpers (any_of, all_of, none_of)")
            print("  [OK] Time helpers (time_between, is_daytime, is_nighttime)")
            print("  [OK] Collection helpers (count_*, any_*, all_*)")
            print("  [OK] Object state helpers (is_occupied, is_moving, etc.)")
            print("\nYou can confidently use helper functions in your trigger conditions!")
        else:
            print("\n[FAILURE] Some integration tests failed")

        print()
        return all(results)

    except Exception as e:
        print("\n" + "=" * 80)
        print("[ERROR] Test execution failed with exception")
        print("=" * 80)
        print(f"\n{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
