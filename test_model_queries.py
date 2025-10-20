#!/usr/bin/env python3
"""Test model query commands"""

import xml.etree.ElementTree as ET
from pyrocrail.pyrocrail import PyRocrail
from tests.tools.mock_communicator import MockCommunicator


def test_model_queries():
    """Test that model query commands generate correct XML"""
    print("=" * 80)
    print("TEST: Model Query Commands")
    print("=" * 80)

    # Create PyRocrail with mock communicator
    pr = PyRocrail("localhost", 8051)
    mock_com = MockCommunicator()
    pr.com = mock_com
    pr.model.communicator = mock_com

    print("\nTesting model query commands:")
    passed = 0
    failed = 0

    # Test request list commands
    list_tests = [
        ("request_locomotive_list", lambda: pr.model.request_locomotive_list(), "model", '<model cmd="lclist"/>'),
        ("request_switch_list", lambda: pr.model.request_switch_list(), "model", '<model cmd="swlist"/>'),
        ("request_feedback_list", lambda: pr.model.request_feedback_list(), "model", '<model cmd="fblist"/>'),
    ]

    for name, cmd_func, expected_type, expected_msg in list_tests:
        mock_com.clear_sent_messages()
        cmd_func()

        sent = mock_com.get_sent_messages()
        if len(sent) == 1:
            msg = sent[0]
            if msg["type"] == expected_type and msg["message"] == expected_msg:
                print(f"  (OK) {name:30s} -> {msg['message']}")
                passed += 1
            else:
                print(f"  (FAIL) {name:30s}")
                print(f"       Expected: {expected_msg}")
                print(f"       Got:      {msg['message']}")
                failed += 1
        else:
            print(f"  (FAIL) {name:30s} -> Expected 1 message, got {len(sent)}")
            failed += 1

    # Test locomotive properties query
    print("\n" + "=" * 80)
    print("Locomotive Properties Query")
    print("=" * 80)

    mock_com.clear_sent_messages()
    pr.model.request_locomotive_properties("my_loco")

    sent = mock_com.get_sent_messages()
    if len(sent) == 1:
        msg = sent[0]
        expected = '<model cmd="lcprops" val="my_loco"/>'
        if msg["type"] == "model" and msg["message"] == expected:
            print(f"  (OK) request_locomotive_properties -> {msg['message']}")
            passed += 1
        else:
            print(f"  (FAIL) request_locomotive_properties")
            print(f"       Expected: {expected}")
            print(f"       Got:      {msg['message']}")
            failed += 1
    else:
        print(f"  (FAIL) request_locomotive_properties -> Expected 1 message, got {len(sent)}")
        failed += 1

    # Test add object
    print("\n" + "=" * 80)
    print("Dynamic Object Management")
    print("=" * 80)

    mock_com.clear_sent_messages()
    lc_xml = ET.fromstring('<lc id="new_loco" addr="3" V="0"/>')
    pr.model.add_object("lc", lc_xml)

    sent = mock_com.get_sent_messages()
    if len(sent) == 1:
        msg = sent[0]
        if msg["type"] == "model" and '<model cmd="add">' in msg["message"] and 'id="new_loco"' in msg["message"]:
            print(f"  (OK) add_object                 -> {msg['message']}")
            passed += 1
        else:
            print(f"  (FAIL) add_object")
            print(f"       Expected: <model cmd=\"add\"> with new_loco")
            print(f"       Got:      {msg['message']}")
            failed += 1
    else:
        print(f"  (FAIL) add_object -> Expected 1 message, got {len(sent)}")
        failed += 1

    # Test remove object
    mock_com.clear_sent_messages()
    pr.model.remove_object("lc", "old_loco")

    sent = mock_com.get_sent_messages()
    if len(sent) == 1:
        msg = sent[0]
        expected = '<model cmd="remove"><lc id="old_loco"/></model>'
        if msg["type"] == "model" and msg["message"] == expected:
            print(f"  (OK) remove_object              -> {msg['message']}")
            passed += 1
        else:
            print(f"  (FAIL) remove_object")
            print(f"       Expected: {expected}")
            print(f"       Got:      {msg['message']}")
            failed += 1
    else:
        print(f"  (FAIL) remove_object -> Expected 1 message, got {len(sent)}")
        failed += 1

    # Test modify object
    mock_com.clear_sent_messages()
    pr.model.modify_object("lc", "my_loco", V_max="120", mass="100")

    sent = mock_com.get_sent_messages()
    if len(sent) == 1:
        msg = sent[0]
        if (
            msg["type"] == "model"
            and '<model cmd="modify">' in msg["message"]
            and 'id="my_loco"' in msg["message"]
            and 'V_max="120"' in msg["message"]
            and 'mass="100"' in msg["message"]
        ):
            print(f"  (OK) modify_object              -> {msg['message']}")
            passed += 1
        else:
            print(f"  (FAIL) modify_object")
            print(f"       Expected: <model cmd=\"modify\"> with my_loco, V_max, mass")
            print(f"       Got:      {msg['message']}")
            failed += 1
    else:
        print(f"  (FAIL) modify_object -> Expected 1 message, got {len(sent)}")
        failed += 1

    # Test merge plan
    mock_com.clear_sent_messages()
    plan_xml = ET.fromstring('<plan title="Test"/>')
    pr.model.merge_plan(plan_xml)

    sent = mock_com.get_sent_messages()
    if len(sent) == 1:
        msg = sent[0]
        if msg["type"] == "model" and '<model cmd="merge">' in msg["message"] and '<plan title="Test"' in msg["message"]:
            print(f"  (OK) merge_plan                 -> {msg['message']}")
            passed += 1
        else:
            print(f"  (FAIL) merge_plan")
            print(f"       Expected: <model cmd=\"merge\"> with plan")
            print(f"       Got:      {msg['message']}")
            failed += 1
    else:
        print(f"  (FAIL) merge_plan -> Expected 1 message, got {len(sent)}")
        failed += 1

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"\nTests passed: {passed}/{passed + failed}")

    if failed == 0:
        print("\n(SUCCESS) All model query commands work correctly!")
        print("\nAvailable model query commands:")
        print("  List queries:")
        print("    model.request_locomotive_list()")
        print("    model.request_switch_list()")
        print("    model.request_feedback_list()")
        print("\n  Object queries:")
        print("    model.request_locomotive_properties(loco_id)")
        print("\n  Dynamic management:")
        print("    model.add_object(obj_type, xml_element)")
        print("    model.remove_object(obj_type, obj_id)")
        print("    model.modify_object(obj_type, obj_id, **attributes)")
        print("\n  Plan updates:")
        print("    model.merge_plan(plan_xml)")
        print("\nUsage example:")
        print("  # Add a new locomotive")
        print("  lc_xml = ET.fromstring('<lc id=\"new_loco\" addr=\"3\"/>')")
        print("  pr.model.add_object('lc', lc_xml)")
        print("\n  # Modify locomotive properties")
        print("  pr.model.modify_object('lc', 'my_loco', V_max='120', mass='100')")
        print("\n  # Remove a locomotive")
        print("  pr.model.remove_object('lc', 'old_loco')")
        return True
    else:
        print(f"\n(FAILURE) {failed} tests failed")
        return False


if __name__ == "__main__":
    test_model_queries()
