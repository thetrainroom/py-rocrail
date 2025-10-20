#!/usr/bin/env python3
"""Test script to demonstrate trigger functionality"""

from pyrocrail.pyrocrail import PyRocrail, Action, Trigger


def my_script(model):
    """Example script that runs on trigger"""
    print(f"[TRIGGER FIRED] Time: {model.clock.hour}:{model.clock.minute:02d}")
    print(f"  - Locomotives: {len(model._lc_domain)}")
    print(f"  - Blocks: {len(model._bk_domain)}")
    print(f"  - Feedback sensors: {len(model._fb_domain)}")
    return "Success"


def test_time_trigger():
    """Test TIME trigger functionality"""
    print("="*80)
    print("Testing TIME Trigger Functionality")
    print("="*80)

    # Create PyRocrail instance (mock - won't connect)
    print("\n1. Creating PyRocrail instance...")
    pr = PyRocrail("localhost", 8051)

    # Create a TIME trigger action
    print("2. Creating TIME trigger action...")
    action = Action(
        script=my_script,
        trigger_type=Trigger.TIME,
        trigger="12:30",  # NOTE: This value is currently IGNORED
        condition="",
        timeout=60
    )

    # Add the action
    print("3. Adding action to PyRocrail...")
    pr.add(action)

    # Check where it was added
    print(f"   - Time actions: {len(pr._time_actions)}")
    print(f"   - Event actions: {len(pr._event_actions)}")

    # Simulate what happens when time callback is triggered
    print("\n4. Simulating clock update (this would normally come from Rocrail server)...")
    print("   NOTE: Currently _exec_time() runs ALL time actions on EVERY clock update")
    print("   It does NOT check the 'trigger' time value!")

    # This would be called by model when clock updates
    # pr._exec_time()  # Can't call directly without model initialized

    print("\n" + "="*80)
    print("FINDINGS:")
    print("="*80)
    print("(OK) Actions are stored correctly in _time_actions list")
    print("[ISSUE] TIME trigger executes on EVERY clock update, not at specific time")
    print("[ISSUE] The 'trigger' parameter (e.g., '12:30') is NEVER checked")
    print("[ISSUE] The 'condition' parameter is NEVER evaluated")
    print("[ISSUE] The 'timeout' parameter is NEVER used")
    print("\n" + "="*80)
    print("RECOMMENDED FIXES:")
    print("="*80)
    print("1. In _exec_time(), check if current time matches action.trigger")
    print("2. Evaluate action.condition before executing script")
    print("3. Implement timeout handling in ThreadPoolExecutor")
    print("4. Implement _exec_event() for EVENT triggers")
    print("\nExample fix for _exec_time():")
    print("""
    def _exec_time(self):
        current_time = f"{self.model.clock.hour}:{self.model.clock.minute:02d}"
        for ac in self._time_actions:
            # Check if trigger time matches
            if ac.trigger and ac.trigger != current_time:
                continue

            # Check condition (would need eval or parser)
            if ac.condition:
                # TODO: Evaluate condition safely
                pass

            # Execute with timeout
            ac._start_time = time.monotonic()
            future = self._executor.submit(ac.script, self.model)
            # Store with timeout for cleanup thread to check
            self.__threads.append((future, ac.timeout))
    """)

    print("\n")


def test_event_trigger():
    """Test EVENT trigger functionality"""
    print("="*80)
    print("Testing EVENT Trigger Functionality")
    print("="*80)

    pr = PyRocrail("localhost", 8051)

    # Create an EVENT trigger action
    action = Action(
        script=my_script,
        trigger_type=Trigger.EVENT,
        trigger="fb1",  # Feedback sensor ID
        condition="state == 'on'",
        timeout=60
    )

    pr.add(action)

    print(f"(OK) Event action added to _event_actions list: {len(pr._event_actions)}")
    print("[ISSUE] BUT there is NO _exec_event() method!")
    print("[ISSUE] Event triggers will NEVER execute!")
    print("\nTo fix: Need to implement model.change_callback handler")
    print("""
    def _exec_event(self, obj_type, obj_id, obj):
        for ac in self._event_actions:
            # Check if trigger matches (e.g., 'fb1' matches obj_id)
            if ac.trigger and ac.trigger != obj_id:
                continue

            # Evaluate condition (e.g., "state == 'on'")
            if ac.condition:
                # TODO: Safely evaluate condition against obj attributes
                pass

            # Execute script
            self.__threads.append(self._executor.submit(ac.script, self.model))

    # Then in __init__, set:
    # self.model.change_callback = self._exec_event
    """)
    print("\n")


if __name__ == "__main__":
    test_time_trigger()
    print("\n")
    test_event_trigger()
