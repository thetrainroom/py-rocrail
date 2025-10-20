import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Variable:
    """Variable object for global state tracking

    Variables store values that can be used across scripts and automation.
    Supports integer values and text strings.
    """

    def __init__(self, vr_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com
        self.build(vr_xml)

    def build(self, vr: ET.Element):
        self.idx = vr.attrib["id"]
        for attr, value in vr.attrib.items():
            if attr == "id":
                continue
            set_attr(self, attr, value)

    def random(self):
        """Set variable to a random value"""
        cmd = f'<vr id="{self.idx}" cmd="random"/>'
        self.communicator.send("vr", cmd)

    def start(self):
        """Start variable (for timer variables)"""
        cmd = f'<vr id="{self.idx}" cmd="start"/>'
        self.communicator.send("vr", cmd)

    def stop(self):
        """Stop variable (for timer variables)"""
        cmd = f'<vr id="{self.idx}" cmd="stop"/>'
        self.communicator.send("vr", cmd)

    def set_value(self, value: int = None, text: str = None, generated: bool = True):
        """Set variable value and/or text

        Args:
            value: Integer value to set (optional)
            text: Text string to set (optional)
            generated: If True, variable is temporary (default). If False, persists between sessions.
        """
        attrs = [f'id="{self.idx}"']
        if value is not None:
            attrs.append(f'value="{value}"')
        if text is not None:
            attrs.append(f'text="{text}"')
        attrs.append(f'generated="{"true" if generated else "false"}"')

        cmd = f'<vr {" ".join(attrs)}/>'
        self.communicator.send("vr", cmd)
