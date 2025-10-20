import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Location:
    """Location object for geographic tracking

    Locations represent geographic points on the layout like cities,
    stations, or regions for organization and tracking purposes.
    """

    def __init__(self, location_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com
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
