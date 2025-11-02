#!/usr/bin/env python3
"""Integration tests for PyRocrail against Docker Rocrail server

These tests require the Docker Rocrail server to be running:
    cd docker && docker-compose up -d

Run tests with:
    pytest tests/integration/test_docker_rocrail.py -v
"""

import pytest
import time
from pyrocrail.pyrocrail import PyRocrail


@pytest.fixture(scope="module")
def rocrail_server():
    """Connect to Docker Rocrail server

    Assumes the Docker container is running on localhost:8051
    """
    pr = PyRocrail("localhost", 8051)
    pr.start()

    # Wait for model to fully load
    time.sleep(2)

    yield pr

    # Cleanup
    pr.power_off()
    pr.stop()


def test_connection(rocrail_server):
    """Test basic connection to Rocrail server"""
    pr = rocrail_server
    assert pr.model.plan_recv is True, "Model plan should be received"
    assert pr.com is not None, "Communicator should be initialized"


def test_model_objects_loaded(rocrail_server):
    """Test that all example plan objects are loaded"""
    pr = rocrail_server

    # Check locomotives
    assert "Loc1" in pr.model._lc_domain, "Locomotive 'Loc1' should be loaded"
    loco = pr.model.get_lc("Loc1")
    assert loco.idx == "Loc1"

    # Check feedback sensors
    assert "fb1" in pr.model._fb_domain, "Feedback 'fb1' should be loaded"
    fb = pr.model.get_fb("fb1")
    assert fb.idx == "fb1"

    # Check switches
    assert "sw1" in pr.model._sw_domain, "Switch 'sw1' should be loaded"
    sw = pr.model.get_sw("sw1")
    assert sw.idx == "sw1"

    # Check signals
    assert "sg1" in pr.model._sg_domain, "Signal 'sg1' should be loaded"
    sg = pr.model.get_sg("sg1")
    assert sg.idx == "sg1"

    # Check blocks
    assert "bk1" in pr.model._bk_domain, "Block 'bk1' should be loaded"
    bk = pr.model.get_bk("bk1")
    assert bk.idx == "bk1"

    # Check stage blocks
    assert "sb1" in pr.model._sb_domain, "Stage block 'sb1' should be loaded"
    sb = pr.model.get_stage("sb1")
    assert sb.idx == "sb1"

    # Check outputs
    assert "co1" in pr.model._co_domain, "Output 'co1' should be loaded"
    co = pr.model.get_co("co1")
    assert co.idx == "co1"

    # Check cars
    assert "Car1" in pr.model._car_domain, "Car 'Car1' should be loaded"
    car = pr.model.get_car("Car1")
    assert car.idx == "Car1"

    # Check operators
    assert "Train" in pr.model._operator_domain, "Operator 'Train' should be loaded"
    train = pr.model.get_operator("Train")
    assert train.idx == "Train"

    # Check schedules
    assert "NEW" in pr.model._sc_domain, "Schedule 'NEW' should be loaded"
    schedule = pr.model.get_schedule("NEW")
    assert schedule.idx == "NEW"


def test_system_commands(rocrail_server):
    """Test basic system commands"""
    pr = rocrail_server

    # Power control
    pr.power_on()
    time.sleep(0.5)

    pr.power_off()
    time.sleep(0.5)

    # Auto mode
    pr.auto_on()
    time.sleep(0.5)

    pr.auto_off()
    time.sleep(0.5)


def test_locomotive_control(rocrail_server):
    """Test locomotive control commands"""
    pr = rocrail_server

    loco = pr.model.get_lc("Loc1")

    # Power on first
    pr.power_on()
    time.sleep(0.5)

    # Set speed
    loco.set_speed(30)
    time.sleep(0.5)

    # Change direction
    loco.set_direction(forward=False)
    time.sleep(0.5)

    loco.set_direction(forward=True)
    time.sleep(0.5)

    # Stop
    loco.stop()
    time.sleep(0.5)

    # Power off
    pr.power_off()


def test_locomotive_functions(rocrail_server):
    """Test locomotive function commands (F0-F31)

    This verifies the fixed set_function() method that uses <fn> tag format
    with all function states as required by Rocrail protocol.
    """
    pr = rocrail_server

    loco = pr.model.get_lc("Loc1")

    # Power on first
    pr.power_on()
    time.sleep(0.5)

    # Test function 0 (lights)
    loco.set_function(0, True)
    time.sleep(0.5)

    loco.set_function(0, False)
    time.sleep(0.5)

    # Test function 1
    loco.set_function(1, True)
    time.sleep(0.5)

    loco.set_function(1, False)
    time.sleep(0.5)

    # Test multiple functions at once
    loco.set_function(0, True)
    loco.set_function(1, True)
    loco.set_function(2, True)
    time.sleep(0.5)

    # Turn all off
    loco.set_function(0, False)
    loco.set_function(1, False)
    loco.set_function(2, False)
    time.sleep(0.5)

    # Power off
    pr.power_off()


def test_switch_control(rocrail_server):
    """Test switch control commands"""
    pr = rocrail_server

    sw = pr.model.get_sw("sw1")

    # Switch positions
    sw.straight()
    time.sleep(0.5)

    sw.turnout()
    time.sleep(0.5)

    sw.flip()
    time.sleep(0.5)


def test_signal_control(rocrail_server):
    """Test signal control commands"""
    pr = rocrail_server

    sg = pr.model.get_sg("sg1")

    # Signal aspects
    sg.red()
    time.sleep(0.5)

    sg.green()
    time.sleep(0.5)

    sg.yellow()
    time.sleep(0.5)

    sg.red()
    time.sleep(0.5)


def test_block_control(rocrail_server):
    """Test block control commands"""
    pr = rocrail_server

    bk = pr.model.get_bk("bk1")

    # Block operations
    bk.close()
    time.sleep(0.5)

    bk.open()
    time.sleep(0.5)


def test_output_control(rocrail_server):
    """Test output control commands"""
    pr = rocrail_server

    co = pr.model.get_co("co1")

    # Output control
    co.on()
    time.sleep(0.5)

    co.off()
    time.sleep(0.5)

    co.flip()
    time.sleep(0.5)


def test_feedback_sensor(rocrail_server):
    """Test feedback sensor operations"""
    pr = rocrail_server

    fb = pr.model.get_fb("fb1")

    # Manual feedback control (for testing)
    fb.on()
    time.sleep(0.5)

    fb.off()
    time.sleep(0.5)


def test_clock_control(rocrail_server):
    """Test clock control"""
    pr = rocrail_server

    # Set time
    pr.set_clock(hour=12, minute=30)
    time.sleep(0.5)

    # Set divider (speed up clock)
    pr.set_clock(divider=10)
    time.sleep(0.5)

    # Freeze clock
    pr.set_clock(freeze=True)
    time.sleep(0.5)

    # Resume clock
    pr.set_clock(freeze=False)
    time.sleep(0.5)


def test_model_queries(rocrail_server):
    """Test model query commands"""
    pr = rocrail_server

    # These commands request data from the server
    pr.model.request_locomotive_list()
    time.sleep(0.5)

    pr.model.request_switch_list()
    time.sleep(0.5)

    pr.model.request_feedback_list()
    time.sleep(0.5)


def test_add_object_api(rocrail_server):
    """Test object-based API for adding objects to the model

    This test verifies that objects added via add_object() are actually
    saved to the Rocrail server by:
    1. Creating a new feedback sensor object
    2. Adding it via model.add_object()
    3. Clearing the local model cache
    4. Re-requesting the plan from server
    5. Verifying the object exists in the refreshed plan
    """
    pr = rocrail_server

    # Create a new feedback sensor with unique ID
    import xml.etree.ElementTree as ET
    from pyrocrail.objects.feedback import Feedback

    test_fb_id = f"test_fb_{int(time.time())}"
    fb_xml = ET.fromstring(f'<fb id="{test_fb_id}" addr="99" iid="TEST" bus="0" state="false"/>')
    new_fb = Feedback(fb_xml, pr.com)

    # Add the object via object-based API
    pr.model.add_object(new_fb)
    time.sleep(1)  # Wait for server to process

    # Clear the local domain to force refresh from server
    pr.model._fb_domain.clear()

    # Re-request the plan from server
    pr.model.plan_recv = False
    pr.model.communicator.send("model", '<model cmd="plan"/>')

    # Wait for plan to be received
    timeout = 10
    start = time.time()
    while not pr.model.plan_recv:
        time.sleep(0.1)
        if time.time() - start > timeout:
            pytest.fail("Timeout waiting for plan refresh")

    # Verify the object exists in the refreshed plan
    assert test_fb_id in pr.model._fb_domain, f"Feedback sensor '{test_fb_id}' should exist in refreshed plan"

    retrieved_fb = pr.model.get_fb(test_fb_id)
    assert retrieved_fb.idx == test_fb_id
    assert str(retrieved_fb.addr) == "99", f"Address should be 99, got {retrieved_fb.addr}"

    print(f"[+] Object-based API test passed: {test_fb_id} successfully added and retrieved")


def test_add_complex_object_api(rocrail_server):
    """Test object-based API for adding complex objects with children

    This test verifies that complex objects (with child elements) can be
    added via add_object() by:
    1. Creating a new schedule with multiple entries
    2. Adding it via model.add_object()
    3. Clearing the local model cache
    4. Re-requesting the plan from server
    5. Verifying the schedule and all entries exist
    """
    pr = rocrail_server

    # Create a new schedule with unique ID
    import xml.etree.ElementTree as ET
    from pyrocrail.objects.schedule import Schedule

    test_sc_id = f"test_schedule_{int(time.time())}"
    sc_xml = ET.fromstring(f'''<sc id="{test_sc_id}" timeframe="1" cycles="0" maxdelay="60">
        <scentry block="sb1" hour="8" minute="0"/>
        <scentry block="bk1" hour="10" minute="30"/>
        <scentry block="sb2" hour="12" minute="0"/>
    </sc>''')
    new_schedule = Schedule(sc_xml, pr.com)

    # Verify the schedule has entries
    assert len(new_schedule.entries) == 3, "Schedule should have 3 entries"
    assert new_schedule.entries[0].block == "sb1"
    assert new_schedule.entries[1].block == "bk1"
    assert new_schedule.entries[2].block == "sb2"

    # Add the object via object-based API
    pr.model.add_object(new_schedule)
    time.sleep(1)  # Wait for server to process

    # Clear the local domain to force refresh from server
    pr.model._sc_domain.clear()

    # Re-request the plan from server
    pr.model.plan_recv = False
    pr.model.communicator.send("model", '<model cmd="plan"/>')

    # Wait for plan to be received
    timeout = 10
    start = time.time()
    while not pr.model.plan_recv:
        time.sleep(0.1)
        if time.time() - start > timeout:
            pytest.fail("Timeout waiting for plan refresh")

    # Verify the schedule exists in the refreshed plan
    assert test_sc_id in pr.model._sc_domain, f"Schedule '{test_sc_id}' should exist in refreshed plan"

    retrieved_schedule = pr.model.get_schedule(test_sc_id)
    assert retrieved_schedule.idx == test_sc_id
    assert retrieved_schedule.timeframe == 1

    # Verify all entries were saved
    assert len(retrieved_schedule.entries) == 3, f"Schedule should have 3 entries, got {len(retrieved_schedule.entries)}"
    assert retrieved_schedule.entries[0].block == "sb1", "First entry should be sb1"
    assert retrieved_schedule.entries[1].block == "bk1", "Second entry should be bk1"
    assert retrieved_schedule.entries[2].block == "sb2", "Third entry should be sb2"
    assert retrieved_schedule.entries[0].hour == 8
    assert retrieved_schedule.entries[1].minute == 30

    print(f"[+] Complex object API test passed: {test_sc_id} with 3 entries successfully added and retrieved")


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
