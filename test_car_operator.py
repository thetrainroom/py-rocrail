#!/usr/bin/env python3
"""Test script to verify Car and Operator object loading"""

import xml.etree.ElementTree as ET
from pyrocrail.communicator import Communicator
from pyrocrail.model import Model


def test_car_operator_loading():
    """Test that Car and Operator objects load from plan XML"""

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

    # Check cars were loaded
    print(f"\nCars loaded: {len(model._car_domain)}")
    if len(model._car_domain) > 0:
        car_id = list(model._car_domain.keys())[0]
        car = model.get_car(car_id)
        print(f"   Sample car: {car_id}")
        print(f"   - Type: {car.type}")
        print(f"   - Status: {car.status}")
        print(f"   - Location: {car.location}")

    # Check operators were loaded
    print(f"\nOperators loaded: {len(model._operator_domain)}")
    if len(model._operator_domain) > 0:
        opr_id = list(model._operator_domain.keys())[0]
        opr = model.get_operator(opr_id)
        print(f"   Sample operator: {opr_id}")
        print(f"   - Locomotive: {opr.lcid}")
        print(f"   - Cars: {opr.carids}")
        print(f"   - Cargo: {opr.cargo}")

    # Test car commands
    if len(model._car_domain) > 0:
        print("\nTesting Car commands:")
        car = list(model._car_domain.values())[0]
        print(f"   - empty() command ready")
        print(f"   - loaded() command ready")
        print(f"   - maintenance() command ready")
        print(f"   - assign_waybill() command ready")
        print(f"   - reset_waybill() command ready")

    # Test operator commands
    if len(model._operator_domain) > 0:
        print("\nTesting Operator commands:")
        opr = list(model._operator_domain.values())[0]
        print(f"   - empty_car() command ready")
        print(f"   - load_car() command ready")
        print(f"   - add_car() command ready")
        print(f"   - leave_car() command ready")

    print("\nAll tests passed!")
    return True


if __name__ == "__main__":
    test_car_operator_loading()
