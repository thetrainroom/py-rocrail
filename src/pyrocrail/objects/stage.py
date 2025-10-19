import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Stage:
    """Staging yard block object

    Represents a staging yard (fiddle yard) for train storage and management.
    Supports automatic train compression and expansion operations.

    Commands verified against Rocrail wiki documentation.
    """

    def __init__(self, sb_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com

        # State attributes
        self.entering = False  # Train entering
        self.allowchgdir = False  # Allow direction change
        self.reserved = False  # Reserved state
        self.state = "open"  # open, closed, etc.
        self.totallength = 0  # Total length of trains
        self.totalsections = 0  # Number of occupied sections

        # Configuration
        self.prev_id = ""  # Previous stage ID
        self.desc = ""  # Description
        self.slen = 30  # Section length
        self.gap = 5  # Gap between trains

        # Sensors and signals
        self.fbenterid = ""  # Enter feedback sensor ID
        self.entersignal = ""  # Enter signal ID
        self.exitsignal = ""  # Exit signal ID

        # Timing and randomization
        self.randomrate = 10  # Random departure rate
        self.departdelay = 0  # Departure delay
        self.waitmode = "random"  # Wait mode (random, min, max, fixed)
        self.minwaittime = 1  # Minimum wait time (minutes)
        self.maxwaittime = 30  # Maximum wait time (minutes)
        self.waittime = 1  # Fixed wait time (minutes)

        # Occupancy control
        self.minocc = 0  # Minimum occupied sections
        self.minoccsec = 0  # Minimum occupied sections (electrical)

        # Speed settings
        self.exitspeed = "cruise"  # Exit speed (cruise, min, mid, max, percent)
        self.stopspeed = "min"  # Stop speed
        self.speedpercent = 10  # Speed percentage
        self.exitspeedpercent = 80  # Exit speed percentage

        # Flags
        self.suitswell = False  # Suits well (for route selection)
        self.inatlen = False  # Include in automatic train length calculation
        self.usewd = True  # Use watchdog
        self.wdsleep = 1  # Watchdog sleep time (seconds)
        self.movetimeout = 0  # Move timeout
        self.electrified = False  # Electrified track
        self.smallsymbol = False  # Small symbol display
        self.stopspeedtolastsection = False  # Apply stop speed to last section
        self.vmintofirstsection = False  # Apply minimum speed to first section

        # Classification
        self.typeperm = ""  # Type permission
        self.era = 0  # Era
        self.class_ = ""  # Class (using class_ to avoid Python keyword)
        self.maxlen = 0  # Maximum train length
        self.minlen = 0  # Minimum train length

        # Position
        self.x = 0
        self.y = 0
        self.z = 0

        self.build(sb_xml)

    def build(self, sb_xml: ET.Element):
        """Build stage object from XML element"""
        self.idx = sb_xml.attrib["id"]

        for attr, value in sb_xml.attrib.items():
            # Handle 'class' attribute specially (Python keyword)
            if attr == "class":
                set_attr(self, "class_", value)
            else:
                set_attr(self, attr, value)

    # Commands based on Rocrail wiki documentation

    def compress(self):
        """Compress staging yard - advance trains to fill gaps

        Moves occupying trains towards the end section to fill up gaps
        and make room at the start. Triggered automatically by watchdog
        if auto mode is enabled.
        """
        cmd = f'<sb id="{self.idx}" cmd="compress"/>'
        self.communicator.send("sb", cmd)

    def expand(self):
        """Expand staging yard - activate train in end section

        Turns on the auto mode of the train waiting in the end section
        if the exit state is open.
        """
        cmd = f'<sb id="{self.idx}" cmd="expand"/>'
        self.communicator.send("sb", cmd)

    # State control commands (similar to Block)

    def open(self):
        """Open staging block for entry"""
        cmd = f'<sb id="{self.idx}" cmd="open"/>'
        self.communicator.send("sb", cmd)
        self.state = "open"

    def close(self):
        """Close staging block (no entry)"""
        cmd = f'<sb id="{self.idx}" cmd="close"/>'
        self.communicator.send("sb", cmd)
        self.state = "closed"

    def free(self):
        """Free the staging block"""
        cmd = f'<sb id="{self.idx}" cmd="free"/>'
        self.communicator.send("sb", cmd)
        self.reserved = False

    def go(self):
        """Give go permission to train in staging block"""
        cmd = f'<sb id="{self.idx}" cmd="go"/>'
        self.communicator.send("sb", cmd)
