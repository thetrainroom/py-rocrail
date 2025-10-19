import time
import re
from typing import Callable
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, Future

from pyrocrail.model import Model
from pyrocrail.communicator import Communicator


class Trigger(Enum):
    TIME = 0
    EVENT = 1


class Action:
    def __init__(
        self,
        script: Callable,
        trigger_type: Trigger = Trigger.TIME,
        trigger: str | None = None,
        condition: str = "",
        timeout: int | float = 60,
        on_success: Callable | None = None,
        on_error: Callable | None = None,
    ):
        """Create an action with trigger pattern and condition.

        Args:
            script: Function to execute, receives model as parameter
            trigger_type: TIME or EVENT
            trigger: Time pattern (for TIME) or object ID pattern (for EVENT)
                TIME patterns:
                  - "12:30" - exact time
                  - "*:00" - every hour at :00
                  - "*/2:00" - every 2 hours at :00
                  - "*:*/15" - every 15 minutes
                  - "*:*" or "*" or None - every clock update
                EVENT patterns:
                  - "fb1" - specific object ID
                  - "fb*" - wildcard pattern (all feedback sensors)
            condition: Python expression evaluated before execution
                Available variables: hour, minute, time (float), model
                Examples: "9 <= hour <= 17", "minute == 0"
            timeout: Maximum execution time in seconds
            on_success: Callback(result, elapsed_time) called when action completes successfully
            on_error: Callback(exception, elapsed_time) called when action fails or times out
        """
        self.script = script
        self.trigger_type = trigger_type
        self.trigger = trigger
        self.condition = condition
        self.timeout = timeout
        self.on_success = on_success
        self.on_error = on_error
        self._start_time = 0.0
        self._last_execution = None  # Track last execution time to avoid duplicates
        self.name = script.__name__ if hasattr(script, "__name__") else "anonymous"  # For logging


class PyRocrail:
    def __init__(self, ip: str = "localhost", port: int = 8051):
        self.com = Communicator(ip, port)
        self.model = Model(self.com)
        self._event_actions: list[Action] = []
        self._time_actions: list[Action] = []
        self._executor = ThreadPoolExecutor()
        self.__threads: list[Future] = []
        self.running = True
        self.__clean_thread = None

    def __del__(self):
        self.stop()

    def start(self):
        self.com.start()
        self.model.init()
        self.model.time_callback = self._exec_time
        self.model.change_callback = self._exec_event
        self.__clean_thread = threading.Thread(target=self.__clean)
        self.__clean_thread.start()

    def stop(self):
        self.running = False
        if self.__clean_thread is not None:
            self.__clean_thread.join()
        self.com.stop()

    def power_on(self):
        """Turn system power on"""
        self.com.send("sys", '<sys cmd="go"/>')

    def power_off(self):
        """Turn system power off"""
        self.com.send("sys", '<sys cmd="stop"/>')

    def emergency_stop(self):
        """Emergency stop all trains"""
        # TODO: Verify emergency stop command format
        self.com.send("sys", '<sys cmd="ebreak"/>')

    def auto_on(self):
        """Enable automatic mode"""
        self.com.send("auto", '<auto cmd="on"/>')

    def auto_off(self):
        """Disable automatic mode"""
        self.com.send("auto", '<auto cmd="off"/>')

    def reset(self):
        """Reset the system"""
        # TODO: Verify reset command format
        self.com.send("sys", '<sys cmd="reset"/>')

    def add(self, action: Action):
        if action.trigger_type == Trigger.TIME:
            self._time_actions.append(action)
        else:
            self._event_actions.append(action)

    def _match_time_pattern(self, pattern: str | None, hour: int, minute: int) -> bool:
        """Check if current time matches the trigger pattern.

        Pattern syntax:
          - "12:30" - exact time
          - "*:00" - every hour at :00
          - "*/2:00" - every 2 hours at :00 (0:00, 2:00, 4:00, ...)
          - "*:*/15" - every 15 minutes (0:00, 0:15, 0:30, ...)
          - "*:*", "*", None - every clock update

        Args:
            pattern: Time pattern string
            hour: Current hour (0-23)
            minute: Current minute (0-59)

        Returns:
            True if time matches pattern
        """
        # No pattern or wildcard = always match
        if not pattern or pattern == "*" or pattern == "*:*":
            return True

        # Parse pattern
        if ":" not in pattern:
            return False

        hour_pat, minute_pat = pattern.split(":", 1)

        # Check hour pattern
        if hour_pat == "*":
            # Match any hour
            pass
        elif hour_pat.startswith("*/"):
            # Interval: */2 = every 2 hours
            try:
                interval = int(hour_pat[2:])
                if hour % interval != 0:
                    return False
            except ValueError:
                return False
        else:
            # Exact hour
            try:
                if int(hour_pat) != hour:
                    return False
            except ValueError:
                return False

        # Check minute pattern
        if minute_pat == "*":
            # Match any minute
            pass
        elif minute_pat.startswith("*/"):
            # Interval: */15 = every 15 minutes
            try:
                interval = int(minute_pat[2:])
                if minute % interval != 0:
                    return False
            except ValueError:
                return False
        else:
            # Exact minute
            try:
                if int(minute_pat) != minute:
                    return False
            except ValueError:
                return False

        return True

    def _evaluate_condition(self, condition: str, hour: int, minute: int, model: Model) -> bool:
        """Safely evaluate a condition expression.

        Available variables: hour, minute, time (as float), model

        Args:
            condition: Python expression string
            hour: Current hour
            minute: Current minute
            model: Model reference

        Returns:
            True if condition evaluates to true, False otherwise
        """
        if not condition:
            return True

        try:
            # Create limited scope with safe variables
            scope = {
                "hour": hour,
                "minute": minute,
                "time": hour + minute / 60.0,
                "model": model,
                # Add some safe builtins
                "abs": abs,
                "min": min,
                "max": max,
                "len": len,
            }
            # Evaluate expression in restricted scope
            result = eval(condition, {"__builtins__": {}}, scope)
            return bool(result)
        except Exception as e:
            print(f"Warning: Condition evaluation failed: {condition}")
            print(f"  Error: {e}")
            return False

    def _match_object_pattern(self, pattern: str | None, obj_id: str) -> bool:
        """Check if object ID matches the trigger pattern.

        Pattern syntax:
          - "fb1" - exact match
          - "fb*" - wildcard (all starting with "fb")
          - "*" or None - match any object

        Args:
            pattern: Object ID pattern
            obj_id: Actual object ID

        Returns:
            True if object matches pattern
        """
        if not pattern or pattern == "*":
            return True

        # Simple wildcard matching
        if "*" in pattern:
            # Convert to regex: "fb*" -> "^fb.*$"
            regex_pattern = "^" + pattern.replace("*", ".*") + "$"
            return bool(re.match(regex_pattern, obj_id))

        # Exact match
        return pattern == obj_id

    def _exec_time(self):
        """Execute time-based triggers on clock update."""
        hour = self.model.clock.hour
        minute = self.model.clock.minute
        current_time_key = (hour, minute)

        for ac in self._time_actions:
            # Check if pattern matches
            if not self._match_time_pattern(ac.trigger, hour, minute):
                continue

            # Avoid duplicate execution in same minute
            if ac._last_execution == current_time_key:
                continue

            # Check condition
            if not self._evaluate_condition(ac.condition, hour, minute, self.model):
                continue

            # Execute action
            ac._start_time = time.monotonic()
            ac._last_execution = current_time_key
            future = self._executor.submit(ac.script, self.model)
            self.__threads.append((future, ac.timeout, ac._start_time, ac))

    def _exec_event(self, obj_type: str, obj_id: str, obj):
        """Execute event-based triggers on object state changes."""
        for ac in self._event_actions:
            # Check if object pattern matches
            if not self._match_object_pattern(ac.trigger, obj_id):
                continue

            # Check condition (with object attributes available)
            if ac.condition:
                try:
                    scope = {
                        "obj_type": obj_type,
                        "obj_id": obj_id,
                        "obj": obj,
                        "model": self.model,
                        "hour": self.model.clock.hour,
                        "minute": self.model.clock.minute,
                        "time": self.model.clock.hour + self.model.clock.minute / 60.0,
                        # Safe builtins
                        "abs": abs,
                        "min": min,
                        "max": max,
                        "len": len,
                        "hasattr": hasattr,
                        "getattr": getattr,
                    }
                    result = eval(ac.condition, {"__builtins__": {}}, scope)
                    if not result:
                        continue
                except Exception as e:
                    print(f"Warning: Event condition evaluation failed: {ac.condition}")
                    print(f"  Error: {e}")
                    continue

            # Execute action
            ac._start_time = time.monotonic()
            future = self._executor.submit(ac.script, self.model)
            self.__threads.append((future, ac.timeout, ac._start_time, ac))

    def __clean(self):
        """Cleanup thread - monitors futures and enforces timeouts."""
        while self.running:
            time.sleep(0.1)  # Check every 100ms
            if len(self.__threads) > 0:
                item = self.__threads.pop(0)

                # Handle different formats
                if isinstance(item, tuple):
                    if len(item) == 4:
                        # New format: (future, timeout, start_time, action)
                        future, timeout, start_time, action = item
                    elif len(item) == 3:
                        # Old format: (future, timeout, start_time)
                        future, timeout, start_time = item
                        action = None
                    else:
                        # Unknown format
                        continue
                else:
                    # Legacy format for backwards compatibility
                    future = item
                    timeout = 60
                    start_time = time.monotonic()
                    action = None

                # Check if done
                if future.done():
                    elapsed = time.monotonic() - start_time
                    exp = future.exception(timeout=0)
                    if exp:
                        # Action failed
                        print(f"Action '{action.name if action else 'unknown'}' failed: {repr(exp)}")
                        if action and action.on_error:
                            try:
                                action.on_error(exp, elapsed)
                            except Exception as callback_err:
                                print(f"  Error callback failed: {repr(callback_err)}")
                    else:
                        # Action succeeded
                        result = future.result()
                        if action and action.on_success:
                            try:
                                action.on_success(result, elapsed)
                            except Exception as callback_err:
                                print(f"  Success callback failed: {repr(callback_err)}")
                    continue

                # Check timeout
                elapsed = time.monotonic() - start_time
                if elapsed > timeout:
                    print(f"Warning: Action '{action.name if action else 'unknown'}' timeout after {elapsed:.1f}s (limit: {timeout}s)")
                    future.cancel()
                    if action and action.on_error:
                        try:
                            action.on_error(TimeoutError(f"Timeout after {elapsed:.1f}s"), elapsed)
                        except Exception as callback_err:
                            print(f"  Error callback failed: {repr(callback_err)}")
                    continue

                # Still running, put back in queue
                self.__threads.append((future, timeout, start_time, action) if action else (future, timeout, start_time))
