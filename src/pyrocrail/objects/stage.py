import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Section:
    """Staging block section

    Represents an individual section (track) within a staging yard.
    Each section can hold one train and has its own feedback sensor.
    """

    def __init__(self, section_xml: ET.Element):
        self.idx = ""  # Section ID (e.g., "T0_0")
        self.fbid = ""  # Feedback sensor ID
        self.fbidocc = ""  # Occupancy feedback sensor ID
        self.nr = 0  # Section number
        self.len = 0  # Section length
        self.lcid = ""  # Locomotive ID currently in section

        self.build(section_xml)

    def build(self, section_xml: ET.Element):
        """Build section from XML element"""
        # Save the section ID first (it's in the "id" attribute)
        section_id = section_xml.attrib.get("id", "")

        # Process all attributes
        for attr, value in section_xml.attrib.items():
            # Skip "id" attribute as we handle it specially
            if attr == "id":
                continue
            set_attr(self, attr, value)

        # Set idx to the section ID (not the numeric idx attribute)
        self.idx = section_id

    def is_occupied(self) -> bool:
        """Check if section has a locomotive"""
        return bool(self.lcid)


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

        # Sections
        self.sections = []  # List of Section objects

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

        # Parse section child elements
        self.sections = []
        for section_el in sb_xml.findall("section"):
            section = Section(section_el)
            self.sections.append(section)

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

    # Section query methods

    def get_section(self, section_id: str) -> Section | None:
        """Get section by ID

        Args:
            section_id: Section ID (e.g., "T0_0")

        Returns:
            Section object or None if not found
        """
        for section in self.sections:
            if section.idx == section_id:
                return section
        return None

    def get_section_by_number(self, nr: int) -> Section | None:
        """Get section by number

        Args:
            nr: Section number (0-indexed)

        Returns:
            Section object or None if not found
        """
        for section in self.sections:
            if section.nr == nr:
                return section
        return None

    def get_occupied_sections(self) -> list[Section]:
        """Get all occupied sections

        Returns:
            List of sections with locomotives
        """
        return [s for s in self.sections if s.is_occupied()]

    def get_free_sections(self) -> list[Section]:
        """Get all free sections

        Returns:
            List of sections without locomotives
        """
        return [s for s in self.sections if not s.is_occupied()]

    def get_section_count(self) -> int:
        """Get total number of sections

        Returns:
            Number of sections in staging yard
        """
        return len(self.sections)

    def get_locomotives_in_staging(self) -> list[str]:
        """Get list of locomotive IDs in staging yard

        Returns:
            List of locomotive IDs currently in any section
        """
        loco_ids = []
        for section in self.sections:
            if section.lcid:
                loco_ids.append(section.lcid)
        return loco_ids

    def get_front_locomotive(self) -> str | None:
        """Get locomotive at front/entry of staging yard

        Returns the locomotive in the lowest numbered section (section 0
        or first occupied section). This is the train that entered first.

        Returns:
            Locomotive ID or None if staging is empty
        """
        # Sort sections by number
        sorted_sections = sorted(self.sections, key=lambda s: s.nr)

        # Find first occupied section
        for section in sorted_sections:
            if section.is_occupied():
                return section.lcid

        return None

    def get_exit_locomotive(self) -> str | None:
        """Get locomotive ready to depart (at exit)

        Returns the locomotive in the highest numbered section. This is
        the train that will depart next when expand() or go() is called.

        Returns:
            Locomotive ID or None if staging is empty
        """
        # Sort sections by number (descending)
        sorted_sections = sorted(self.sections, key=lambda s: s.nr, reverse=True)

        # Find first occupied section from the exit end
        for section in sorted_sections:
            if section.is_occupied():
                return section.lcid

        return None

    def get_exit_section(self) -> Section | None:
        """Get the exit section (highest numbered section)

        Returns:
            Exit section or None if no sections
        """
        if not self.sections:
            return None

        return max(self.sections, key=lambda s: s.nr)

    def get_entry_section(self) -> Section | None:
        """Get the entry section (section 0)

        Returns:
            Entry section or None if no sections
        """
        return self.get_section_by_number(0)
