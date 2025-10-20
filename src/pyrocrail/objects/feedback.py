import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Feedback:
    def __init__(self, fb_xml: ET.Element, com: Communicator):
        self.state = False
        self.change = False
        self.idx = ""
        self.communicator = com
        self.build(fb_xml)

    def build(self, fb_xml: ET.Element):
        self.idx = fb_xml.attrib["id"]
        for attr, value in fb_xml.attrib.items():
            set_attr(self, attr, value)

    def set(self, en: bool):
        xml = f'<fb id="{self.idx}" state="{str(en).lower()}"/>'
        if self.state != en:
            self.communicator.send("fb", xml)
        # Don't update state immediately - wait for server response
        # self.state = en

    def on(self):
        xml = f'<fb id="{self.idx}" state="true"/>'
        if not self.state:
            self.communicator.send("fb", xml)
        # Don't update state immediately - wait for server response
        # self.state = True

    def off(self):
        xml = f'<fb id="{self.idx}" state="false"/>'
        if self.state:
            self.communicator.send("fb", xml)
        # Don't update state immediately - wait for server response
        # self.state = False

    def flip(self):
        xml = f'<fb id="{self.idx}" cmd="flip"/>'
        self.communicator.send("fb", xml)
        # Don't update state immediately - wait for server response
        # self.state = not self.state
