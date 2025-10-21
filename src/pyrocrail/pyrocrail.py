import time
import re
import atexit
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
        self._last_execution: tuple[int, int] | None = None  # Track last execution time to avoid duplicates
        self.name = script.__name__ if hasattr(script, "__name__") else "anonymous"  # For logging


class PyRocrail:
    def __init__(self, ip: str = "localhost", port: int = 8051, verbose: bool = False):
        """Initialize PyRocrail connection

        Args:
            ip: Rocrail server IP address
            port: Rocrail server port
            verbose: Enable verbose logging (prints all sent/received messages)
        """
        self.com = Communicator(ip, port, verbose=verbose)
        self.model = Model(self.com)
        self._event_actions: list[Action] = []
        self._time_actions: list[Action] = []
        self._executor = ThreadPoolExecutor()
        self.__threads: list[tuple[Future, int | float, float, Action] | tuple[Future, int | float, float]] = []
        self.running = True
        self.__clean_thread = None
        self.verbose = verbose
        self._stopped = False

        # Register cleanup handler for exit() / interactive mode
        atexit.register(self.stop)

    def __enter__(self):
        """Context manager entry - allows 'with PyRocrail() as pr:' syntax"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatic cleanup"""
        self.stop()
        return False  # Don't suppress exceptions

    def __del__(self):
        """Destructor - final backup cleanup (unreliable, prefer context manager or explicit stop())"""
        self.stop()

    def start(self) -> None:
        self.com.start()
        self.model.init()
        self.model.time_callback = self._exec_time
        self.model.change_callback = self._exec_event
        self.__clean_thread = threading.Thread(target=self.__clean)
        self.__clean_thread.start()

    def stop(self) -> None:
        """Stop PyRocrail and cleanup resources

        Safe to call multiple times (idempotent).
        """
        if self._stopped:
            return  # Already stopped, prevent duplicate cleanup

        self._stopped = True
        self.running = False

        # Stop cleanup thread
        if self.__clean_thread is not None and self.__clean_thread.is_alive():
            self.__clean_thread.join(timeout=5.0)

        # Shutdown executor
        try:
            self._executor.shutdown(wait=True, cancel_futures=True)
        except Exception:
            pass  # Executor may already be shutdown

        # Stop communicator
        self.com.stop()

    def power_on(self) -> None:
        """Turn system power on"""
        self.com.send("sys", '<sys cmd="go"/>')

    def power_off(self) -> None:
        """Turn system power off"""
        self.com.send("sys", '<sys cmd="stop"/>')

    def emergency_stop(self) -> None:
        """Emergency stop all trains"""
        # TODO: Verify emergency stop command format
        self.com.send("sys", '<sys cmd="ebreak"/>')

    def auto_on(self) -> None:
        """Enable automatic mode"""
        self.com.send("auto", '<auto cmd="on"/>')

    def auto_off(self) -> None:
        """Disable automatic mode"""
        self.com.send("auto", '<auto cmd="off"/>')

    def reset(self) -> None:
        """Reset the system"""
        self.com.send("sys", '<sys cmd="reset"/>')

    def save(self) -> None:
        """Save Rocrail plan to disk"""
        self.com.send("sys", '<sys cmd="save"/>')

    def shutdown(self) -> None:
        """Shutdown Rocrail server

        Warning: This will terminate the Rocrail server process.
        """
        self.com.send("sys", '<sys cmd="shutdown"/>')

    def query(self) -> None:
        """Query server capabilities and version information"""
        self.com.send("sys", '<sys cmd="query"/>')

    def start_of_day(self) -> None:
        """Execute start of day operations

        Typically used to initialize the layout at the beginning of an operating session.
        """
        self.com.send("sys", '<sys cmd="sod"/>')

    def end_of_day(self) -> None:
        """Execute end of day operations

        Typically used to shut down the layout at the end of an operating session.
        """
        self.com.send("sys", '<sys cmd="eod"/>')

    def update_ini(self) -> None:
        """Update Rocrail configuration from rocrail.ini file

        Reloads configuration settings without restarting the server.
        """
        self.com.send("sys", '<sys cmd="updateini"/>')

    def set_clock(self, hour: int | None = None, minute: int | None = None, divider: int | None = None, freeze: bool | None = None) -> None:
        """Control the fast clock

        Args:
            hour: Set clock hour (0-23), None to keep current
            minute: Set clock minute (0-59), None to keep current
            divider: Clock speed divider (1=real time, 2=2x speed, etc.), None to keep current
            freeze: True to freeze clock, False to resume, None to keep current

        Examples:
            pr.set_clock(hour=12, minute=30)  # Set time to 12:30
            pr.set_clock(divider=10)  # Run clock at 10x speed
            pr.set_clock(freeze=True)  # Freeze the clock
            pr.set_clock(freeze=False)  # Resume the clock
        """
        attrs = []
        if hour is not None:
            attrs.append(f'hour="{hour}"')
        if minute is not None:
            attrs.append(f'minute="{minute}"')
        if divider is not None:
            attrs.append(f'divider="{divider}"')
        if freeze is not None:
            attrs.append(f'freeze="{"true" if freeze else "false"}"')

        if attrs:
            self.com.send("clock", f'<clock {" ".join(attrs)}/>')

    def fire_event(self, event_id: str, **kwargs: str) -> None:
        """Fire a custom event

        Args:
            event_id: Event identifier
            **kwargs: Additional event attributes

        Example:
            pr.fire_event("my_custom_event", state="active", value="123")
        """
        attrs = [f'id="{event_id}"']
        for key, value in kwargs.items():
            attrs.append(f'{key}="{value}"')

        self.com.send("event", f'<event {" ".join(attrs)}/>')

    def request_locomotive_list(self) -> None:
        """Request list of all locomotives from server

        The server will respond with locomotive data that will be processed
        by the model's decode method.
        """
        self.com.send("sys", '<sys cmd="locliste"/>')

    def add(self, action: Action) -> None:
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
            if self.verbose:
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
                    if self.verbose:
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
            if not self.running:  # Check again after sleep
                break
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
                        if action and action.on_error:
                            try:
                                action.on_error(exp, elapsed)
                            except Exception as callback_err:
                                if self.verbose:
                                    print(f"  Error callback failed: {repr(callback_err)}")
                        else:
                            # Only print if no callback registered
                            if self.verbose:
                                print(f"Action '{action.name if action else 'unknown'}' failed: {repr(exp)}")
                    else:
                        # Action succeeded
                        result = future.result()
                        if action and action.on_success:
                            try:
                                action.on_success(result, elapsed)
                            except Exception as callback_err:
                                if self.verbose:
                                    print(f"  Success callback failed: {repr(callback_err)}")
                    continue

                # Check timeout
                elapsed = time.monotonic() - start_time
                if elapsed > timeout:
                    future.cancel()
                    if action and action.on_error:
                        try:
                            action.on_error(TimeoutError(f"Timeout after {elapsed:.1f}s"), elapsed)
                        except Exception as callback_err:
                            if self.verbose:
                                print(f"  Error callback failed: {repr(callback_err)}")
                    else:
                        # Only print if no callback registered
                        if self.verbose:
                            print(f"Warning: Action '{action.name if action else 'unknown'}' timeout after {elapsed:.1f}s (limit: {timeout}s)")
                    continue

                # Still running, put back in queue
                self.__threads.append((future, timeout, start_time, action) if action else (future, timeout, start_time))
