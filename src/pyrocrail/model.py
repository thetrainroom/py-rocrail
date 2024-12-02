import xml.etree.ElementTree as ET
from pyrocrail.objects.feedback import Feedback
from pyrocrail.communicator import Communicator


class Model:
    def __init__(self, com: Communicator):
        self.communicator = com
        self.communicator.model = self
        self._fb_domain: dict[str, Feedback] = {}

    def init(self):
        self.communicator.send("model", '<model cmd="plan"/>')


    def decode(self, xml: ET.ElementTree):
        for child in xml:
            if child.tag == "clock":
                self._recv_clock(child)
            elif child.tag == "plan":
                print(f"Rocrail Plan {child.attrib['title']} Version: {child.attrib['rocrailversion']}")
                self.build(child)

    def build(self, plan_xml: ET.Element):
        for child in plan_xml:
            #if child.tag == "colist":
            #    self._build_co(child)
            if child.tag == "fblist":
                print(child)
                self._build_fb(child)


    def get_fb(self, label: str):
        return self._fb_domain[label]

    def _build_co(self, colist: ET.Element):
        for child in colist:
            idx = child.attrib['id']
            co = Output(idx)
            for attr, value in child.attrib.items():
                try:
                    val = int(value)
                except ValueError:
                    val = value
                setattr(co, attr, val)
            for sub in child:
                if sub.tag == "color":
                    co.color = Color(**sub.attrib)
            self.colist[idx] = co

    def _build_fb(self, fblist: ET.Element):
        for child in fblist:
            fb = Feedback(child, self.communicator)
            self._fb_domain[fb.idx] = fb
