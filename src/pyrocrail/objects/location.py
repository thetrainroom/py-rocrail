import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Location:
    """Location object for geographic tracking and flow management

    Locations represent geographic points on the layout like cities, stations,
    or regions. They provide sophisticated train flow management for hidden yards
    and scheduling through occupancy control.

    Key Features:
    - Minimal occupancy: Controls minimum number of trains in location (min_occ)
    - Maximal occupancy: Limits total trains allowed in location
    - FIFO (First In, First Out): Controls train departure order
    - Scheduling: Generates timetables and manages train assignments
    - Flow management: Automatic traffic control for hidden yards

    See: https://wiki.rocrail.net/doku.php?id=locations-details-en
    """

    def __init__(self, location_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com

        # Occupancy control attributes (set in plan, read-only at runtime)
        self.minocc = 0  # Minimal occupancy - trains must remain in location
        self.maxocc = 0  # Maximal occupancy - maximum trains allowed
        self.fifo = False  # First-in-first-out departure order
        self.random = False  # Random train selection for departure

        # Scheduling attributes
        self.scheduleid = ""  # Associated schedule ID
        self.trains = False  # Only assigned train locomotives allowed

        self.build(location_xml)

    def build(self, location: ET.Element):
        self.idx = location.attrib["id"]
        for attr, value in location.attrib.items():
            if attr == "id":
                continue
            set_attr(self, attr, value)

    def info(self, svalue: str | None = None) -> None:
        """Set or query location information

        Args:
            svalue: Optional string value to set (e.g., a text display ID)
        """
        if svalue:
            cmd = f'<location id="{self.idx}" cmd="info" svalue="{svalue}"/>'
        else:
            cmd = f'<location id="{self.idx}" cmd="info"/>'
        self.communicator.send("location", cmd)
