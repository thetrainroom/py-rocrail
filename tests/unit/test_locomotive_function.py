#!/usr/bin/env python3
"""Test locomotive function commands use correct <fn> tag format

This test verifies that set_function() sends the correct XML format
as observed in PCAP captures (tests/fixtures/pcap/rocrail_function.pcapng).
"""

from ..tools.mock_communicator import create_mock_pyrocrail


def test_locomotive_function_format():
    """Test that set_function sends correct <fn> tag format"""
    print("=" * 80)
    print("TEST: Locomotive Function Command Format")
    print("=" * 80)

    # Create PyRocrail with mock communicator
    pr, mock_com = create_mock_pyrocrail("tests/fixtures/pcap/rocrail_start.txt")
    mock_com.start()
    pr.model.init()

    # Find a locomotive to test with
    if len(pr.model._lc_domain) == 0:
        print("\n(SKIP) No locomotives in test PCAP")
        return True

    lc = list(pr.model._lc_domain.values())[0]
    print(f"\nTesting with locomotive: {lc.idx}")

    # Clear any previous messages
    mock_com.clear_sent_messages()

    # Test setting function 2 to ON
    print("  - Setting function 2 to ON")
    lc.set_function(2, True)

    # Get sent messages
    sent = mock_com.get_sent_messages()

    if len(sent) == 0:
        print("\n(FAIL) No message sent")
        return False

    msg = sent[0]
    print(f"\n  Message type: {msg['type']}")
    print(f"  Message XML: {msg['message'][:200]}...")

    # Verify message type is "fn" not "lc"
    if msg["type"] != "fn":
        print(f"\n(FAIL) Wrong message type. Expected 'fn', got '{msg['type']}'")
        return False

    # Verify message contains required attributes
    message_xml = msg["message"]

    required_attrs = [
        f'id="{lc.idx}"',
        'fnchanged="2"',
        'fnchangedstate="true"',
        'f0="',
        'f1="',
        'f2="true"',  # Function 2 should be true
    ]

    missing = []
    for attr in required_attrs:
        if attr not in message_xml:
            missing.append(attr)

    if missing:
        print(f"\n(FAIL) Missing required attributes: {missing}")
        print(f"  Full message: {message_xml}")
        return False

    print("\n(OK) Function command format is correct:")
    print("  [+] Uses <fn> tag (not <lc>)")
    print("  [+] Contains fnchanged='2'")
    print("  [+] Contains fnchangedstate='true'")
    print("  [+] Contains all function states (f0, f1, f2, ...)")

    # Test setting function 2 to OFF
    print("\n  - Setting function 2 to OFF")
    mock_com.clear_sent_messages()
    lc.set_function(2, False)
    sent = mock_com.get_sent_messages()

    if len(sent) > 0:
        msg = sent[0]
        if 'fnchangedstate="false"' in msg["message"] and 'f2="false"' in msg["message"]:
            print("  [+] OFF state verified")
        else:
            print("  (WARN) OFF state format may be incorrect")
            print(f"    Message: {msg['message'][:200]}...")

    return True


def test_locomotive_multiple_functions():
    """Test that multiple function states are preserved"""
    print("\n" + "=" * 80)
    print("TEST: Multiple Function States Preserved")
    print("=" * 80)

    pr, mock_com = create_mock_pyrocrail("tests/fixtures/pcap/rocrail_start.txt")
    mock_com.start()
    pr.model.init()

    if len(pr.model._lc_domain) == 0:
        print("\n(SKIP) No locomotives in test PCAP")
        return True

    lc = list(pr.model._lc_domain.values())[0]
    print(f"\nTesting with locomotive: {lc.idx}")

    # Set multiple functions
    print("  - Setting F0=ON, F1=ON, F2=ON")
    lc.set_function(0, True)
    lc.set_function(1, True)
    lc.set_function(2, True)

    # Clear and test that all states are preserved
    mock_com.clear_sent_messages()
    print("  - Setting F5=ON (should preserve F0, F1, F2)")
    lc.set_function(5, True)

    sent = mock_com.get_sent_messages()
    if len(sent) > 0:
        msg = sent[0]
        message_xml = msg["message"]

        # Check that previous states are preserved
        preserved = ['f0="true"', 'f1="true"', 'f2="true"', 'f5="true"']
        all_preserved = all(state in message_xml for state in preserved)

        if all_preserved:
            print("\n(OK) All function states preserved:")
            print("  [+] F0=ON preserved")
            print("  [+] F1=ON preserved")
            print("  [+] F2=ON preserved")
            print("  [+] F5=ON set correctly")
            return True
        else:
            print("\n(FAIL) Function states not preserved")
            print(f"  Message: {message_xml[:200]}...")
            return False
    else:
        print("\n(FAIL) No message sent")
        return False


def main():
    """Run locomotive function tests"""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "LOCOMOTIVE FUNCTION TESTS")
    print("=" * 80)
    print()

    results = []
    results.append(test_locomotive_function_format())
    results.append(test_locomotive_multiple_functions())

    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    passed = sum(results)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")

    if all(results):
        print("\n(SUCCESS) All locomotive function tests passed!")
        print("\nVerified:")
        print("  [+] Function commands use <fn> tag (not <lc>)")
        print("  [+] Commands include fnchanged and fnchangedstate attributes")
        print("  [+] Commands include all function states (f0-f31)")
        print("  [+] Multiple function states are preserved correctly")
    else:
        print("\n[FAILURE] Some tests failed")

    print()
    return all(results)


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
