import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


@dataclass
class ScheduleEntry:
    """Schedule entry (stop/waypoint)"""
    block: str = ""  # Block ID
    hour: int = 0  # Departure hour
    minute: int = 0  # Departure minute
    ahour: int = 0  # Arrival hour
    aminute: int = 0  # Arrival minute
    minwait: int = 0  # Minimum wait time
    regularstop: bool = True  # Regular stop flag
    swap: bool = False  # Swap direction
    free2go: bool = False  # Free to go flag
    blockexitside: int = 0  # Block exit side
    indelay: int = 0  # In delay
    departspeed: int = 0  # Departure speed


class Schedule:
    """Schedule/Timetable object

    Represents a train schedule/timetable with entries for each block stop.
    Controls automated train operations based on time.

    Note: Commands not yet documented in official XMLScript reference.
    Implementation based on plan structure and likely control methods.
    """

    def __init__(self, sc_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com

        # Schedule configuration
        self.trainid = ""  # Assigned train/operator ID
        self.group = ""  # Schedule group
        self.class_ = ""  # Train class (using class_ to avoid Python keyword)
        self.timeframe = 1  # Time frame mode
        self.timeprocessing = 1  # Time processing mode
        self.fromhour = 0  # Active from hour
        self.tohour = 0  # Active to hour
        self.cycles = 0  # Number of cycles (0=infinite)
        self.maxdelay = 60  # Maximum delay in minutes
        self.weekdays = 127  # Active weekdays (bitfield: Mon=1, Tue=2, etc.)
        self.followuponenter = False  # Follow up on enter
        self.recordtime = False  # Record time flag

        # Schedule entries (stops)
        self.entries: list[ScheduleEntry] = []

        self.build(sc_xml)

    def build(self, sc_xml: ET.Element):
        """Build schedule object from XML element"""
        self.idx = sc_xml.attrib['id']

        for attr, value in sc_xml.attrib.items():
            # Handle 'class' attribute specially (Python keyword)
            if attr == 'class':
                set_attr(self, 'class_', value)
            else:
                set_attr(self, attr, value)

        # Parse schedule entries
        for child in sc_xml:
            if child.tag == 'scentry':
                entry = ScheduleEntry(
                    block=child.attrib.get('block', ''),
                    hour=int(child.attrib.get('hour', '0')),
                    minute=int(child.attrib.get('minute', '0')),
                    ahour=int(child.attrib.get('ahour', '0')),
                    aminute=int(child.attrib.get('aminute', '0')),
                    minwait=int(child.attrib.get('minwait', '0')),
                    regularstop=child.attrib.get('regularstop', 'true').lower() == 'true',
                    swap=child.attrib.get('swap', 'false').lower() == 'true',
                    free2go=child.attrib.get('free2go', 'false').lower() == 'true',
                    blockexitside=int(child.attrib.get('blockexitside', '0')),
                    indelay=int(child.attrib.get('indelay', '0')),
                    departspeed=int(child.attrib.get('departspeed', '0'))
                )
                self.entries.append(entry)

    # Note: The following commands are NOT verified in XMLScript documentation
    # They are implemented based on expected functionality but may not work
    # until confirmed with real Rocrail server or documentation

    def start(self):
        """Start the schedule (UNVERIFIED COMMAND)

        WARNING: This command is not documented in official XMLScript reference.
        It may not work with actual Rocrail servers.
        """
        cmd = f'<sc id="{self.idx}" cmd="start"/>'
        self.communicator.send("sc", cmd)

    def stop(self):
        """Stop the schedule (UNVERIFIED COMMAND)

        WARNING: This command is not documented in official XMLScript reference.
        It may not work with actual Rocrail servers.
        """
        cmd = f'<sc id="{self.idx}" cmd="stop"/>'
        self.communicator.send("sc", cmd)

    def reset(self):
        """Reset the schedule to beginning (UNVERIFIED COMMAND)

        WARNING: This command is not documented in official XMLScript reference.
        It may not work with actual Rocrail servers.
        """
        cmd = f'<sc id="{self.idx}" cmd="reset"/>'
        self.communicator.send("sc", cmd)
