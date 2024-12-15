from dataclasses import dataclass
import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


@dataclass
class Color:
    red: int = 0
    green: int = 0
    blue: int = 0
    white: int = 0
    white2: int = 0
    saturation: int = 0
    rgbType: int = 0  # noqa
    brightness: int = 0
    id: str = ""

    def xml(self):
        return f'<color red="{self.red}" green="{self.green}" blue="{self.blue}" white="{self.white}" white2="{self.white2}" saturation="{self.saturation}" rgbType="{self.rgbType}" />'


class Output:
    def __init__(self, fb_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com
        self.build(fb_xml)

    def build(self, co: ET.Element):
        self.idx = co.attrib["id"]
        for attr, value in co.attrib.items():
            if attr == "id":
                continue
            set_attr(self, attr, value)
        for sub in co:
            if sub.tag == "color":
                co.color = Color(**sub.attrib)

    def xml(self):
        if self.color:
            cmd = f'<co id="{self.idx}" state="{self.state}" value="{self.value}" valueoff="{self.valueoff}" iid="{self.iid}">\n{self.color.xml()}\n</co>'
        else:
            cmd = f'<co id="{self.idx}" state="{self.state}" value="{self.value}" valueoff="{self.valueoff}" iid="{self.iid}"/>'

        self.communicator.send("co", cmd)
