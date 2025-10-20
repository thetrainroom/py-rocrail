import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Booster:
    """Booster/power district control object

    Boosters manage power distribution to different sections of the layout.
    Used for power management and short circuit handling.
    """

    def __init__(self, bstr_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com
        self.build(bstr_xml)

    def build(self, bstr: ET.Element):
        self.idx = bstr.attrib["id"]
        for attr, value in bstr.attrib.items():
            if attr == "id":
                continue
            set_attr(self, attr, value)

    def on(self):
        """Turn booster power on"""
        cmd = f'<powercmd id="{self.idx}" cmd="on"/>'
        self.communicator.send("powercmd", cmd)

    def off(self):
        """Turn booster power off"""
        cmd = f'<powercmd id="{self.idx}" cmd="off"/>'
        self.communicator.send("powercmd", cmd)
