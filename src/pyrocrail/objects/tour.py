import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Tour:
    """Tour object for automated demonstrations

    Tours provide automated sequences for demo mode and visitor presentations.
    Note: Commands are not documented in official XMLScript documentation.
    """

    def __init__(self, tour_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com
        self.build(tour_xml)

    def build(self, tour: ET.Element):
        self.idx = tour.attrib["id"]
        for attr, value in tour.attrib.items():
            if attr == "id":
                continue
            set_attr(self, attr, value)
