import time
import re
import atexit
import logging
from typing import Callable
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, Future

from pyrocrail.model import Model
from pyrocrail.communicator import Communicator

# Use package-level logger
logger = logging.getLogger("pyrocrail")


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
    def __init__(
        self,
        ip: str = "localhost",
        port: int = 8051,
        verbose: bool = False,
        on_disconnect: Callable[[Model], None] | None = None,
    ):
        """Initialize PyRocrail connection

        Args:
            ip: Rocrail server IP address
            port: Rocrail server port
            verbose: Enable verbose logging (prints all sent/received messages)
            on_disconnect: Callback function called when connection to Rocrail is lost unexpectedly.
                         Receives Model snapshot for state recovery. Use this to:
                         - Cut power to tracks (hardware relay)
                         - Save layout state for manual recovery
                         - Alert operator
        """
        self.com = Communicator(ip, port, verbose=verbose, on_disconnect=on_disconnect)
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

    def start_locomotive_in_block(self, block_id: str) -> bool:
        """Start the locomotive in a block or staging block

        Automatically detects whether the ID refers to a regular block or
        staging block and starts the appropriate locomotive:
        - Regular block: Starts the locomotive in block.locid
        - Staging block: Expands the staging yard and starts the exit locomotive

        Args:
            block_id: Block ID or staging block ID (names are unique)

        Returns:
            True if locomotive was started, False if block/stage is empty or not found

        Example:
            pr.start_locomotive_in_block("BK01")    # Regular block
            pr.start_locomotive_in_block("SB_T0")   # Staging block
        """
        # Try as regular block first
        block = self.model.get_bk(block_id)
        if block:
            if block.locid:
                loco = self.model.get_lc(block.locid)
                if loco:
                    loco.go()
                    return True
            return False

        # Try as staging block
        stage = self.model.get_stage(block_id)
        if stage:
            exit_loco_id = stage.get_exit_locomotive()
            if exit_loco_id:
                stage.expand()  # Activate train in exit section
                loco = self.model.get_lc(exit_loco_id)
                if loco:
                    loco.go()
                    return True
            return False

        # Neither block nor staging block found
        logger.warning(f"Block or staging block '{block_id}' not found")
        return False

    def add(self, action: Action) -> None:
        if action.trigger_type == Trigger.TIME:
            self._time_actions.append(action)
        else:
            self._event_actions.append(action)

    # ========== Condition Helper Functions ==========
    # These helpers make writing conditions easier and more readable

    # Sensor/Feedback helpers
    def _is_active(self, obj_id: str) -> bool:
        """Check if a feedback sensor is active"""
        try:
            fb = self.model.get_fb(obj_id)
            return getattr(fb, "state", False)
        except (KeyError, AttributeError):
            return False

    def _is_inactive(self, obj_id: str) -> bool:
        """Check if a feedback sensor is inactive"""
        return not self._is_active(obj_id)

    # Block helpers
    def _is_occupied(self, block_id: str) -> bool:
        """Check if a block is occupied"""
        try:
            bk = self.model.get_bk(block_id)
            return getattr(bk, "occ", False)
        except (KeyError, AttributeError):
            return False

    def _is_free(self, block_id: str) -> bool:
        """Check if a block is free (not occupied)"""
        return not self._is_occupied(block_id)

    def _is_reserved(self, block_id: str) -> bool:
        """Check if a block is reserved"""
        try:
            bk = self.model.get_bk(block_id)
            return getattr(bk, "reserved", False)
        except (KeyError, AttributeError):
            return False

    # Switch helpers
    def _is_straight(self, switch_id: str) -> bool:
        """Check if switch is in straight position"""
        try:
            sw = self.model.get_sw(switch_id)
            return getattr(sw, "state", "") == "straight"
        except (KeyError, AttributeError):
            return False

    def _is_turnout(self, switch_id: str) -> bool:
        """Check if switch is in turnout position"""
        try:
            sw = self.model.get_sw(switch_id)
            return getattr(sw, "state", "") == "turnout"
        except (KeyError, AttributeError):
            return False

    def _is_left(self, switch_id: str) -> bool:
        """Check if 3-way switch is in left position"""
        try:
            sw = self.model.get_sw(switch_id)
            return getattr(sw, "state", "") == "left"
        except (KeyError, AttributeError):
            return False

    def _is_right(self, switch_id: str) -> bool:
        """Check if 3-way switch is in right position"""
        try:
            sw = self.model.get_sw(switch_id)
            return getattr(sw, "state", "") == "right"
        except (KeyError, AttributeError):
            return False

    # Signal helpers
    def _is_red(self, signal_id: str) -> bool:
        """Check if signal is showing red aspect"""
        try:
            sg = self.model.get_sg(signal_id)
            return getattr(sg, "aspect", "") == "red"
        except (KeyError, AttributeError):
            return False

    def _is_green(self, signal_id: str) -> bool:
        """Check if signal is showing green aspect"""
        try:
            sg = self.model.get_sg(signal_id)
            return getattr(sg, "aspect", "") == "green"
        except (KeyError, AttributeError):
            return False

    def _is_yellow(self, signal_id: str) -> bool:
        """Check if signal is showing yellow aspect"""
        try:
            sg = self.model.get_sg(signal_id)
            return getattr(sg, "aspect", "") == "yellow"
        except (KeyError, AttributeError):
            return False

    def _is_white(self, signal_id: str) -> bool:
        """Check if signal is showing white/shunt aspect"""
        try:
            sg = self.model.get_sg(signal_id)
            return getattr(sg, "aspect", "") == "white"
        except (KeyError, AttributeError):
            return False

    # Locomotive helpers
    def _is_moving(self, loco_id: str) -> bool:
        """Check if locomotive is moving (speed > 0)"""
        try:
            lc = self.model.get_lc(loco_id)
            return getattr(lc, "V", 0) > 0
        except (KeyError, AttributeError):
            return False

    def _is_stopped(self, loco_id: str) -> bool:
        """Check if locomotive is stopped (speed == 0)"""
        return not self._is_moving(loco_id)

    def _is_forward(self, loco_id: str) -> bool:
        """Check if locomotive direction is forward"""
        try:
            lc = self.model.get_lc(loco_id)
            return getattr(lc, "dir", True)
        except (KeyError, AttributeError):
            return False

    def _is_reverse(self, loco_id: str) -> bool:
        """Check if locomotive direction is reverse"""
        return not self._is_forward(loco_id)

    def _speed_above(self, loco_id: str, threshold: int) -> bool:
        """Check if locomotive speed is above threshold"""
        try:
            lc = self.model.get_lc(loco_id)
            return getattr(lc, "V", 0) > threshold
        except (KeyError, AttributeError):
            return False

    def _speed_below(self, loco_id: str, threshold: int) -> bool:
        """Check if locomotive speed is below threshold"""
        try:
            lc = self.model.get_lc(loco_id)
            return getattr(lc, "V", 0) < threshold
        except (KeyError, AttributeError):
            return False

    def _speed_between(self, loco_id: str, min_speed: int, max_speed: int) -> bool:
        """Check if locomotive speed is between min and max (inclusive)"""
        try:
            lc = self.model.get_lc(loco_id)
            speed = getattr(lc, "V", 0)
            return min_speed <= speed <= max_speed
        except (KeyError, AttributeError):
            return False

    # Route helpers
    def _is_locked(self, route_id: str) -> bool:
        """Check if route is locked"""
        try:
            st = self.model.get_st(route_id)
            return getattr(st, "status", "") == "locked"
        except (KeyError, AttributeError):
            return False

    def _is_unlocked(self, route_id: str) -> bool:
        """Check if route is unlocked"""
        return not self._is_locked(route_id)

    # Output helpers
    def _is_on(self, output_id: str) -> bool:
        """Check if output is on"""
        try:
            co = self.model.get_co(output_id)
            return getattr(co, "state", False)
        except (KeyError, AttributeError):
            return False

    def _is_off(self, output_id: str) -> bool:
        """Check if output is off"""
        return not self._is_on(output_id)

    # Collection/counting helpers
    def _count_occupied(self) -> int:
        """Count number of occupied blocks"""
        return sum(1 for bk in self.model.get_blocks().values() if getattr(bk, "occ", False))

    def _count_active(self, obj_type: str = "fb") -> int:
        """Count active objects (sensors by default)"""
        if obj_type == "fb":
            return sum(1 for fb in self.model.get_feedbacks().values() if getattr(fb, "state", False))
        elif obj_type == "co":
            return sum(1 for co in self.model.get_outputs().values() if getattr(co, "state", False))
        return 0

    def _count_moving(self) -> int:
        """Count number of moving locomotives"""
        return sum(1 for lc in self.model.get_locomotives().values() if getattr(lc, "V", 0) > 0)

    def _any_moving(self) -> bool:
        """Check if any locomotive is moving"""
        return self._count_moving() > 0

    def _all_stopped(self) -> bool:
        """Check if all locomotives are stopped"""
        return self._count_moving() == 0

    def _loco_in_block(self, loco_id: str, block_id: str) -> bool:
        """Check if specific locomotive is in specific block"""
        try:
            bk = self.model.get_bk(block_id)
            return getattr(bk, "locid", "") == loco_id
        except (KeyError, AttributeError):
            return False

    def _block_has_loco(self, block_id: str) -> bool:
        """Check if block has any locomotive"""
        try:
            bk = self.model.get_bk(block_id)
            return bool(getattr(bk, "locid", ""))
        except (KeyError, AttributeError):
            return False

    # Logic helpers
    def _any_of(self, checks: list[bool]) -> bool:
        """OR logic - return True if any check is True"""
        return any(checks)

    def _all_of(self, checks: list[bool]) -> bool:
        """AND logic - return True if all checks are True"""
        return all(checks)

    def _none_of(self, checks: list[bool]) -> bool:
        """NOT OR logic - return True if no checks are True"""
        return not any(checks)

    # Time helpers
    def _time_between(self, start_hour: int, end_hour: int) -> bool:
        """Check if current time is between start and end hours (inclusive)"""
        hour = self.model.clock.hour
        if start_hour <= end_hour:
            return start_hour <= hour <= end_hour
        else:  # Wraps around midnight (e.g., 22:00 to 06:00)
            return hour >= start_hour or hour <= end_hour

    def _is_daytime(self) -> bool:
        """Check if it's daytime (6:00 to 20:00)"""
        return self._time_between(6, 20)

    def _is_nighttime(self) -> bool:
        """Check if it's nighttime (20:00 to 6:00)"""
        return not self._is_daytime()

    # ========== End Helper Functions ==========

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
            # Create limited scope with safe variables and helper functions
            scope = {
                "hour": hour,
                "minute": minute,
                "time": hour + minute / 60.0,
                "model": model,
                # Safe builtins
                "abs": abs,
                "min": min,
                "max": max,
                "len": len,
                # Helper functions
                "is_active": self._is_active,
                "is_inactive": self._is_inactive,
                "is_occupied": self._is_occupied,
                "is_free": self._is_free,
                "is_reserved": self._is_reserved,
                "is_straight": self._is_straight,
                "is_turnout": self._is_turnout,
                "is_left": self._is_left,
                "is_right": self._is_right,
                "is_red": self._is_red,
                "is_green": self._is_green,
                "is_yellow": self._is_yellow,
                "is_white": self._is_white,
                "is_moving": self._is_moving,
                "is_stopped": self._is_stopped,
                "is_forward": self._is_forward,
                "is_reverse": self._is_reverse,
                "speed_above": self._speed_above,
                "speed_below": self._speed_below,
                "speed_between": self._speed_between,
                "is_locked": self._is_locked,
                "is_unlocked": self._is_unlocked,
                "is_on": self._is_on,
                "is_off": self._is_off,
                "count_occupied": self._count_occupied,
                "count_active": self._count_active,
                "count_moving": self._count_moving,
                "any_moving": self._any_moving,
                "all_stopped": self._all_stopped,
                "loco_in_block": self._loco_in_block,
                "block_has_loco": self._block_has_loco,
                "any_of": self._any_of,
                "all_of": self._all_of,
                "none_of": self._none_of,
                "time_between": self._time_between,
                "is_daytime": self._is_daytime,
                "is_nighttime": self._is_nighttime,
            }
            # Evaluate expression in restricted scope
            result = eval(condition, {"__builtins__": {}}, scope)
            return bool(result)
        except Exception as e:
            logger.warning(f"Condition evaluation failed: {condition} - Error: {e}")
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
                        # Helper functions
                        "is_active": self._is_active,
                        "is_inactive": self._is_inactive,
                        "is_occupied": self._is_occupied,
                        "is_free": self._is_free,
                        "is_reserved": self._is_reserved,
                        "is_straight": self._is_straight,
                        "is_turnout": self._is_turnout,
                        "is_left": self._is_left,
                        "is_right": self._is_right,
                        "is_red": self._is_red,
                        "is_green": self._is_green,
                        "is_yellow": self._is_yellow,
                        "is_white": self._is_white,
                        "is_moving": self._is_moving,
                        "is_stopped": self._is_stopped,
                        "is_forward": self._is_forward,
                        "is_reverse": self._is_reverse,
                        "speed_above": self._speed_above,
                        "speed_below": self._speed_below,
                        "speed_between": self._speed_between,
                        "is_locked": self._is_locked,
                        "is_unlocked": self._is_unlocked,
                        "is_on": self._is_on,
                        "is_off": self._is_off,
                        "count_occupied": self._count_occupied,
                        "count_active": self._count_active,
                        "count_moving": self._count_moving,
                        "any_moving": self._any_moving,
                        "all_stopped": self._all_stopped,
                        "loco_in_block": self._loco_in_block,
                        "block_has_loco": self._block_has_loco,
                        "any_of": self._any_of,
                        "all_of": self._all_of,
                        "none_of": self._none_of,
                        "time_between": self._time_between,
                        "is_daytime": self._is_daytime,
                        "is_nighttime": self._is_nighttime,
                    }
                    result = eval(ac.condition, {"__builtins__": {}}, scope)
                    if not result:
                        continue
                except Exception as e:
                    logger.warning(f"Event condition evaluation failed: {ac.condition} - Error: {e}")
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
                                logger.error(f"Error callback failed: {repr(callback_err)}")
                        else:
                            # Only print if no callback registered
                            logger.error(f"Action '{action.name if action else 'unknown'}' failed: {repr(exp)}")
                    else:
                        # Action succeeded
                        result = future.result()
                        if action and action.on_success:
                            try:
                                action.on_success(result, elapsed)
                            except Exception as callback_err:
                                logger.error(f"Success callback failed: {repr(callback_err)}")
                    continue

                # Check timeout
                elapsed = time.monotonic() - start_time
                if elapsed > timeout:
                    future.cancel()
                    if action and action.on_error:
                        try:
                            action.on_error(TimeoutError(f"Timeout after {elapsed:.1f}s"), elapsed)
                        except Exception as callback_err:
                            logger.error(f"Error callback failed: {repr(callback_err)}")
                    else:
                        # Only print if no callback registered
                        logger.warning(f"Action '{action.name if action else 'unknown'}' timeout after {elapsed:.1f}s (limit: {timeout}s)")
                    continue

                # Still running, put back in queue
                self.__threads.append((future, timeout, start_time, action) if action else (future, timeout, start_time))
