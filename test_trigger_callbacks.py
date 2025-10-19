#!/usr/bin/env python3
"""Test action success/error callbacks"""

import time
from pyrocrail.pyrocrail import PyRocrail, Action, Trigger


def test_success_callback():
    """Test that success callback is called when action completes"""
    print("="*80)
    print("TEST: Success Callback")
    print("="*80)

    pr = PyRocrail("localhost", 8051)

    # Start cleanup thread manually (without connecting to server)
    import threading
    pr.__clean_thread = threading.Thread(target=pr._PyRocrail__clean)
    pr.__clean_thread.start()

    # Track callback invocations
    results = []

    def my_action(model):
        """Action that returns a value"""
        print("  [ACTION] Running...")
        time.sleep(0.2)  # Simulate work
        return "Task completed successfully!"

    def on_success(result, elapsed):
        """Called when action succeeds"""
        print(f"  [SUCCESS] Action completed in {elapsed:.2f}s")
        print(f"  [SUCCESS] Result: {result}")
        results.append(('success', result, elapsed))

    def on_error(exception, elapsed):
        """Called when action fails"""
        print(f"  [ERROR] Action failed after {elapsed:.2f}s: {exception}")
        results.append(('error', exception, elapsed))

    # Create action with callbacks
    action = Action(
        my_action,
        Trigger.TIME,
        "12:30",
        "",
        60,
        on_success=on_success,
        on_error=on_error
    )

    pr.add(action)

    # Trigger the action
    pr.model.clock.hour = 12
    pr.model.clock.minute = 30
    print("\nTriggering action...")
    pr._exec_time()

    # Wait for completion
    print("Waiting for action to complete...")
    time.sleep(0.5)

    # Stop cleanup thread
    pr.running = False
    pr.__clean_thread.join(timeout=1.0)

    print("\n" + "="*80)
    print(f"RESULTS: {len(results)} callbacks invoked")
    print("="*80)

    if len(results) == 1:
        callback_type, data, elapsed = results[0]
        if callback_type == 'success':
            print(f"[OK] Success callback invoked")
            print(f"  Result: {data}")
            print(f"  Time: {elapsed:.2f}s")
            return True
        else:
            print(f"[FAIL] Error callback invoked instead: {data}")
            return False
    else:
        print(f"[FAIL] Expected 1 callback, got {len(results)}")
        return False


def test_error_callback():
    """Test that error callback is called when action fails"""
    print("\n" + "="*80)
    print("TEST: Error Callback")
    print("="*80)

    pr = PyRocrail("localhost", 8051)

    # Start cleanup thread manually
    import threading
    pr.__clean_thread = threading.Thread(target=pr._PyRocrail__clean)
    pr.__clean_thread.start()

    results = []

    def failing_action(model):
        """Action that raises an exception"""
        print("  [ACTION] Running...")
        time.sleep(0.1)
        raise ValueError("Something went wrong!")

    def on_success(result, elapsed):
        results.append(('success', result, elapsed))

    def on_error(exception, elapsed):
        print(f"  [ERROR] Caught exception after {elapsed:.2f}s: {exception}")
        results.append(('error', exception, elapsed))

    action = Action(
        failing_action,
        Trigger.TIME,
        "12:30",
        "",
        60,
        on_success=on_success,
        on_error=on_error
    )

    pr.add(action)

    # Trigger the action
    pr.model.clock.hour = 12
    pr.model.clock.minute = 30
    print("\nTriggering failing action...")
    pr._exec_time()

    # Wait for completion
    print("Waiting for action to fail...")
    time.sleep(0.5)

    # Stop cleanup thread
    pr.running = False
    pr.__clean_thread.join(timeout=1.0)

    print("\n" + "="*80)
    print(f"RESULTS: {len(results)} callbacks invoked")
    print("="*80)

    if len(results) == 1:
        callback_type, data, elapsed = results[0]
        if callback_type == 'error':
            print(f"[OK] Error callback invoked")
            print(f"  Exception: {data}")
            print(f"  Time: {elapsed:.2f}s")
            return True
        else:
            print(f"[FAIL] Success callback invoked instead: {data}")
            return False
    else:
        print(f"[FAIL] Expected 1 callback, got {len(results)}")
        return False


def test_timeout_callback():
    """Test that error callback is called on timeout"""
    print("\n" + "="*80)
    print("TEST: Timeout Callback")
    print("="*80)

    pr = PyRocrail("localhost", 8051)

    # Start cleanup thread manually
    import threading
    pr.__clean_thread = threading.Thread(target=pr._PyRocrail__clean)
    pr.__clean_thread.start()

    results = []

    def slow_action(model):
        """Action that takes too long"""
        print("  [ACTION] Running slow task...")
        time.sleep(2.0)  # Will timeout
        return "Done"

    def on_success(result, elapsed):
        results.append(('success', result, elapsed))

    def on_error(exception, elapsed):
        print(f"  [TIMEOUT] Action timed out after {elapsed:.2f}s: {exception}")
        results.append(('timeout', exception, elapsed))

    action = Action(
        slow_action,
        Trigger.TIME,
        "12:30",
        "",
        timeout=0.5,  # Short timeout
        on_success=on_success,
        on_error=on_error
    )

    pr.add(action)

    # Trigger the action
    pr.model.clock.hour = 12
    pr.model.clock.minute = 30
    print("\nTriggering slow action with 0.5s timeout...")
    pr._exec_time()

    # Wait for timeout
    print("Waiting for timeout...")
    time.sleep(1.0)

    # Stop cleanup thread
    pr.running = False
    pr.__clean_thread.join(timeout=1.0)

    print("\n" + "="*80)
    print(f"RESULTS: {len(results)} callbacks invoked")
    print("="*80)

    if len(results) >= 1:
        callback_type, data, elapsed = results[0]
        if callback_type == 'timeout':
            print(f"[OK] Timeout error callback invoked")
            print(f"  Exception: {data}")
            print(f"  Time: {elapsed:.2f}s")
            return True
        else:
            print(f"[FAIL] Wrong callback type: {callback_type}")
            return False
    else:
        print(f"[FAIL] No callbacks invoked")
        return False


def test_execution_history():
    """Demonstrate tracking execution history"""
    print("\n" + "="*80)
    print("TEST: Execution History Tracking")
    print("="*80)

    pr = PyRocrail("localhost", 8051)

    # Start cleanup thread manually
    import threading
    pr.__clean_thread = threading.Thread(target=pr._PyRocrail__clean)
    pr.__clean_thread.start()

    # Track all executions
    execution_log = []

    def log_execution(action_name):
        """Create callbacks that log to history"""
        def on_success(result, elapsed):
            execution_log.append({
                'action': action_name,
                'status': 'success',
                'result': result,
                'elapsed': elapsed,
                'time': time.time()
            })

        def on_error(exception, elapsed):
            execution_log.append({
                'action': action_name,
                'status': 'error',
                'exception': str(exception),
                'elapsed': elapsed,
                'time': time.time()
            })

        return on_success, on_error

    # Add multiple actions with tracking
    actions = [
        ("lighting_control", lambda m: "Lights adjusted"),
        ("train_report", lambda m: f"Report: {len(m._lc_domain)} trains"),
        ("sensor_check", lambda m: "Sensors OK"),
    ]

    for name, script in actions:
        on_success, on_error = log_execution(name)
        action = Action(
            script,
            Trigger.TIME,
            "*:00",
            "",
            60,
            on_success=on_success,
            on_error=on_error
        )
        pr.add(action)

    # Trigger all actions
    pr.model.clock.hour = 12
    pr.model.clock.minute = 0
    print("\nTriggering all actions at 12:00...")
    pr._exec_time()

    # Wait for completion
    time.sleep(0.5)

    # Stop cleanup thread
    pr.running = False
    pr.__clean_thread.join(timeout=1.0)

    print("\n" + "="*80)
    print("EXECUTION LOG:")
    print("="*80)

    for i, entry in enumerate(execution_log, 1):
        print(f"\n{i}. Action: {entry['action']}")
        print(f"   Status: {entry['status']}")
        if entry['status'] == 'success':
            print(f"   Result: {entry['result']}")
        else:
            print(f"   Exception: {entry['exception']}")
        print(f"   Elapsed: {entry['elapsed']:.3f}s")

    if len(execution_log) == 3:
        print("\n[OK] All 3 actions logged correctly")
        return True
    else:
        print(f"\n[FAIL] Expected 3 log entries, got {len(execution_log)}")
        return False


def main():
    """Run all callback tests"""
    print("\n")
    print("="*80)
    print(" "*20 + "TRIGGER CALLBACK SYSTEM TESTS")
    print("="*80)
    print()

    results = []

    results.append(test_success_callback())
    results.append(test_error_callback())
    results.append(test_timeout_callback())
    results.append(test_execution_history())

    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    passed = sum(results)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")

    if all(results):
        print("\n[SUCCESS] All callback tests passed!")
        print("\nYou can now track action execution:")
        print("  - on_success(result, elapsed) - called when action completes")
        print("  - on_error(exception, elapsed) - called on failure or timeout")
        print("  - Build execution logs, metrics, alerts, etc.")
    else:
        print("\n[FAILURE] Some tests failed")

    print()


if __name__ == "__main__":
    main()
