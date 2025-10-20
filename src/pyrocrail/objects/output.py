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
        # Dynamic attributes set via set_attr() in build()
        self.state: str | None = None
        self.value: int | None = None
        self.valueoff: int | None = None
        self.iid: str | None = None
        self.build(fb_xml)

    def build(self, co: ET.Element):
        self.idx = co.attrib["id"]
        self.color = None  # Initialize color attribute
        for attr, value in co.attrib.items():
            if attr == "id":
                continue
            set_attr(self, attr, value)
        for sub in co:
            if sub.tag == "color":
                # Convert string attributes to int for Color dataclass
                color_attrs: dict[str, int | str] = {}
                for k, v in sub.attrib.items():
                    if k == "id":
                        color_attrs[k] = v
                    else:
                        color_attrs[k] = int(v) if v else 0
                self.color = Color(**color_attrs)  # type: ignore[arg-type]

    def xml(self) -> None:
        # TODO: Verify exact XML format for output control commands
        # TODO: Add proper error handling for missing attributes
        if self.color:
            cmd = f'<co id="{self.idx}" state="{self.state}" value="{self.value}" valueoff="{self.valueoff}" iid="{self.iid}">\n{self.color.xml()}\n</co>'
        else:
            cmd = f'<co id="{self.idx}" state="{self.state}" value="{self.value}" valueoff="{self.valueoff}" iid="{self.iid}"/>'

        self.communicator.send("co", cmd)

    def on(self) -> None:
        # TODO: Verify correct command format for turning output on
        cmd = f'<co id="{self.idx}" cmd="on"/>'
        self.communicator.send("co", cmd)

    def off(self) -> None:
        # TODO: Verify correct command format for turning output off
        cmd = f'<co id="{self.idx}" cmd="off"/>'
        self.communicator.send("co", cmd)

    def flip(self) -> None:
        """Toggle output state (on <-> off)"""
        cmd = f'<co id="{self.idx}" cmd="flip"/>'
        self.communicator.send("co", cmd)

    def active(self, duration_ms: int | None = None) -> None:
        """Set output active for specified duration then turn off

        Args:
            duration_ms: Active duration in milliseconds (optional)
        """
        if duration_ms:
            cmd = f'<co id="{self.idx}" cmd="active" active="{duration_ms}"/>'
        else:
            cmd = f'<co id="{self.idx}" cmd="active"/>'
        self.communicator.send("co", cmd)
