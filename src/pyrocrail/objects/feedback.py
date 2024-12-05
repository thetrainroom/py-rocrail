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
        self.idx = fb_xml.attrib['id']
        for attr, value in fb_xml.attrib.items():
            set_attr(self, attr, value)

    def set(self, en: bool):
        xml = f'<fb id="{self.id}" cmd="{"on" if en else "off"}"/>'
        #xml = f'<fb id="{self.id}" state="{str(en).lower()}"/>'
        if self.state != en:
            self.communicator.send("fb", xml)
        self.state = en

    def on(self):
        xml = f'<fb id="{self.id}" cmd="on"/>'
        if not self.state:
            self.communicator.send("fb", xml)
        self.state = True

    def off(self):
        xml = f'<fb id="{self.id}" cmd="off"/>'
        if self.state:
            self.communicator.send("fb", xml)
        self.state = not self.state

    def flip(self):
        xml = f'<fb id="{self.id}" cmd="flip"/>'
        self.communicator.send("fb", xml)
        self.state = not self.state
