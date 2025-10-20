#!/usr/bin/env python3
"""Test exception handling"""

import xml.etree.ElementTree as ET
from pyrocrail.pyrocrail import PyRocrail
from ..tools.mock_communicator import MockCommunicator
import sys
from io import StringIO


def test_exception_handling():
    """Test that exceptions are properly logged"""
    print("=" * 80)
    print("TEST: Exception Handling")
    print("=" * 80)

    # Create PyRocrail with mock communicator
    pr = PyRocrail("localhost", 8051)
    mock_com = MockCommunicator()
    pr.com = mock_com
    pr.model.communicator = mock_com

    print("\nTesting exception message handling:")
    passed = 0
    failed = 0

    # Test various exception types
    exception_tests = [
        (
            "exception with all attributes",
            '<exception level="exception" code="E001" id="loco1" text="Short circuit detected"/>',
            ["Rocrail EXCEPTION", "[E001]", "(object: loco1)", "Short circuit detected"],
        ),
        (
            "warning message",
            '<exception level="warning" code="W002" text="Track speed limit exceeded"/>',
            ["Rocrail WARNING", "[W002]", "Track speed limit exceeded"],
        ),
        (
            "info message",
            '<exception level="info" text="System initialized successfully"/>',
            ["Rocrail INFO", "System initialized successfully"],
        ),
        (
            "exception without code",
            '<exception level="exception" text="Communication timeout"/>',
            ["Rocrail EXCEPTION", "Communication timeout"],
        ),
        (
            "minimal exception",
            '<exception text="Unknown error"/>',
            ["Rocrail UNKNOWN", "Unknown error"],
        ),
    ]

    for name, xml_str, expected_parts in exception_tests:
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # Process exception
        root = ET.fromstring(f"<root>{xml_str}</root>")
        pr.model.decode(root)

        # Restore stdout
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue().strip()

        # Check if all expected parts are in output
        all_found = all(part in output for part in expected_parts)

        if all_found:
            print(f"  (OK) {name:35s} -> {output}")
            passed += 1
        else:
            print(f"  (FAIL) {name:35s}")
            print(f"       Expected parts: {expected_parts}")
            print(f"       Got output:     {output}")
            failed += 1

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"\nTests passed: {passed}/{passed + failed}")

    if failed == 0:
        print("\n(SUCCESS) Exception handling works correctly!")
        print("\nException messages are automatically logged when received from server.")
        print("\nException types:")
        print("  - level='exception': Critical errors (short circuits, hardware failures)")
        print("  - level='warning':   Non-critical warnings (speed limits, state changes)")
        print("  - level='info':      Informational messages (system status)")
        print("\nExample output:")
        print("  Rocrail EXCEPTION [E001] (object: loco1) : Short circuit detected")
        print("  Rocrail WARNING [W002] : Track speed limit exceeded")
        print("  Rocrail INFO : System initialized successfully")
        return True
    else:
        print(f"\n(FAILURE) {failed} tests failed")
        return False


if __name__ == "__main__":
    test_exception_handling()
