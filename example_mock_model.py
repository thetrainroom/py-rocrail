#!/usr/bin/env python3
"""Examples of different mocking approaches"""

from unittest.mock import Mock
from pyrocrail.pyrocrail import PyRocrail, Action, Trigger


def example_1_real_model_no_connection():
    """Simplest: Real model, no server connection"""
    print("="*80)
    print("Example 1: Real Model, No Connection")
    print("="*80)

    # Create real PyRocrail but don't call start()
    pr = PyRocrail("localhost", 8051)

    # The model exists and is real
    print(f"Model type: {type(pr.model)}")
    print(f"Model has clock: {hasattr(pr.model, 'clock')}")

    # Manually set clock
    pr.model.clock.hour = 14
    pr.model.clock.minute = 30

    # Access model domains (they're empty but exist)
    print(f"Locomotive domain: {len(pr.model._lc_domain)}")
    print(f"Feedback domain: {len(pr.model._fb_domain)}")

    # Populate with test data if needed
    from pyrocrail.objects.feedback import Feedback
    import xml.etree.ElementTree as ET

    fb_xml = ET.fromstring('<fb id="fb1" state="true"/>')
    fb = Feedback(fb_xml, pr.communicator)
    pr.model._fb_domain['fb1'] = fb

    print(f"Added feedback: {len(pr.model._fb_domain)}")
    print()


def example_2_mock_model_with_unittest():
    """Using unittest.mock for full control"""
    print("="*80)
    print("Example 2: Mock Model with unittest.mock")
    print("="*80)

    # Create mock model
    mock_model = Mock()
    mock_model.clock = Mock()
    mock_model.clock.hour = 12
    mock_model.clock.minute = 0

    # Mock domains
    mock_model._lc_domain = {'lc1': Mock(V=50, idx='lc1')}
    mock_model._fb_domain = {'fb1': Mock(state=True, idx='fb1')}

    # Your action script receives this mock
    def my_script(model):
        print(f"  Time: {model.clock.hour}:{model.clock.minute:02d}")
        print(f"  Locomotives: {len(model._lc_domain)}")
        print(f"  First loco speed: {model._lc_domain['lc1'].V}")
        return "Success"

    # Call script with mock
    result = my_script(mock_model)
    print(f"Result: {result}")
    print()


def example_3_replace_model_in_pyrocrail():
    """Replace the model in a PyRocrail instance"""
    print("="*80)
    print("Example 3: Replace Model in PyRocrail")
    print("="*80)

    # Create PyRocrail
    pr = PyRocrail("localhost", 8051)

    # Replace with mock
    pr.model = Mock()
    pr.model.clock = Mock(hour=15, minute=45)
    pr.model._lc_domain = {}
    pr.model._fb_domain = {}

    def test_action(model):
        print(f"  Received model: {type(model)}")
        print(f"  Clock: {model.clock.hour}:{model.clock.minute:02d}")
        return "Tested"

    # Add action
    action = Action(test_action, Trigger.TIME, "15:45")
    pr.add(action)

    # Trigger it
    pr._exec_time()
    print()


def example_4_custom_test_model():
    """Create a custom minimal test model"""
    print("="*80)
    print("Example 4: Custom Test Model Class")
    print("="*80)

    class TestModel:
        """Minimal model for testing"""
        def __init__(self):
            self.clock = type('Clock', (), {'hour': 10, 'minute': 0})()
            self._lc_domain = {}
            self._fb_domain = {}
            self._bk_domain = {}

        def add_loco(self, id, speed=0):
            """Add test locomotive"""
            self._lc_domain[id] = type('Loco', (), {
                'idx': id,
                'V': speed,
                'dir': True
            })()

        def add_feedback(self, id, state=False):
            """Add test feedback sensor"""
            self._fb_domain[id] = type('Feedback', (), {
                'idx': id,
                'state': state
            })()

    # Use it
    test_model = TestModel()
    test_model.add_loco('lc1', speed=80)
    test_model.add_feedback('fb1', state=True)

    def my_action(model):
        print(f"  Time: {model.clock.hour}:{model.clock.minute:02d}")
        print(f"  Locos: {list(model._lc_domain.keys())}")
        print(f"  Loco speed: {model._lc_domain['lc1'].V}")
        print(f"  Sensors: {list(model._fb_domain.keys())}")
        print(f"  Sensor state: {model._fb_domain['fb1'].state}")

    my_action(test_model)
    print()


def example_5_which_to_use():
    """Guidance on which approach to use"""
    print("="*80)
    print("Which Mocking Approach to Use?")
    print("="*80)
    print("""
1. REAL MODEL, NO CONNECTION (Recommended for most tests)
   Use when: Testing trigger logic, simple unit tests
   Pros: Real code paths, easy setup
   Cons: Creates unused objects

   pr = PyRocrail("localhost", 8051)
   pr.model.clock.hour = 12
   pr._exec_time()

2. unittest.mock (For isolated unit tests)
   Use when: Need precise control, testing error cases
   Pros: Full control, can track method calls
   Cons: More setup code

   mock_model = Mock()
   mock_model.clock.hour = 12
   my_script(mock_model)

3. REPLACE MODEL (For integration-style tests)
   Use when: Testing PyRocrail interaction with model
   Pros: Tests full flow
   Cons: More complex setup

   pr = PyRocrail("localhost", 8051)
   pr.model = Mock()
   pr._exec_time()

4. CUSTOM TEST MODEL (For complex test scenarios)
   Use when: Need realistic but controlled test data
   Pros: Reusable, clear test data
   Cons: More code to maintain

   class TestModel:
       def __init__(self): ...
       def add_loco(self, id): ...

   test_model = TestModel()

RECOMMENDATION: Start with #1 (Real Model, No Connection)
    """)


if __name__ == "__main__":
    example_1_real_model_no_connection()
    example_2_mock_model_with_unittest()
    example_3_replace_model_in_pyrocrail()
    example_4_custom_test_model()
    example_5_which_to_use()
