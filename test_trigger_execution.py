#!/usr/bin/env python3
"""Test that trigger actions are actually executed"""

import time
from pyrocrail.pyrocrail import PyRocrail, Action, Trigger


def test_time_trigger_execution():
    """Test that TIME triggers actually execute scripts"""
    print("="*80)
    print("TEST: TIME Trigger Execution")
    print("="*80)

    # Track execution
    executions = []

    def track_execution(name):
        """Return a script that tracks when it's called"""
        def script(model):
            executions.append({
                'name': name,
                'time': f"{model.clock.hour}:{model.clock.minute:02d}",
                'timestamp': time.time()
            })
            print(f"  [EXECUTED] {name} at {model.clock.hour}:{model.clock.minute:02d}")
        return script

    # Create PyRocrail (won't connect to real server)
    pr = PyRocrail("localhost", 8051)

    # Add various time triggers
    actions = [
        Action(track_execution("exact_time"), Trigger.TIME, "12:30", "", 60),
        Action(track_execution("every_hour"), Trigger.TIME, "*:00", "", 60),
        Action(track_execution("every_2_hours"), Trigger.TIME, "*/2:00", "", 60),
        Action(track_execution("every_15_min"), Trigger.TIME, "*:*/15", "", 60),
        Action(track_execution("with_condition"), Trigger.TIME, "*:00", "hour >= 10", 60),
        Action(track_execution("continuous"), Trigger.TIME, None, "", 60),
    ]

    for action in actions:
        pr.add(action)

    print(f"\nAdded {len(actions)} time-based actions")
    print(f"Actions in _time_actions: {len(pr._time_actions)}")

    # Simulate clock updates
    print("\n" + "-"*80)
    print("Simulating clock updates...")
    print("-"*80)

    test_times = [
        (10, 0),   # Should trigger: every_hour, every_2_hours, with_condition, continuous
        (10, 15),  # Should trigger: every_15_min, continuous
        (10, 30),  # Should trigger: continuous
        (11, 0),   # Should trigger: every_hour, with_condition, continuous
        (12, 0),   # Should trigger: every_hour, every_2_hours, with_condition, continuous
        (12, 30),  # Should trigger: exact_time, continuous
        (9, 0),    # Should trigger: every_hour, NOT with_condition (hour < 10), continuous
    ]

    for hour, minute in test_times:
        print(f"\nClock update: {hour:02d}:{minute:02d}")

        # Update model clock
        pr.model.clock.hour = hour
        pr.model.clock.minute = minute

        # Execute time triggers
        pr._exec_time()

        # Small delay to see execution
        time.sleep(0.1)

    print("\n" + "="*80)
    print(f"RESULTS: {len(executions)} executions recorded")
    print("="*80)

    # Group by time
    by_time = {}
    for exec_info in executions:
        t = exec_info['time']
        if t not in by_time:
            by_time[t] = []
        by_time[t].append(exec_info['name'])

    for t in sorted(by_time.keys()):
        print(f"\n{t}:")
        for name in by_time[t]:
            print(f"  - {name}")

    # Verify expected executions
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)

    expected = {
        '10:00': ['every_hour', 'every_2_hours', 'every_15_min', 'with_condition', 'continuous'],
        '10:15': ['every_15_min', 'continuous'],
        '10:30': ['every_15_min', 'continuous'],
        '11:00': ['every_hour', 'every_15_min', 'with_condition', 'continuous'],
        '12:00': ['every_hour', 'every_2_hours', 'every_15_min', 'with_condition', 'continuous'],
        '12:30': ['exact_time', 'every_15_min', 'continuous'],
        '9:00': ['every_hour', 'every_15_min', 'continuous'],  # NOT with_condition
    }

    all_correct = True
    for t, expected_names in expected.items():
        actual_names = sorted(by_time.get(t, []))
        expected_sorted = sorted(expected_names)

        if actual_names == expected_sorted:
            print(f"[OK] {t}: {len(actual_names)} actions executed as expected")
        else:
            print(f"[FAIL] {t}:")
            print(f"  Expected: {expected_sorted}")
            print(f"  Actual: {actual_names}")
            all_correct = False

    if all_correct:
        print("\n[SUCCESS] All triggers executed correctly!")
    else:
        print("\n[FAILURE] Some triggers did not execute as expected")

    return all_correct


def test_event_trigger_execution():
    """Test that EVENT triggers actually execute scripts"""
    print("\n" + "="*80)
    print("TEST: EVENT Trigger Execution")
    print("="*80)

    # Track execution
    executions = []

    def track_event(name):
        """Return a script that tracks event execution"""
        def script(model):
            executions.append({
                'name': name,
                'timestamp': time.time()
            })
            print(f"  [EXECUTED] {name}")
        return script

    pr = PyRocrail("localhost", 8051)

    # Add event triggers
    actions = [
        Action(track_event("fb1_exact"), Trigger.EVENT, "fb1", "", 60),
        Action(track_event("fb_wildcard"), Trigger.EVENT, "fb*", "", 60),
        Action(track_event("fb1_with_condition"), Trigger.EVENT, "fb1", "obj_type == 'fb'", 60),
        Action(track_event("any_object"), Trigger.EVENT, None, "", 60),
    ]

    for action in actions:
        pr.add(action)

    print(f"\nAdded {len(actions)} event-based actions")
    print(f"Actions in _event_actions: {len(pr._event_actions)}")

    # Simulate object changes
    print("\n" + "-"*80)
    print("Simulating object state changes...")
    print("-"*80)

    # Mock object
    class MockFeedback:
        def __init__(self, id, state):
            self.id = id
            self.state = state

    test_events = [
        ('fb', 'fb1', MockFeedback('fb1', True)),
        ('fb', 'fb2', MockFeedback('fb2', True)),
        ('lc', 'lc1', type('obj', (), {'id': 'lc1', 'V': 50})()),
    ]

    for obj_type, obj_id, obj in test_events:
        print(f"\nEvent: {obj_type}/{obj_id}")

        # Execute event triggers
        pr._exec_event(obj_type, obj_id, obj)

        time.sleep(0.1)

    print("\n" + "="*80)
    print(f"RESULTS: {len(executions)} event executions recorded")
    print("="*80)

    for i, exec_info in enumerate(executions, 1):
        print(f"{i}. {exec_info['name']}")

    # Verify
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)

    # Expected: fb1 event should trigger 4 actions (fb1_exact, fb_wildcard, fb1_with_condition, any_object)
    # fb2 event should trigger 2 actions (fb_wildcard, any_object)
    # lc1 event should trigger 1 action (any_object)

    names = [e['name'] for e in executions]

    checks = [
        ('fb1_exact', 1, "fb1_exact should be called once for fb1"),
        ('fb_wildcard', 2, "fb_wildcard should be called for fb1 and fb2"),
        ('fb1_with_condition', 1, "fb1_with_condition should be called once for fb1"),
        ('any_object', 3, "any_object should be called for all 3 events"),
    ]

    all_correct = True
    for name, expected_count, description in checks:
        actual_count = names.count(name)
        if actual_count == expected_count:
            print(f"[OK] {description}")
        else:
            print(f"[FAIL] {description}")
            print(f"  Expected: {expected_count}, Actual: {actual_count}")
            all_correct = False

    if all_correct:
        print("\n[SUCCESS] All event triggers executed correctly!")
    else:
        print("\n[FAILURE] Some event triggers did not execute as expected")

    return all_correct


def test_duplicate_prevention():
    """Test that actions don't execute multiple times in same minute"""
    print("\n" + "="*80)
    print("TEST: Duplicate Execution Prevention")
    print("="*80)

    executions = []

    def track(model):
        executions.append(time.time())
        print(f"  [EXECUTED] at {model.clock.hour}:{model.clock.minute:02d}")

    pr = PyRocrail("localhost", 8051)
    pr.add(Action(track, Trigger.TIME, "12:30", "", 60))

    print("\nSimulating multiple clock updates at same time...")

    # Set clock to 12:30
    pr.model.clock.hour = 12
    pr.model.clock.minute = 30

    # Call _exec_time multiple times
    print("\n1st call at 12:30:")
    pr._exec_time()
    time.sleep(0.1)

    print("2nd call at 12:30 (should NOT execute):")
    pr._exec_time()
    time.sleep(0.2)

    print("3rd call at 12:30 (should NOT execute):")
    pr._exec_time()
    time.sleep(0.2)

    # Change time
    pr.model.clock.minute = 31
    print("\n4th call at 12:31 (should NOT execute - wrong time):")
    pr._exec_time()
    time.sleep(0.2)

    # Change to different time
    pr.model.clock.hour = 13
    pr.model.clock.minute = 30

    # This should NOT execute (wrong time pattern - action is for 12:30 exactly)
    print("\n5th call at 13:30 (should NOT execute - not 12:30):")
    pr._exec_time()
    time.sleep(0.2)

    print("\n" + "="*80)
    print(f"RESULTS: {len(executions)} executions")
    print("="*80)

    print("\nNote: The duplicate prevention works by tracking (hour, minute) combinations.")
    print("Once a trigger executes at 12:30, it won't execute again at 12:30 in the")
    print("same session. This prevents duplicate executions from multiple clock updates")
    print("at the same time. For daily repeating triggers, use patterns like '*:30' instead.")

    if len(executions) == 1:
        print("\n[OK] Executed exactly 1 time (prevented 2 duplicates)")
        return True
    else:
        print(f"\n[FAIL] Expected 1 execution, got {len(executions)}")
        return False


def main():
    """Run all execution tests"""
    results = []

    results.append(test_time_trigger_execution())
    results.append(test_event_trigger_execution())
    results.append(test_duplicate_prevention())

    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    passed = sum(results)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")

    if all(results):
        print("\n[SUCCESS] All execution tests passed!")
        print("\nThe trigger system is working correctly:")
        print("  - TIME triggers execute on clock updates")
        print("  - Pattern matching works (exact, wildcards, intervals)")
        print("  - Conditions are evaluated correctly")
        print("  - EVENT triggers execute on object changes")
        print("  - Duplicate executions are prevented")
    else:
        print("\n[FAILURE] Some tests failed")

    print()


if __name__ == "__main__":
    main()
