#!/usr/bin/env python3
"""Test system commands"""

from pyrocrail.pyrocrail import PyRocrail
from tests.tools.mock_communicator import MockCommunicator


def test_system_commands():
    """Test that system commands generate correct XML"""
    print("=" * 80)
    print("TEST: System Commands")
    print("=" * 80)

    # Create PyRocrail with mock communicator
    pr = PyRocrail("localhost", 8051)
    mock_com = MockCommunicator()
    pr.com = mock_com

    # Test each system command
    commands_to_test = [
        ("power_on", lambda: pr.power_on(), "sys", '<sys cmd="go"/>'),
        ("power_off", lambda: pr.power_off(), "sys", '<sys cmd="stop"/>'),
        ("emergency_stop", lambda: pr.emergency_stop(), "sys", '<sys cmd="ebreak"/>'),
        ("reset", lambda: pr.reset(), "sys", '<sys cmd="reset"/>'),
        ("save", lambda: pr.save(), "sys", '<sys cmd="save"/>'),
        ("shutdown", lambda: pr.shutdown(), "sys", '<sys cmd="shutdown"/>'),
        ("query", lambda: pr.query(), "sys", '<sys cmd="query"/>'),
        ("start_of_day", lambda: pr.start_of_day(), "sys", '<sys cmd="sod"/>'),
        ("end_of_day", lambda: pr.end_of_day(), "sys", '<sys cmd="eod"/>'),
        ("update_ini", lambda: pr.update_ini(), "sys", '<sys cmd="updateini"/>'),
        ("auto_on", lambda: pr.auto_on(), "auto", '<auto cmd="on"/>'),
        ("auto_off", lambda: pr.auto_off(), "auto", '<auto cmd="off"/>'),
        ("request_locomotive_list", lambda: pr.request_locomotive_list(), "sys", '<sys cmd="locliste"/>'),
    ]

    print("\nTesting system commands:")
    passed = 0
    failed = 0

    for name, cmd_func, expected_type, expected_msg in commands_to_test:
        mock_com.clear_sent_messages()
        cmd_func()

        sent = mock_com.get_sent_messages()
        if len(sent) == 1:
            msg = sent[0]
            if msg["type"] == expected_type and msg["message"] == expected_msg:
                print(f"  (OK) {name:25s} -> {msg['message']}")
                passed += 1
            else:
                print(f"  (FAIL) {name:25s} -> Expected: {expected_msg}, Got: {msg['message']}")
                failed += 1
        else:
            print(f"  (FAIL) {name:25s} -> Expected 1 message, got {len(sent)}")
            failed += 1

    print("\n" + "=" * 80)
    print("Clock Commands")
    print("=" * 80)

    # Test clock commands
    clock_tests = [
        ("set time", lambda: pr.set_clock(hour=12, minute=30), "clock", '<clock hour="12" minute="30"/>'),
        ("set divider", lambda: pr.set_clock(divider=10), "clock", '<clock divider="10"/>'),
        ("freeze clock", lambda: pr.set_clock(freeze=True), "clock", '<clock freeze="true"/>'),
        ("resume clock", lambda: pr.set_clock(freeze=False), "clock", '<clock freeze="false"/>'),
        (
            "set all",
            lambda: pr.set_clock(hour=14, minute=45, divider=5, freeze=False),
            "clock",
            '<clock hour="14" minute="45" divider="5" freeze="false"/>',
        ),
    ]

    for name, cmd_func, expected_type, expected_msg in clock_tests:
        mock_com.clear_sent_messages()
        cmd_func()

        sent = mock_com.get_sent_messages()
        if len(sent) == 1:
            msg = sent[0]
            if msg["type"] == expected_type and msg["message"] == expected_msg:
                print(f"  (OK) {name:25s} -> {msg['message']}")
                passed += 1
            else:
                print(f"  (FAIL) {name:25s}")
                print(f"       Expected: {expected_msg}")
                print(f"       Got:      {msg['message']}")
                failed += 1
        else:
            print(f"  (FAIL) {name:25s} -> Expected 1 message, got {len(sent)}")
            failed += 1

    print("\n" + "=" * 80)
    print("Event Commands")
    print("=" * 80)

    # Test event command
    mock_com.clear_sent_messages()
    pr.fire_event("test_event", state="active", value="123")

    sent = mock_com.get_sent_messages()
    if len(sent) == 1:
        msg = sent[0]
        if msg["type"] == "event" and 'id="test_event"' in msg["message"] and 'state="active"' in msg["message"] and 'value="123"' in msg["message"]:
            print(f"  (OK) fire_event              -> {msg['message']}")
            passed += 1
        else:
            print("  (FAIL) fire_event")
            print("       Expected: event with id, state, value")
            print(f"       Got:      {msg['message']}")
            failed += 1
    else:
        print(f"  (FAIL) fire_event -> Expected 1 message, got {len(sent)}")
        failed += 1

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"\nTests passed: {passed}/{passed + failed}")

    if failed == 0:
        print("\n(SUCCESS) All system commands work correctly!")
        print("\nAvailable system commands:")
        print("  Power:     power_on(), power_off(), emergency_stop()")
        print("  System:    reset(), save(), shutdown(), query()")
        print("  Auto:      auto_on(), auto_off()")
        print("  Session:   start_of_day(), end_of_day()")
        print("  Config:    update_ini()")
        print("  Clock:     set_clock(hour, minute, divider, freeze)")
        print("  Events:    fire_event(event_id, **kwargs)")
        print("  Query:     request_locomotive_list()")
        return True
    else:
        print(f"\n(FAILURE) {failed} tests failed")
        return False


if __name__ == "__main__":
    test_system_commands()
