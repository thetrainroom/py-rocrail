import xml.etree.ElementTree as ET
from enum import Enum
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class SignalAspect(Enum):
    """Signal aspect/color enum for type-safe signal state management"""

    RED = "red"  # Stop
    GREEN = "green"  # Go/Clear
    YELLOW = "yellow"  # Caution/Approach
    WHITE = "white"  # Shunt/Restricted speed

    def __str__(self) -> str:
        """Return string value for XML serialization"""
        return self.value


class Signal:
    def __init__(self, sg_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com

        # State attributes
        self.state = SignalAspect.RED  # Current aspect enum
        self.aspect = 0  # Numeric aspect value
        self.cmd = ""  # Last command

        # Configuration attributes
        self.addr = 0  # Signal address
        self.port = 0  # Signal port
        self.gate = 0  # Gate timing
        self.type = "light"  # Signal type: light, semaphore, dwarf
        self.aspects = 2  # Number of aspects (2, 3, 4)
        self.dwarf = False  # Dwarf signal flag
        self.distant = False  # Distant signal flag

        self.build(sg_xml)

    def build(self, sg_xml: ET.Element):
        self.idx = sg_xml.attrib["id"]
        for attr, value in sg_xml.attrib.items():
            # Convert state string to enum
            if attr == "state":
                try:
                    self.state = SignalAspect(value)
                except ValueError:
                    # Fallback for unknown states
                    self.state = SignalAspect.RED
            else:
                set_attr(self, attr, value)

    def red(self):
        """Set signal to red (stop)"""
        cmd = f'<sg id="{self.idx}" cmd="red"/>'
        self.communicator.send("sg", cmd)
        self.state = SignalAspect.RED
        self.aspect = 0

    def green(self):
        """Set signal to green (go)"""
        cmd = f'<sg id="{self.idx}" cmd="green"/>'
        self.communicator.send("sg", cmd)
        self.state = SignalAspect.GREEN
        self.aspect = 1

    def yellow(self):
        """Set signal to yellow (caution)"""
        cmd = f'<sg id="{self.idx}" cmd="yellow"/>'
        self.communicator.send("sg", cmd)
        self.state = SignalAspect.YELLOW
        self.aspect = 2

    def white(self):
        """Set signal to white (shunt)"""
        cmd = f'<sg id="{self.idx}" cmd="white"/>'
        self.communicator.send("sg", cmd)
        self.state = SignalAspect.WHITE
        self.aspect = 3

    def set_aspect(self, aspect):
        """Set signal to specific aspect

        Args:
            aspect: Can be int (0-3), string ("red", "green", etc.), or SignalAspect enum
        """
        if isinstance(aspect, SignalAspect):
            # Direct enum usage
            aspect_method_map = {
                SignalAspect.RED: self.red,
                SignalAspect.GREEN: self.green,
                SignalAspect.YELLOW: self.yellow,
                SignalAspect.WHITE: self.white,
            }
            aspect_method_map[aspect]()
        elif isinstance(aspect, int):
            aspect_map = {0: "red", 1: "green", 2: "yellow", 3: "white"}
            if aspect in aspect_map:
                getattr(self, aspect_map[aspect])()
            else:
                raise ValueError(f"Invalid aspect number: {aspect}")
        elif isinstance(aspect, str):
            aspect_lower = aspect.lower()
            if aspect_lower in ["red", "stop"]:
                self.red()
            elif aspect_lower in ["green", "go", "clear"]:
                self.green()
            elif aspect_lower in ["yellow", "caution", "approach"]:
                self.yellow()
            elif aspect_lower in ["white", "shunt"]:
                self.white()
            else:
                raise ValueError(f"Invalid aspect name: {aspect}")

    def next_aspect(self):
        """Cycle to next aspect"""
        # Map enum to index
        aspect_order = [SignalAspect.RED, SignalAspect.GREEN, SignalAspect.YELLOW, SignalAspect.WHITE]
        try:
            current_index = aspect_order.index(self.state)
            next_index = (current_index + 1) % min(self.aspects, len(aspect_order))
            self.set_aspect(next_index)
        except ValueError:
            self.red()  # Default to red if current state unknown

    def auto(self):
        """Set signal to automatic mode"""
        # TODO: Verify auto command format
        cmd = f'<sg id="{self.idx}" cmd="auto"/>'
        self.communicator.send("sg", cmd)

    def manual(self):
        """Set signal to manual mode"""
        # TODO: Verify manual command format
        cmd = f'<sg id="{self.idx}" cmd="manual"/>'
        self.communicator.send("sg", cmd)

    def aspect_number(self, aspect_num: int):
        """Set signal to specific numbered aspect (0-31)

        Args:
            aspect_num: Aspect number (0-31) for complex signals
        """
        if not 0 <= aspect_num <= 31:
            raise ValueError(f"Aspect number must be 0-31, got {aspect_num}")
        cmd = f'<sg id="{self.idx}" cmd="aspect{aspect_num}"/>'
        self.communicator.send("sg", cmd)
        self.aspect = aspect_num

    def blank(self):
        """Blank the signal (turn off all lights)"""
        cmd = f'<sg id="{self.idx}" cmd="blank"/>'
        self.communicator.send("sg", cmd)
