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

    def showon(self):
        """Show/turn on the text display"""
        cmd = f'<text id="{self.idx}" cmd="showon"/>'
        self.communicator.send("text", cmd)

    def showoff(self):
        """Hide/turn off the text display"""
        cmd = f'<text id="{self.idx}" cmd="showoff"/>'
        self.communicator.send("text", cmd)

    def blink(self, enable: bool = True):
        """Enable or disable text blinking

        Args:
            enable: True to enable blinking, False to disable
        """
        blink_value = "true" if enable else "false"
        cmd = f'<text id="{self.idx}" cmd="blink" blink="{blink_value}"/>'
        self.communicator.send("text", cmd)

    def on(self):
        """Turn text display on"""
        cmd = f'<text id="{self.idx}" cmd="on"/>'
        self.communicator.send("text", cmd)

    def off(self):
        """Turn text display off"""
        cmd = f'<text id="{self.idx}" cmd="off"/>'
        self.communicator.send("text", cmd)

    def click(self):
        """Simulate a click on the text display"""
        cmd = f'<text id="{self.idx}" cmd="click"/>'
        self.communicator.send("text", cmd)

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
