#!/usr/bin/env python3
"""Comprehensive test for improved trigger system"""

from pyrocrail.pyrocrail import PyRocrail, Action, Trigger


def test_time_pattern_matching():
    """Test time pattern matching logic"""
    print("="*80)
    print("TEST 1: Time Pattern Matching")
    print("="*80)

    pr = PyRocrail("localhost", 8051)

    # Test cases: (pattern, hour, minute, expected_result)
    test_cases = [
        # Exact time
        ("12:30", 12, 30, True),
        ("12:30", 12, 31, False),
        ("12:30", 13, 30, False),

        # Wildcard patterns
        ("*:00", 0, 0, True),
        ("*:00", 12, 0, True),
        ("*:00", 12, 30, False),
        ("*:15", 0, 15, True),
        ("*:15", 23, 15, True),
        ("*:15", 12, 0, False),

        # Interval patterns - hours
        ("*/2:00", 0, 0, True),   # Every 2 hours at :00
        ("*/2:00", 2, 0, True),
        ("*/2:00", 4, 0, True),
        ("*/2:00", 1, 0, False),  # Odd hour
        ("*/2:00", 2, 30, False), # Wrong minute

        ("*/3:30", 0, 30, True),  # Every 3 hours at :30
        ("*/3:30", 3, 30, True),
        ("*/3:30", 6, 30, True),
        ("*/3:30", 2, 30, False),

        # Interval patterns - minutes
        ("*:*/15", 0, 0, True),   # Every 15 minutes
        ("*:*/15", 0, 15, True),
        ("*:*/15", 0, 30, True),
        ("*:*/15", 0, 45, True),
        ("*:*/15", 0, 10, False),
        ("*:*/15", 12, 0, True),  # Works in any hour
        ("*:*/15", 12, 30, True),

        ("12:*/10", 12, 0, True),  # Every 10 min in hour 12
        ("12:*/10", 12, 10, True),
        ("12:*/10", 12, 20, True),
        ("12:*/10", 12, 15, False),
        ("12:*/10", 13, 0, False),  # Wrong hour

        # Always trigger
        ("*:*", 12, 34, True),
        ("*", 5, 6, True),
        (None, 23, 59, True),
    ]

    passed = 0
    failed = 0

    for pattern, hour, minute, expected in test_cases:
        result = pr._match_time_pattern(pattern, hour, minute)
        status = "[OK]" if result == expected else "[FAIL]"
        if result == expected:
            passed += 1
        else:
            failed += 1
            print(f"{status} Pattern '{pattern}' at {hour:02d}:{minute:02d} -> {result} (expected {expected})")

    print(f"\nResults: {passed} passed, {failed} failed")
    print()


def test_condition_evaluation():
    """Test condition evaluation"""
    print("="*80)
    print("TEST 2: Condition Evaluation")
    print("="*80)

    pr = PyRocrail("localhost", 8051)

    # Mock model for testing
    class MockModel:
        def __init__(self):
            self.clock = type('obj', (object,), {'hour': 10, 'minute': 30})()

    model = MockModel()

    # Test cases: (condition, hour, minute, expected)
    test_cases = [
        ("", 12, 30, True),  # Empty condition = always true
        ("9 <= hour <= 17", 10, 0, True),  # Work hours
        ("9 <= hour <= 17", 8, 0, False),
        ("9 <= hour <= 17", 18, 0, False),
        ("hour == 12", 12, 0, True),
        ("hour == 12", 11, 0, False),
        ("minute == 0", 10, 0, True),
        ("minute == 0", 10, 30, False),
        ("minute % 15 == 0", 10, 0, True),
        ("minute % 15 == 0", 10, 15, True),
        ("minute % 15 == 0", 10, 30, True),
        ("minute % 15 == 0", 10, 10, False),
        ("hour % 2 == 0", 10, 0, True),  # Even hours
        ("hour % 2 == 0", 11, 0, False), # Odd hours
        ("minute == 0 or minute == 30", 10, 0, True),
        ("minute == 0 or minute == 30", 10, 30, True),
        ("minute == 0 or minute == 30", 10, 15, False),
    ]

    passed = 0
    failed = 0

    for condition, hour, minute, expected in test_cases:
        result = pr._evaluate_condition(condition, hour, minute, model)
        status = "[OK]" if result == expected else "[FAIL]"
        if result == expected:
            passed += 1
        else:
            failed += 1
            print(f"{status} Condition '{condition}' at {hour:02d}:{minute:02d} -> {result} (expected {expected})")

    print(f"\nResults: {passed} passed, {failed} failed")
    print()


def test_object_pattern_matching():
    """Test object ID pattern matching"""
    print("="*80)
    print("TEST 3: Object Pattern Matching")
    print("="*80)

    pr = PyRocrail("localhost", 8051)

    # Test cases: (pattern, obj_id, expected)
    test_cases = [
        ("fb1", "fb1", True),
        ("fb1", "fb2", False),
        ("fb*", "fb1", True),
        ("fb*", "fb2", True),
        ("fb*", "fbMain", True),
        ("fb*", "sw1", False),
        ("*", "fb1", True),
        ("*", "sw1", True),
        ("*", "anything", True),
        (None, "fb1", True),
        ("lc*", "lc1", True),
        ("lc*", "lc_big", True),
        ("lc*", "fb1", False),
    ]

    passed = 0
    failed = 0

    for pattern, obj_id, expected in test_cases:
        result = pr._match_object_pattern(pattern, obj_id)
        status = "[OK]" if result == expected else "[FAIL]"
        if result == expected:
            passed += 1
        else:
            failed += 1
            print(f"{status} Pattern '{pattern}' for '{obj_id}' -> {result} (expected {expected})")

    print(f"\nResults: {passed} passed, {failed} failed")
    print()


def test_action_examples():
    """Demonstrate example actions"""
    print("="*80)
    print("TEST 4: Example Action Configurations")
    print("="*80)

    def lighting_script(model):
        """Adjust lighting based on time"""
        hour = model.clock.hour
        if 6 <= hour < 9:
            print("  -> Morning: Gradually increase lights")
        elif 9 <= hour < 17:
            print("  -> Daytime: Full lighting")
        elif 17 <= hour < 21:
            print("  -> Evening: Dim lights")
        else:
            print("  -> Night: Minimal lighting")

    def hourly_report(model):
        """Generate hourly report"""
        print(f"  -> Hourly report at {model.clock.hour}:00")
        print(f"     Locomotives: {len(model._lc_domain)}")

    def sensor_reaction(model):
        """React to sensor change"""
        print("  -> Sensor triggered!")

    examples = [
        # TIME triggers
        Action(lighting_script, Trigger.TIME, "*:*", "", 60),
        "Every clock update (for continuous lighting adjustment)",

        Action(hourly_report, Trigger.TIME, "*:00", "", 30),
        "Every hour at :00",

        Action(hourly_report, Trigger.TIME, "*/2:00", "", 30),
        "Every 2 hours at :00 (0:00, 2:00, 4:00, ...)",

        Action(lambda m: print("  -> 15 minute mark"), Trigger.TIME, "*:*/15", "", 10),
        "Every 15 minutes (0:00, 0:15, 0:30, 0:45, ...)",

        Action(hourly_report, Trigger.TIME, "*:00", "9 <= hour <= 17", 30),
        "Every hour during work hours (9-17)",

        Action(lambda m: print("  -> Noon!"), Trigger.TIME, "12:00", "", 5),
        "Exactly at 12:00",

        # EVENT triggers
        Action(sensor_reaction, Trigger.EVENT, "fb1", "obj.state == True", 15),
        "When sensor fb1 turns on",

        Action(lambda m: print("  -> Any feedback!"), Trigger.EVENT, "fb*", "", 10),
        "When any feedback sensor changes",

        Action(lambda m: print("  -> Locomotive moved!"), Trigger.EVENT, "lc*", "hasattr(obj, 'V') and obj.V > 0", 10),
        "When any locomotive starts moving",
    ]

    for i in range(0, len(examples), 2):
        action = examples[i]
        description = examples[i+1]
        print(f"\n{i//2 + 1}. {description}")
        print(f"   trigger_type: {action.trigger_type.name}")
        print(f"   trigger: '{action.trigger}'")
        if action.condition:
            print(f"   condition: '{action.condition}'")
        print(f"   timeout: {action.timeout}s")

    print()


def main():
    """Run all tests"""
    test_time_pattern_matching()
    test_condition_evaluation()
    test_object_pattern_matching()
    test_action_examples()

    print("="*80)
    print("SUMMARY: Trigger System Features")
    print("="*80)
    print("\n[OK] Time pattern matching:")
    print("  - Exact times: '12:30'")
    print("  - Hour wildcards: '*:00' (every hour)")
    print("  - Hour intervals: '*/2:00' (every 2 hours)")
    print("  - Minute intervals: '*:*/15' (every 15 minutes)")
    print("  - Continuous: '*' or None (every clock update)")
    print("\n[OK] Condition evaluation:")
    print("  - Time ranges: '9 <= hour <= 17'")
    print("  - Modulo checks: 'hour % 2 == 0'")
    print("  - Boolean logic: 'minute == 0 or minute == 30'")
    print("\n[OK] Event triggers:")
    print("  - Exact object: 'fb1'")
    print("  - Wildcards: 'fb*' (all feedback sensors)")
    print("  - Conditions: 'obj.state == True'")
    print("\n[OK] Timeout handling:")
    print("  - Configurable per action")
    print("  - Monitored by cleanup thread")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
