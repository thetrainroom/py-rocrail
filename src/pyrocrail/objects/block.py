import xml.etree.ElementTree as ET
from enum import Enum
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class BlockState(Enum):
    """Block state enum for type-safe state management"""

    OPEN = "open"
    CLOSED = "closed"
    FREE = "free"
    RESERVED = "reserved"

    def __str__(self) -> str:
        """Return string value for XML serialization"""
        return self.value


class Block:
    def __init__(self, bk_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com

        # State attributes
        self.state = BlockState.FREE  # Block state enum
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
            # Convert state string to enum
            if attr == "state":
                try:
                    self.state = BlockState(value)
                except ValueError:
                    # Fallback for unknown states
                    self.state = BlockState.FREE
            else:
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
        self.state = BlockState.RESERVED

    def free(self):
        """Free the block"""
        cmd = f'<bk id="{self.idx}" cmd="free"/>'
        self.communicator.send("bk", cmd)
        self.reserved = False
        self.occ = False
        self.locid = ""
        self.state = BlockState.FREE

    def stop(self):
        """Stop locomotive in block"""
        cmd = f'<bk id="{self.idx}" cmd="stop"/>'
        self.communicator.send("bk", cmd)

    def close(self):
        """Close the block (no entry allowed)"""
        cmd = f'<bk id="{self.idx}" state="{BlockState.CLOSED.value}"/>'
        self.communicator.send("bk", cmd)
        # Don't update state immediately - wait for server response
        # self.state = BlockState.CLOSED

    def open(self):
        """Open the block (allow entry)"""
        cmd = f'<bk id="{self.idx}" state="{BlockState.OPEN.value}"/>'
        self.communicator.send("bk", cmd)
        # Don't update state immediately - wait for server response
        # if not self.occ and not self.reserved:
        #     self.state = BlockState.FREE

    def accept_ident(self):
        """Accept locomotive identification"""
        # TODO: Verify accept ident command format
        cmd = f'<bk id="{self.idx}" cmd="acceptident"/>'
        self.communicator.send("bk", cmd)

    def is_free(self) -> bool:
        """Check if block is free (not occupied, not reserved, not closed)"""
        return not self.is_occupied() and not self.reserved and self.state != BlockState.CLOSED

    def is_occupied(self) -> bool:
        """Check if block is occupied

        A block is considered occupied if either:
        - The occ (occupied) flag is True
        - OR a locomotive ID (locid) is assigned to the block
        """
        return self.occ or bool(self.locid)

    def is_reserved(self) -> bool:
        """Check if block is reserved"""
        return self.reserved

    def is_closed(self) -> bool:
        """Check if block is closed"""
        return self.state == BlockState.CLOSED

    def get_locomotive(self) -> str:
        """Get ID of locomotive in block"""
        return self.locid
