import xml.etree.ElementTree as ET
import datetime
import time
from dataclasses import dataclass, field
from pyrocrail.objects.feedback import Feedback
from pyrocrail.objects.output import Output
from pyrocrail.objects.locomotive import Locomotive
from pyrocrail.objects.switch import Switch
from pyrocrail.objects.signal import Signal
from pyrocrail.objects.route import Route
from pyrocrail.objects.block import Block
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
        self._co_domain: dict[str, Output] = {}
        self._lc_domain: dict[str, Locomotive] = {}
        self._sw_domain: dict[str, Switch] = {}
        self._sg_domain: dict[str, Signal] = {}
        self._st_domain: dict[str, Route] = {}
        self._bk_domain: dict[str, Block] = {}
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
            if child.tag == "colist":
                self._build_co(child)
            elif child.tag == "fblist":
                self._build_fb(child)
            elif child.tag == "lclist":
                self._build_lc(child)
            elif child.tag == "swlist":
                self._build_sw(child)
            elif child.tag == "sglist":
                self._build_sg(child)
            elif child.tag == "stlist":
                self._build_st(child)
            elif child.tag == "bklist":
                self._build_bk(child)
        self.plan_recv = True

    def get_fb(self, label: str) -> Feedback:
        return self._fb_domain[label]
        
    def get_co(self, label: str) -> Output:
        return self._co_domain[label]
        
    def get_lc(self, label: str) -> Locomotive:
        return self._lc_domain[label]
        
    def get_sw(self, label: str) -> Switch:
        return self._sw_domain[label]
        
    def get_sg(self, label: str) -> Signal:
        return self._sg_domain[label]
        
    def get_st(self, label: str) -> Route:
        return self._st_domain[label]
        
    def get_bk(self, label: str) -> Block:
        return self._bk_domain[label]

    def _recv_clock(self, tag: ET.Element):
        self.clock.hour = int(tag.attrib["hour"])
        self.clock.minute = int(tag.attrib["minute"])
        self.clock.ts = datetime.datetime.fromtimestamp(int(tag.attrib["time"]))
        self.curr_time = self.clock.hour + self.clock.minute / 60
        if self.time_callback is not None:
            self.time_callback()
        print("Time")

    def _build_co(self, colist: ET.Element):
        for child in colist:
            co = Output(child, self.communicator)
            self._co_domain[co.idx] = co

    def _build_fb(self, fblist: ET.Element):
        for child in fblist:
            fb = Feedback(child, self.communicator)
            self._fb_domain[fb.idx] = fb
            
    def _build_lc(self, lclist: ET.Element):
        for child in lclist:
            lc = Locomotive(child, self.communicator)
            self._lc_domain[lc.idx] = lc
            
    def _build_sw(self, swlist: ET.Element):
        for child in swlist:
            # TODO: Determine if this should be a ThreeWaySwitch based on XML attributes
            sw = Switch(child, self.communicator)
            self._sw_domain[sw.idx] = sw
            
    def _build_sg(self, sglist: ET.Element):
        for child in sglist:
            sg = Signal(child, self.communicator)
            self._sg_domain[sg.idx] = sg
            
    def _build_st(self, stlist: ET.Element):
        for child in stlist:
            st = Route(child, self.communicator)
            self._st_domain[st.idx] = st
            
    def _build_bk(self, bklist: ET.Element):
        for child in bklist:
            bk = Block(child, self.communicator)
            self._bk_domain[bk.idx] = bk
