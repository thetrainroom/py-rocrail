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
from pyrocrail.objects import set_attr
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
            elif child.tag == "lc":
                # Locomotive state update
                self._update_lc(child)
            elif child.tag == "fb":
                # Feedback sensor state update
                self._update_fb(child)
            elif child.tag == "bk":
                # Block state update
                self._update_bk(child)
            elif child.tag == "sw":
                # Switch state update
                self._update_sw(child)
            elif child.tag == "sg":
                # Signal state update
                self._update_sg(child)
            elif child.tag == "st":
                # Route state update
                self._update_st(child)
            # TODO: Add output state update handler (co)

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

    def _update_lc(self, lc_xml: ET.Element):
        """Update locomotive state from server"""
        lc_id = lc_xml.attrib.get('id')

        if not lc_id:
            print(f"Warning: Locomotive update without id: {ET.tostring(lc_xml, encoding='unicode')[:100]}")
            return

        # Check if locomotive exists
        if lc_id not in self._lc_domain:
            print(f"Warning: Received update for unknown locomotive: {lc_id}")
            return

        # Update locomotive attributes
        lc = self._lc_domain[lc_id]
        for attr, value in lc_xml.attrib.items():
            if attr == 'id':
                continue  # Don't overwrite the id
            set_attr(lc, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback('lc', lc_id, lc)

    def _update_fb(self, fb_xml: ET.Element):
        """Update feedback sensor state from server"""
        fb_id = fb_xml.attrib.get('id')

        if not fb_id:
            print(f"Warning: Feedback update without id: {ET.tostring(fb_xml, encoding='unicode')[:100]}")
            return

        # Check if feedback exists
        if fb_id not in self._fb_domain:
            print(f"Warning: Received update for unknown feedback sensor: {fb_id}")
            return

        # Update feedback attributes
        fb = self._fb_domain[fb_id]
        for attr, value in fb_xml.attrib.items():
            if attr == 'id':
                continue  # Don't overwrite the id
            set_attr(fb, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback('fb', fb_id, fb)

    def _update_bk(self, bk_xml: ET.Element):
        """Update block state from server"""
        bk_id = bk_xml.attrib.get('id')

        if not bk_id:
            print(f"Warning: Block update without id: {ET.tostring(bk_xml, encoding='unicode')[:100]}")
            return

        # Check if block exists
        if bk_id not in self._bk_domain:
            print(f"Warning: Received update for unknown block: {bk_id}")
            return

        # Update block attributes
        bk = self._bk_domain[bk_id]
        for attr, value in bk_xml.attrib.items():
            if attr == 'id':
                continue  # Don't overwrite the id
            set_attr(bk, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback('bk', bk_id, bk)

    def _update_sw(self, sw_xml: ET.Element):
        """Update switch state from server"""
        sw_id = sw_xml.attrib.get('id')

        if not sw_id:
            print(f"Warning: Switch update without id: {ET.tostring(sw_xml, encoding='unicode')[:100]}")
            return

        # Check if switch exists
        if sw_id not in self._sw_domain:
            print(f"Warning: Received update for unknown switch: {sw_id}")
            return

        # Update switch attributes
        sw = self._sw_domain[sw_id]
        for attr, value in sw_xml.attrib.items():
            if attr == 'id':
                continue  # Don't overwrite the id
            set_attr(sw, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback('sw', sw_id, sw)

    def _update_sg(self, sg_xml: ET.Element):
        """Update signal state from server"""
        sg_id = sg_xml.attrib.get('id')

        if not sg_id:
            print(f"Warning: Signal update without id: {ET.tostring(sg_xml, encoding='unicode')[:100]}")
            return

        # Check if signal exists
        if sg_id not in self._sg_domain:
            print(f"Warning: Received update for unknown signal: {sg_id}")
            return

        # Update signal attributes
        sg = self._sg_domain[sg_id]
        for attr, value in sg_xml.attrib.items():
            if attr == 'id':
                continue  # Don't overwrite the id
            set_attr(sg, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback('sg', sg_id, sg)

    def _update_st(self, st_xml: ET.Element):
        """Update route state from server"""
        st_id = st_xml.attrib.get('id')

        if not st_id:
            print(f"Warning: Route update without id: {ET.tostring(st_xml, encoding='unicode')[:100]}")
            return

        # Check if route exists
        if st_id not in self._st_domain:
            print(f"Warning: Received update for unknown route: {st_id}")
            return

        # Update route attributes
        st = self._st_domain[st_id]
        for attr, value in st_xml.attrib.items():
            if attr == 'id':
                continue  # Don't overwrite the id
            set_attr(st, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback('st', st_id, st)
