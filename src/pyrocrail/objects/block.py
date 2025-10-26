import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Block:
    def __init__(self, bk_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com

        # State attributes
        self.state = "free"  # Block state: free, occupied, reserved, closed
        self.occ = False  # Occupied flag
        self.reserved = False  # Reserved flag
        self.locid = ""  # Locomotive ID currently in block
        self.td = False  # Train detection

        # Configuration attributes
        self.len = 0  # Block length in mm
        self.speed = 0  # Block speed limit
        self.incline = 0  # Block incline
        self.fbenter = ""  # Enter feedback sensor ID
        self.fbexit = ""  # Exit feedback sensor ID
        self.signal = ""  # Signal ID
        self.wsignal = ""  # White signal ID
        self.electrified = True  # Electrified track
        self.type = "none"  # Block type
        self.commuter = False  # Commuter block
        self.wait = 0  # Wait time

        self.build(bk_xml)

    def build(self, bk_xml: ET.Element):
        self.idx = bk_xml.attrib["id"]
        for attr, value in bk_xml.attrib.items():
            set_attr(self, attr, value)

    def reserve(self, loco_id: str = ""):
        """Reserve the block for a locomotive"""
        if loco_id:
            cmd = f'<bk id="{self.idx}" cmd="reserve" locid="{loco_id}"/>'
            self.locid = loco_id
        else:
            cmd = f'<bk id="{self.idx}" cmd="reserve"/>'
        self.communicator.send("bk", cmd)
        self.reserved = True
        self.state = "reserved"

    def free(self):
        """Free the block"""
        cmd = f'<bk id="{self.idx}" cmd="free"/>'
        self.communicator.send("bk", cmd)
        self.reserved = False
        self.occ = False
        self.locid = ""
        self.state = "free"

    def stop(self):
        """Stop locomotive in block"""
        cmd = f'<bk id="{self.idx}" cmd="stop"/>'
        self.communicator.send("bk", cmd)

    def close(self):
        """Close the block (no entry allowed)"""
        cmd = f'<bk id="{self.idx}" state="closed"/>'
        self.communicator.send("bk", cmd)
        # Don't update state immediately - wait for server response
        # self.state = "closed"

    def open(self):
        """Open the block (allow entry)"""
        cmd = f'<bk id="{self.idx}" state="open"/>'
        self.communicator.send("bk", cmd)
        # Don't update state immediately - wait for server response
        # if not self.occ and not self.reserved:
        #     self.state = "free"

    def accept_ident(self):
        """Accept locomotive identification"""
        # TODO: Verify accept ident command format
        cmd = f'<bk id="{self.idx}" cmd="acceptident"/>'
        self.communicator.send("bk", cmd)

    def is_free(self) -> bool:
        """Check if block is free"""
        return self.state == "free" and not self.occ and not self.reserved

    def is_occupied(self) -> bool:
        """Check if block is occupied"""
        return self.occ

    def is_reserved(self) -> bool:
        """Check if block is reserved"""
        return self.reserved

    def is_closed(self) -> bool:
        """Check if block is closed"""
        return self.state == "closed"

    def get_locomotive(self) -> str:
        """Get ID of locomotive in block"""
        return self.locid
