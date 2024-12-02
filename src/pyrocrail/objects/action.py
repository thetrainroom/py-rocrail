import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr

class ActionCtrl:
    def __init__(self, actrl_xml: ET.Element):
        self.idx = ""
        self.actioncond = []

    def build(self, fb_xml: ET.Element):
        self.idx = fb_xml.attrib['id']
        for attr, value in fb_xml.attrib.items():
            set_attr(self, attr, value)
