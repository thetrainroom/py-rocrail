import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


@dataclass
class SwitchCommand:
    """Switch command in route"""

    id: str = ""
    cmd: str = "straight"  # straight, turnout, left, right
    lock: bool = False


@dataclass
class OutputCommand:
    """Output command in route"""

    id: str = ""
    cmd: str = "on"  # on, off, flip
    value: int = 0


@dataclass
class Permission:
    """Route permission"""

    id: str = ""  # Locomotive or class ID
    type: str = "include"  # include or exclude


class Route:
    def __init__(self, st_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com

        # State attributes
        self.state = "free"  # Route state: free, locked, set
        self.cmd = ""  # Last command

        # Configuration attributes
        self.bka = ""  # Block A (from)
        self.bkb = ""  # Block B (to)
        self.bkc = ""  # Block C (via)
        self.speed = 0  # Route speed limit
        self.manual = False  # Manual route
        self.countcars = False  # Count cars
        self.swcmd = "flip"  # Switch command type
        self.status = "free"  # Route status

        # TODO: Add support for switch list, output list, permission list
        self.switches = []  # List of switches in route
        self.outputs = []  # List of outputs to control
        self.conditions = []  # List of conditions

        self.build(st_xml)

    def build(self, st_xml: ET.Element):
        self.idx = st_xml.attrib["id"]
        for attr, value in st_xml.attrib.items():
            set_attr(self, attr, value)

        # Parse child elements for switches, outputs, permissions
        for child in st_xml:
            if child.tag == "swcmd":
                # Parse switch command
                sw_cmd = SwitchCommand(id=child.attrib.get("id", ""), cmd=child.attrib.get("cmd", "straight"), lock=child.attrib.get("lock", "false").lower() == "true")
                self.switches.append(sw_cmd)
            elif child.tag == "outcmd":
                # Parse output command
                out_cmd = OutputCommand(id=child.attrib.get("id", ""), cmd=child.attrib.get("cmd", "on"), value=int(child.attrib.get("value", "0")))
                self.outputs.append(out_cmd)
            elif child.tag == "permissionlist":
                # Parse permissions
                for perm_child in child:
                    if perm_child.tag == "permission":
                        perm = Permission(id=perm_child.attrib.get("id", ""), type=perm_child.attrib.get("type", "include"))
                        self.conditions.append(perm)

    def set(self):
        """Set/activate the route"""
        cmd = f'<st id="{self.idx}" cmd="set"/>'
        self.communicator.send("st", cmd)
        self.state = "set"

    def go(self):
        """Alias for set() - activate the route"""
        self.set()

    def lock(self):
        """Lock the route"""
        cmd = f'<st id="{self.idx}" cmd="lock"/>'
        self.communicator.send("st", cmd)
        self.state = "locked"

    def unlock(self):
        """Unlock the route"""
        cmd = f'<st id="{self.idx}" cmd="unlock"/>'
        self.communicator.send("st", cmd)
        self.state = "free"

    def free(self):
        """Free the route"""
        cmd = f'<st id="{self.idx}" cmd="free"/>'
        self.communicator.send("st", cmd)
        self.state = "free"

    def test(self):
        """Test the route without activating"""
        # TODO: Verify test command format
        cmd = f'<st id="{self.idx}" cmd="test"/>'
        self.communicator.send("st", cmd)

    def is_free(self) -> bool:
        """Check if route is free"""
        return self.state == "free"

    def is_locked(self) -> bool:
        """Check if route is locked"""
        return self.state == "locked"

    def is_set(self) -> bool:
        """Check if route is set/active"""
        return self.state == "set"
