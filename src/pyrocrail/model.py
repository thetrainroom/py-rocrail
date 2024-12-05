import xml.etree.ElementTree as ET
import datetime
import time
from dataclasses import dataclass, field
from pyrocrail.objects.feedback import Feedback
from pyrocrail.communicator import Communicator


@dataclass
class Clock:
    hour: int = 0
    minute: int = 0
    ts: datetime.datetime = field(default_factory=datetime.datetime.now)

class Model:
    def __init__(self, com: Communicator):
        self.communicator = com
        self.communicator.model = self
        self._fb_domain: dict[str, Feedback] = {}
        self.curr_time: float = 0.0
        self.clock: Clock = Clock()
        self.change_callback = None
        self.time_callback = None
        self.plan_recv = False

    def init(self):
        self.communicator.send("model", '<model cmd="plan"/>')
        while not self.plan_recv:
            time.sleep(0.1)
        print("Model OK")


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
                self._build_fb(child)
        self.plan_recv = True


    def get_fb(self, label: str):
        return self._fb_domain[label]

    def _recv_clock(self, tag: ET.Element):
        self.clock.hour = int(tag.attrib['hour'])
        self.clock.minute = int(tag.attrib['minute'])
        self.clock.ts = datetime.datetime.fromtimestamp(int(tag.attrib['time']))
        self.curr_time = self.clock.hour + self.clock.minute / 60
        if self.time_callback is not None:
            self.time_callback()
        print("Time")

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
