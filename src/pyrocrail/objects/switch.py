import xml.etree.ElementTree as ET
from enum import Enum
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class SwitchPosition(Enum):
    """Switch position enum for type-safe switch state management"""

    STRAIGHT = "straight"
    TURNOUT = "turnout"
    LEFT = "left"  # For 3-way switches
    RIGHT = "right"  # For 3-way switches

    def __str__(self) -> str:
        """Return string value for XML serialization"""
        return self.value


class Switch:
    def __init__(self, sw_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com

        # State attributes
        self.state = SwitchPosition.STRAIGHT  # Current position enum
        self.switched = False  # Switch state
        self.cmd = ""  # Last command

        # Configuration attributes
        self.addr1 = 0  # Primary address
        self.addr2 = 0  # Secondary address (for 3-way switches)
        self.port1 = 0  # Primary port
        self.port2 = 0  # Secondary port
        self.gate1 = 0  # Gate 1 timing
        self.gate2 = 0  # Gate 2 timing
        self.type = "default"  # Switch type
        self.delay = 0  # Switch delay
        self.motor = False  # Motor type switch
        self.accessory = False  # Accessory decoder

        self.build(sw_xml)

    def build(self, sw_xml: ET.Element):
        self.idx = sw_xml.attrib["id"]
        for attr, value in sw_xml.attrib.items():
            # Convert state string to enum
            if attr == "state":
                try:
                    self.state = SwitchPosition(value)
                except ValueError:
                    # Fallback for unknown states
                    self.state = SwitchPosition.STRAIGHT
            else:
                set_attr(self, attr, value)

    def straight(self):
        """Set switch to straight position"""
        cmd = f'<sw id="{self.idx}" cmd="straight"/>'
        self.communicator.send("sw", cmd)
        self.state = SwitchPosition.STRAIGHT
        self.switched = False

    def turnout(self):
        """Set switch to turnout position"""
        cmd = f'<sw id="{self.idx}" cmd="turnout"/>'
        self.communicator.send("sw", cmd)
        self.state = SwitchPosition.TURNOUT
        self.switched = True

    def flip(self):
        """Flip switch to opposite position"""
        cmd = f'<sw id="{self.idx}" cmd="flip"/>'
        self.communicator.send("sw", cmd)
        self.switched = not self.switched
        self.state = SwitchPosition.TURNOUT if self.switched else SwitchPosition.STRAIGHT

    def set_state(self, state):
        """Set switch to specific state

        Args:
            state: Can be str, int, or SwitchPosition enum
        """
        if isinstance(state, SwitchPosition):
            # Direct enum usage
            state_method_map = {
                SwitchPosition.STRAIGHT: self.straight,
                SwitchPosition.TURNOUT: self.turnout,
                SwitchPosition.LEFT: self.left,
                SwitchPosition.RIGHT: self.right,
            }
            if state in state_method_map:
                state_method_map[state]()
            else:
                raise ValueError(f"Invalid switch state: {state}")
        elif isinstance(state, str):
            if state.lower() in ["straight", "0", "green"]:
                self.straight()
            elif state.lower() in ["turnout", "1", "red"]:
                self.turnout()
            elif state.lower() == "left":
                self.left()
            elif state.lower() == "right":
                self.right()
            else:
                raise ValueError(f"Invalid switch state: {state}")
        else:
            raise ValueError(f"Invalid switch state type: {type(state)}")

    def lock(self):
        """Lock switch in current position"""
        # TODO: Verify lock command format
        cmd = f'<sw id="{self.idx}" cmd="lock"/>'
        self.communicator.send("sw", cmd)

    def unlock(self):
        """Unlock switch"""
        # TODO: Verify unlock command format
        cmd = f'<sw id="{self.idx}" cmd="unlock"/>'
        self.communicator.send("sw", cmd)

    def left(self):
        """Set switch to left position (for 3-way or double-slip switches)"""
        cmd = f'<sw id="{self.idx}" cmd="left"/>'
        self.communicator.send("sw", cmd)
        self.state = SwitchPosition.LEFT

    def right(self):
        """Set switch to right position (for 3-way or double-slip switches)"""
        cmd = f'<sw id="{self.idx}" cmd="right"/>'
        self.communicator.send("sw", cmd)
        self.state = SwitchPosition.RIGHT


class ThreeWaySwitch(Switch):
    """Three-way switch implementation"""

    def __init__(self, sw_xml: ET.Element, com: Communicator):
        super().__init__(sw_xml, com)
        self.state = "left"  # left, right, straight

    def left(self):
        """Set to left position"""
        # TODO: Verify 3-way switch command format
        cmd = f'<sw id="{self.idx}" cmd="left"/>'
        self.communicator.send("sw", cmd)
        self.state = "left"

    def right(self):
        """Set to right position"""
        # TODO: Verify 3-way switch command format
        cmd = f'<sw id="{self.idx}" cmd="right"/>'
        self.communicator.send("sw", cmd)
        self.state = "right"

    def straight(self):
        """Set to straight position"""
        cmd = f'<sw id="{self.idx}" cmd="straight"/>'
        self.communicator.send("sw", cmd)
        self.state = "straight"
