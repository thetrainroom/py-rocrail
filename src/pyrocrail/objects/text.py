import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Text:
    """Text display object for stations and panels

    Text objects display information on layout displays, station boards,
    and control panels.
    """

    def __init__(self, tx_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com
        self.build(tx_xml)

    def build(self, tx: ET.Element):
        self.idx = tx.attrib["id"]
        for attr, value in tx.attrib.items():
            if attr == "id":
                continue
            set_attr(self, attr, value)

    def set_format(self, format_str: str, **kwargs):
        """Set text format with optional parameters

        Args:
            format_str: Format string (e.g., "the loco id is %lcid%")
            **kwargs: Optional parameters like bkid, lcid
        """
        attrs = [f'id="{self.idx}"', f'format="{format_str}"']
        for key, value in kwargs.items():
            attrs.append(f'{key}="{value}"')
        cmd = f'<text {" ".join(attrs)}/>'
        self.communicator.send("text", cmd)
