import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Locomotive:
    def __init__(self, lc_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com

        # State attributes
        self.V = 0  # Current speed
        self.dir = True  # Direction (True = forward, False = reverse)
        self.lights = False  # Main lights state
        self.fn = {}  # Function states (key = function number, value = state)
        self.placing = False  # Placing mode
        self.active = False  # Active state
        self.throttleid = ""  # Throttle ID
        self.train = ""  # Train ID
        self.mode = "idle"  # Operating mode

        # Configuration attributes
        self.addr = 0  # DCC address
        self.V_max = 100  # Maximum speed
        self.V_min = 0  # Minimum speed
        self.V_mid = 50  # Mid speed
        self.mass = 0  # Mass for physics
        self.length = 0  # Length in mm

        self.build(lc_xml)

    def build(self, lc_xml: ET.Element):
        self.idx = lc_xml.attrib["id"]
        for attr, value in lc_xml.attrib.items():
            set_attr(self, attr, value)

        # TODO: Parse function definitions from XML
        # TODO: Parse CV values if present

    def set_speed(self, speed: int):
        """Set locomotive speed (0-100)"""
        # TODO: Verify speed range and scaling
        speed = max(0, min(100, speed))
        cmd = f'<lc id="{self.idx}" V="{speed}"/>'
        self.communicator.send("lc", cmd)
        self.V = speed

    def set_direction(self, forward: bool):
        """Set locomotive direction"""
        dir_str = "true" if forward else "false"
        cmd = f'<lc id="{self.idx}" dir="{dir_str}"/>'
        self.communicator.send("lc", cmd)
        self.dir = forward

    def stop(self):
        """Emergency stop"""
        cmd = f'<lc id="{self.idx}" V="0"/>'
        self.communicator.send("lc", cmd)
        self.V = 0

    def set_lights(self, on: bool):
        """Set main lights on/off"""
        lights_str = "true" if on else "false"
        cmd = f'<lc id="{self.idx}" lights="{lights_str}"/>'
        self.communicator.send("lc", cmd)
        self.lights = on

    def set_function(self, fn_num: int, state: bool):
        """Set function state"""
        # TODO: Verify function command format
        state_str = "true" if state else "false"
        cmd = f'<lc id="{self.idx}" fn="{fn_num}" fnstate="{state_str}"/>'
        self.communicator.send("lc", cmd)
        if not hasattr(self, "fn") or not isinstance(self.fn, dict):
            self.fn = {}
        self.fn[fn_num] = state

    def go_forward(self, speed: int = None):
        """Move forward at specified speed"""
        self.set_direction(True)
        if speed is not None:
            self.set_speed(speed)

    def go_reverse(self, speed: int = None):
        """Move reverse at specified speed"""
        self.set_direction(False)
        if speed is not None:
            self.set_speed(speed)

    def dispatch(self):
        """Dispatch locomotive for automatic control"""
        # TODO: Verify dispatch command format
        cmd = f'<lc id="{self.idx}" cmd="dispatch"/>'
        self.communicator.send("lc", cmd)

    def collect(self):
        """Collect locomotive from automatic control"""
        # TODO: Verify collect command format
        cmd = f'<lc id="{self.idx}" cmd="collect"/>'
        self.communicator.send("lc", cmd)

    def shortcut(self):
        """Handle short circuit event"""
        # TODO: Verify shortcut command format
        cmd = f'<lc id="{self.idx}" cmd="shortcut"/>'
        self.communicator.send("lc", cmd)

    def regularreset(self):
        """Regular reset - removes assigned schedule"""
        cmd = f'<lc id="{self.idx}" cmd="regularreset"/>'
        self.communicator.send("lc", cmd)

    def softreset(self):
        """Soft reset locomotive"""
        cmd = f'<lc id="{self.idx}" cmd="softreset"/>'
        self.communicator.send("lc", cmd)

    def use_schedule(self, schedule_id: str):
        """Assign schedule to locomotive

        Args:
            schedule_id: Schedule ID to use
        """
        cmd = f'<lc id="{self.idx}" cmd="useschedule" scheduleid="{schedule_id}"/>'
        self.communicator.send("lc", cmd)
