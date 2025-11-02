import xml.etree.ElementTree as ET
import datetime
import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Any
from pyrocrail.objects.feedback import Feedback
from pyrocrail.objects.output import Output
from pyrocrail.objects.locomotive import Locomotive
from pyrocrail.objects.switch import Switch
from pyrocrail.objects.signal import Signal
from pyrocrail.objects.route import Route
from pyrocrail.objects.block import Block
from pyrocrail.objects.car import Car
from pyrocrail.objects.operator import Operator
from pyrocrail.objects.schedule import Schedule
from pyrocrail.objects.stage import Stage, Section
from pyrocrail.objects.text import Text
from pyrocrail.objects.booster import Booster
from pyrocrail.objects.variable import Variable
from pyrocrail.objects.tour import Tour
from pyrocrail.objects.location import Location
from pyrocrail.objects.weather import Weather
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator

# Use package-level logger
logger = logging.getLogger("pyrocrail")


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
        self._car_domain: dict[str, Car] = {}
        self._operator_domain: dict[str, Operator] = {}
        self._sc_domain: dict[str, Schedule] = {}
        self._sb_domain: dict[str, Stage] = {}
        self._tx_domain: dict[str, Text] = {}
        self._bstr_domain: dict[str, Booster] = {}
        self._vr_domain: dict[str, Variable] = {}
        self._tour_domain: dict[str, Tour] = {}
        self._location_domain: dict[str, Location] = {}
        self._weather_domain: dict[str, Weather] = {}
        self.curr_time: float = 0.0
        self.clock: Clock = Clock()
        self.change_callback: Callable[[str, str, Any], None] | None = None
        self.time_callback: Callable[[], None] | None = None
        self.plan_recv = False
        self.server_shutting_down = False  # Flag for graceful server shutdown

    def init(self):
        self.communicator.send("model", '<model cmd="plan"/>')
        while not self.plan_recv:
            time.sleep(0.1)
        logger.info("Model initialized successfully")

    def decode(self, xml: ET.Element) -> None:
        for child in xml:
            if child.tag == "clock":
                self._recv_clock(child)
            elif child.tag == "plan":
                logger.info(f"Loaded plan '{child.attrib['title']}' (Rocrail {child.attrib['rocrailversion']})")
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
            elif child.tag == "car":
                # Car state update
                self._update_car(child)
            elif child.tag == "operator":
                # Operator state update
                self._update_operator(child)
            elif child.tag == "sc":
                # Schedule state update
                self._update_sc(child)
            elif child.tag == "sb":
                # Stage block state update
                self._update_sb(child)
            elif child.tag == "exception":
                # Exception/error message from server
                self._handle_exception(child)
            elif child.tag == "text":
                # Text display state update
                self._update_tx(child)
            elif child.tag == "bstr":
                # Booster state update
                self._update_bstr(child)
            elif child.tag == "vr":
                # Variable state update
                self._update_vr(child)
            elif child.tag == "tour":
                # Tour state update
                self._update_tour(child)
            elif child.tag == "location":
                # Location state update
                self._update_location(child)
            elif child.tag == "weather":
                # Weather state update
                self._update_weather(child)
            elif child.tag == "sys":
                # System messages (shutdown, etc.)
                self._handle_sys(child)
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
            elif child.tag == "carlist":
                self._build_car(child)
            elif child.tag == "operatorlist":
                self._build_operator(child)
            elif child.tag == "sclist":
                self._build_sc(child)
            elif child.tag == "sblist":
                self._build_sb(child)
            elif child.tag == "txlist":
                self._build_tx(child)
            elif child.tag == "bstrlist":
                self._build_bstr(child)
            elif child.tag == "vrlist":
                self._build_vr(child)
            elif child.tag == "tourlist":
                self._build_tour(child)
            elif child.tag == "locationlist":
                self._build_location(child)
            elif child.tag == "weatherlist":
                self._build_weather(child)
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

    def get_car(self, label: str) -> Car:
        return self._car_domain[label]

    def get_operator(self, label: str) -> Operator:
        return self._operator_domain[label]

    def get_schedule(self, label: str) -> Schedule:
        return self._sc_domain[label]

    def get_stage(self, label: str) -> Stage:
        return self._sb_domain[label]

    def get_text(self, label: str) -> Text:
        return self._tx_domain[label]

    def get_booster(self, label: str) -> Booster:
        return self._bstr_domain[label]

    def get_variable(self, label: str) -> Variable:
        return self._vr_domain[label]

    def get_tour(self, label: str) -> Tour:
        return self._tour_domain[label]

    def get_location(self, label: str) -> Location:
        return self._location_domain[label]

    def get_weather(self, label: str) -> Weather:
        return self._weather_domain[label]

    # List getter methods (returns dictionaries of objects)
    def get_locomotives(self) -> dict[str, Locomotive]:
        """Get all locomotives {id: Locomotive}"""
        return dict(self._lc_domain)

    def get_blocks(self) -> dict[str, Block]:
        """Get all blocks {id: Block}"""
        return dict(self._bk_domain)

    def get_switches(self) -> dict[str, Switch]:
        """Get all switches {id: Switch}"""
        return dict(self._sw_domain)

    def get_signals(self) -> dict[str, Signal]:
        """Get all signals {id: Signal}"""
        return dict(self._sg_domain)

    def get_routes(self) -> dict[str, Route]:
        """Get all routes {id: Route}"""
        return dict(self._st_domain)

    def get_feedbacks(self) -> dict[str, Feedback]:
        """Get all feedback sensors {id: Feedback}"""
        return dict(self._fb_domain)

    def get_outputs(self) -> dict[str, Output]:
        """Get all outputs {id: Output}"""
        return dict(self._co_domain)

    def get_cars(self) -> dict[str, Car]:
        """Get all cars {id: Car}"""
        return dict(self._car_domain)

    def get_operators(self) -> dict[str, Operator]:
        """Get all operators {id: Operator}"""
        return dict(self._operator_domain)

    def get_schedules(self) -> dict[str, Schedule]:
        """Get all schedules {id: Schedule}"""
        return dict(self._sc_domain)

    def get_stages(self) -> dict[str, Stage]:
        """Get all stage blocks {id: Stage}"""
        return dict(self._sb_domain)

    # Model query commands
    def request_locomotive_list(self) -> None:
        """Request locomotive list from server

        The server will respond with <lclist> containing all locomotives,
        which will be processed by decode() and added to _lc_domain.
        """
        self.communicator.send("model", '<model cmd="lclist"/>')

    def request_switch_list(self) -> None:
        """Request switch list from server

        The server will respond with <swlist> containing all switches,
        which will be processed by decode() and added to _sw_domain.
        """
        self.communicator.send("model", '<model cmd="swlist"/>')

    def request_feedback_list(self) -> None:
        """Request feedback sensor list from server

        The server will respond with <fblist> containing all feedback sensors,
        which will be processed by decode() and added to _fb_domain.
        """
        self.communicator.send("model", '<model cmd="fblist"/>')

    def request_locomotive_properties(self, loco_id: str) -> None:
        """Request detailed properties for a specific locomotive

        Args:
            loco_id: Locomotive ID to query

        The server will respond with detailed locomotive properties including
        all configuration and current state information.
        """
        self.communicator.send("model", f'<model cmd="lcprops" val="{loco_id}"/>')

    def add_object(self, obj_type: str, xml_element: ET.Element) -> None:
        """Add a new object to the model dynamically

        Args:
            obj_type: Object type (lc, sw, fb, bk, sg, st, etc.)
            xml_element: XML element defining the object

        Example:
            # Create a new locomotive
            lc_xml = ET.fromstring('<lc id="new_loco" addr="3" V="0"/>')
            model.add_object("lc", lc_xml)
        """
        xml_str = ET.tostring(xml_element, encoding="unicode")
        self.communicator.send("model", f'<model cmd="add">{xml_str}</model>')

    def remove_object(self, obj_type: str, obj_id: str) -> None:
        """Remove an object from the model

        Args:
            obj_type: Object type (lc, sw, fb, bk, sg, st, etc.)
            obj_id: Object ID to remove

        Example:
            model.remove_object("lc", "old_loco")
        """
        self.communicator.send("model", f'<model cmd="remove"><{obj_type} id="{obj_id}"/></model>')

    def modify_object(self, obj_type: str, obj_id_or_xml: str | ET.Element, **attributes: str | int | None) -> None:
        """Modify an existing object's properties

        Supports two modes:
        1. Simple attribute modification (pass obj_id + attributes)
        2. Complex object modification (pass xml_element)

        Args:
            obj_type: Object type (lc, sw, fb, bk, sg, st, sc, etc.)
            obj_id_or_xml: Either object ID (str) for simple modification,
                          or complete XML element for complex objects with children
            **attributes: Attributes to update (only used for simple modification)

        Examples:
            # Simple: Modify locomotive attributes
            model.modify_object("lc", "my_loco", V_max="120", mass="100")

            # Complex: Modify schedule with entries (child elements)
            sc_xml = ET.fromstring('''<sc id="Test" timeframe="1">
                <scentry block="sb1" hour="10" minute="30"/>
                <scentry block="cb3" hour="12" minute="0"/>
            </sc>''')
            model.modify_object("sc", sc_xml)
        """
        # Check if we received an XML element (complex object)
        if isinstance(obj_id_or_xml, ET.Element):
            xml_str = ET.tostring(obj_id_or_xml, encoding="unicode")
            self.communicator.send("model", f'<model cmd="modify" controlcode="" slavecode="">{xml_str}</model>')
        else:
            # Simple attribute modification
            obj_id = obj_id_or_xml
            # Convert None back to empty string for XML
            attrs = " ".join([f'{key}="{value if value is not None else ""}"' for key, value in attributes.items()])
            self.communicator.send("model", f'<model cmd="modify"><{obj_type} id="{obj_id}" {attrs}/></model>')

    def merge_plan(self, plan_xml: ET.Element) -> None:
        """Merge plan updates from XML

        Args:
            plan_xml: Plan XML element to merge

        This is used to update the model with changes from the server
        without requesting the complete plan again.
        """
        xml_str = ET.tostring(plan_xml, encoding="unicode")
        self.communicator.send("model", f'<model cmd="merge">{xml_str}</model>')

    def _recv_clock(self, tag: ET.Element):
        self.clock.hour = int(tag.attrib["hour"])
        self.clock.minute = int(tag.attrib["minute"])
        self.clock.ts = datetime.datetime.fromtimestamp(int(tag.attrib["time"]))
        self.curr_time = self.clock.hour + self.clock.minute / 60
        if self.time_callback is not None:
            self.time_callback()
        logger.debug(f"Clock update: {self.clock.hour:02d}:{self.clock.minute:02d}")

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

    def _build_car(self, carlist: ET.Element):
        for child in carlist:
            car = Car(child, self.communicator)
            self._car_domain[car.idx] = car

    def _build_operator(self, operatorlist: ET.Element):
        for child in operatorlist:
            opr = Operator(child, self.communicator)
            self._operator_domain[opr.idx] = opr

    def _build_sc(self, sclist: ET.Element):
        for child in sclist:
            sc = Schedule(child, self.communicator)
            self._sc_domain[sc.idx] = sc

    def _build_sb(self, sblist: ET.Element):
        for child in sblist:
            sb = Stage(child, self.communicator)
            self._sb_domain[sb.idx] = sb

    def _build_tx(self, txlist: ET.Element):
        for child in txlist:
            tx = Text(child, self.communicator)
            self._tx_domain[tx.idx] = tx

    def _build_bstr(self, bstrlist: ET.Element):
        for child in bstrlist:
            bstr = Booster(child, self.communicator)
            self._bstr_domain[bstr.idx] = bstr

    def _build_vr(self, vrlist: ET.Element):
        for child in vrlist:
            vr = Variable(child, self.communicator)
            self._vr_domain[vr.idx] = vr

    def _build_tour(self, tourlist: ET.Element):
        for child in tourlist:
            tour = Tour(child, self.communicator)
            self._tour_domain[tour.idx] = tour

    def _build_location(self, locationlist: ET.Element):
        for child in locationlist:
            location = Location(child, self.communicator)
            self._location_domain[location.idx] = location

    def _build_weather(self, weatherlist: ET.Element):
        for child in weatherlist:
            weather = Weather(child, self.communicator)
            self._weather_domain[weather.idx] = weather

    def _update_lc(self, lc_xml: ET.Element):
        """Update locomotive state from server"""
        lc_id = lc_xml.attrib.get("id")

        if not lc_id:
            logger.warning(f"Locomotive update without id: {ET.tostring(lc_xml, encoding='unicode')[:100]}")
            return

        # Check if locomotive exists
        if lc_id not in self._lc_domain:
            logger.warning(f"Received update for unknown locomotive: {lc_id}")
            return

        # Update locomotive attributes
        lc = self._lc_domain[lc_id]
        for attr, value in lc_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(lc, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("lc", lc_id, lc)

    def _update_fb(self, fb_xml: ET.Element):
        """Update feedback sensor state from server"""
        fb_id = fb_xml.attrib.get("id")

        if not fb_id:
            logger.warning(f"Feedback update without id: {ET.tostring(fb_xml, encoding='unicode')[:100]}")
            return

        # Check if feedback exists
        if fb_id not in self._fb_domain:
            logger.warning(f"Received update for unknown feedback sensor: {fb_id}")
            return

        # Update feedback attributes
        fb = self._fb_domain[fb_id]
        for attr, value in fb_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(fb, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("fb", fb_id, fb)

    def _update_bk(self, bk_xml: ET.Element):
        """Update block state from server"""
        bk_id = bk_xml.attrib.get("id")

        if not bk_id:
            logger.warning(f"Block update without id: {ET.tostring(bk_xml, encoding='unicode')[:100]}")
            return

        # Check if block exists
        if bk_id not in self._bk_domain:
            logger.warning(f"Received update for unknown block: {bk_id}")
            return

        # Update block attributes
        bk = self._bk_domain[bk_id]
        for attr, value in bk_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(bk, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("bk", bk_id, bk)

    def _update_sw(self, sw_xml: ET.Element):
        """Update switch state from server"""
        sw_id = sw_xml.attrib.get("id")

        if not sw_id:
            logger.warning(f"Switch update without id: {ET.tostring(sw_xml, encoding='unicode')[:100]}")
            return

        # Check if switch exists
        if sw_id not in self._sw_domain:
            logger.warning(f"Received update for unknown switch: {sw_id}")
            return

        # Update switch attributes
        sw = self._sw_domain[sw_id]
        for attr, value in sw_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(sw, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("sw", sw_id, sw)

    def _update_sg(self, sg_xml: ET.Element):
        """Update signal state from server"""
        sg_id = sg_xml.attrib.get("id")

        if not sg_id:
            logger.warning(f"Signal update without id: {ET.tostring(sg_xml, encoding='unicode')[:100]}")
            return

        # Check if signal exists
        if sg_id not in self._sg_domain:
            logger.warning(f"Received update for unknown signal: {sg_id}")
            return

        # Update signal attributes
        sg = self._sg_domain[sg_id]
        for attr, value in sg_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(sg, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("sg", sg_id, sg)

    def _update_st(self, st_xml: ET.Element):
        """Update route state from server"""
        st_id = st_xml.attrib.get("id")

        if not st_id:
            logger.warning(f"Route update without id: {ET.tostring(st_xml, encoding='unicode')[:100]}")
            return

        # Check if route exists
        if st_id not in self._st_domain:
            logger.warning(f"Received update for unknown route: {st_id}")
            return

        # Update route attributes
        st = self._st_domain[st_id]
        for attr, value in st_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(st, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("st", st_id, st)

    def _update_car(self, car_xml: ET.Element):
        """Update car state from server"""
        car_id = car_xml.attrib.get("id")

        if not car_id:
            logger.warning(f"Car update without id: {ET.tostring(car_xml, encoding='unicode')[:100]}")
            return

        # Check if car exists
        if car_id not in self._car_domain:
            logger.warning(f"Received update for unknown car: {car_id}")
            return

        # Update car attributes
        car = self._car_domain[car_id]
        for attr, value in car_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(car, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("car", car_id, car)

    def _update_operator(self, operator_xml: ET.Element):
        """Update operator state from server"""
        operator_id = operator_xml.attrib.get("id")

        if not operator_id:
            logger.warning(f"Operator update without id: {ET.tostring(operator_xml, encoding='unicode')[:100]}")
            return

        # Check if operator exists
        if operator_id not in self._operator_domain:
            logger.warning(f"Received update for unknown operator: {operator_id}")
            return

        # Update operator attributes
        opr = self._operator_domain[operator_id]
        for attr, value in operator_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            # Handle 'class' attribute specially (Python keyword)
            if attr == "class":
                set_attr(opr, "class_", value)
            else:
                set_attr(opr, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("operator", operator_id, opr)

    def _update_sc(self, sc_xml: ET.Element):
        """Update schedule state from server"""
        sc_id = sc_xml.attrib.get("id")

        if not sc_id:
            logger.warning(f"Schedule update without id: {ET.tostring(sc_xml, encoding='unicode')[:100]}")
            return

        # Check if schedule exists
        if sc_id not in self._sc_domain:
            logger.warning(f"Received update for unknown schedule: {sc_id}")
            return

        # Update schedule attributes
        sc = self._sc_domain[sc_id]
        for attr, value in sc_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            # Handle 'class' attribute specially (Python keyword)
            if attr == "class":
                set_attr(sc, "class_", value)
            else:
                set_attr(sc, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("sc", sc_id, sc)

    def _update_sb(self, sb_xml: ET.Element):
        """Update stage block state from server"""
        sb_id = sb_xml.attrib.get("id")

        if not sb_id:
            logger.warning(f"Stage block update without id: {ET.tostring(sb_xml, encoding='unicode')[:100]}")
            return

        # Check if stage exists
        if sb_id not in self._sb_domain:
            logger.warning(f"Received update for unknown stage block: {sb_id}")
            return

        # Update stage attributes
        sb = self._sb_domain[sb_id]
        for attr, value in sb_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            # Handle 'class' attribute specially (Python keyword)
            if attr == "class":
                set_attr(sb, "class_", value)
            else:
                set_attr(sb, attr, value)

        # Update sections if present in the update
        section_elements = sb_xml.findall("section")
        if section_elements:
            # Update existing sections or add new ones
            for section_el in section_elements:
                section_id = section_el.attrib.get("id")
                if not section_id:
                    continue

                # Find existing section
                existing_section = sb.get_section(section_id)
                if existing_section:
                    # Update existing section attributes
                    for attr, value in section_el.attrib.items():
                        if attr == "id":
                            continue  # Don't overwrite the id
                        set_attr(existing_section, attr, value)
                else:
                    # Section doesn't exist, add it (shouldn't happen normally)
                    new_section = Section(section_el)
                    sb.sections.append(new_section)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("sb", sb_id, sb)

    def _handle_exception(self, exception_xml: ET.Element):
        """Handle exception/error messages from server

        Exception messages contain level, code, and text attributes.

        Rocrail uses numeric bit flags for levels:
        - 1 (0x0001): EXCEPTION - Critical errors
        - 2 (0x0002): WARNING - Non-critical warnings
        - 4 (0x0004): INFO - Informational messages
        - 8 (0x0008): BYTE - Byte-level tracing
        - 16384 (0x4000): DEBUG - Debug/trace messages (function acks, etc.)

        Also supports string levels for backward compatibility:
        - "exception", "warning", "info"
        """
        level_str = exception_xml.attrib.get("level", "unknown")
        code = exception_xml.attrib.get("code", "")
        text = exception_xml.attrib.get("text", "")
        obj_id = exception_xml.attrib.get("id", "")

        # Format exception message
        msg_parts = []
        if code:
            msg_parts.append(f"[{code}]")
        if obj_id:
            msg_parts.append(f"(object: {obj_id})")
        if text:
            msg_parts.append(text)
        msg = " ".join(msg_parts) if msg_parts else "Unknown error"

        # Try to parse level as numeric (Rocrail uses bit flags)
        try:
            level_num = int(level_str)

            # Map numeric Rocrail levels to Python logging levels
            if level_num & 0x0001:  # EXCEPTION bit
                logger.error(f"Rocrail exception: {msg}")
            elif level_num & 0x0002:  # WARNING bit
                logger.warning(f"Rocrail warning: {msg}")
            elif level_num & 0x0004:  # INFO bit
                logger.info(f"Rocrail info: {msg}")
            elif level_num & 0x4000:  # DEBUG bit (16384)
                logger.debug(f"Rocrail debug: {msg}")
            else:
                # Other flags (BYTE, AUTO, CALC, MONITOR, PARSE)
                logger.debug(f"Rocrail [{level_num}]: {msg}")

        except ValueError:
            # String-based level (backward compatibility)
            if level_str == "exception":
                logger.error(f"Rocrail exception: {msg}")
            elif level_str == "warning":
                logger.warning(f"Rocrail warning: {msg}")
            elif level_str == "info":
                logger.info(f"Rocrail info: {msg}")
            else:
                logger.info(f"Rocrail {level_str}: {msg}")

    def _handle_sys(self, sys_xml: ET.Element):
        """Handle system messages from server

        System messages include:
        - cmd="shutdown": Server is shutting down gracefully
        - cmd="go": Track power on
        - cmd="stop": Track power off
        - etc.
        """
        cmd = sys_xml.attrib.get("cmd", "")

        if cmd == "shutdown":
            # Server is shutting down gracefully
            self.server_shutting_down = True
            logger.info("Server shutting down gracefully")
        # Other system commands can be logged but don't require special handling
        # as they're typically sent by us, not by the server

    def _update_tx(self, tx_xml: ET.Element):
        """Update text display state from server"""
        tx_id = tx_xml.attrib.get("id")

        if not tx_id:
            logger.warning(f"Text display update without id: {ET.tostring(tx_xml, encoding='unicode')[:100]}")
            return

        # Check if text exists
        if tx_id not in self._tx_domain:
            logger.warning(f"Received update for unknown text display: {tx_id}")
            return

        # Update text attributes
        tx = self._tx_domain[tx_id]
        for attr, value in tx_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(tx, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("text", tx_id, tx)

    def _update_bstr(self, bstr_xml: ET.Element):
        """Update booster state from server"""
        bstr_id = bstr_xml.attrib.get("id")

        if not bstr_id:
            logger.warning(f"Booster update without id: {ET.tostring(bstr_xml, encoding='unicode')[:100]}")
            return

        # Check if booster exists
        if bstr_id not in self._bstr_domain:
            logger.warning(f"Received update for unknown booster: {bstr_id}")
            return

        # Update booster attributes
        bstr = self._bstr_domain[bstr_id]
        for attr, value in bstr_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(bstr, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("bstr", bstr_id, bstr)

    def _update_vr(self, vr_xml: ET.Element):
        """Update variable state from server"""
        vr_id = vr_xml.attrib.get("id")

        if not vr_id:
            logger.warning(f"Variable update without id: {ET.tostring(vr_xml, encoding='unicode')[:100]}")
            return

        # Check if variable exists
        if vr_id not in self._vr_domain:
            logger.warning(f"Received update for unknown variable: {vr_id}")
            return

        # Update variable attributes
        vr = self._vr_domain[vr_id]
        for attr, value in vr_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(vr, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("vr", vr_id, vr)

    def _update_tour(self, tour_xml: ET.Element):
        """Update tour state from server"""
        tour_id = tour_xml.attrib.get("id")

        if not tour_id:
            logger.warning(f"Tour update without id: {ET.tostring(tour_xml, encoding='unicode')[:100]}")
            return

        # Check if tour exists
        if tour_id not in self._tour_domain:
            logger.warning(f"Received update for unknown tour: {tour_id}")
            return

        # Update tour attributes
        tour = self._tour_domain[tour_id]
        for attr, value in tour_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(tour, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("tour", tour_id, tour)

    def _update_location(self, location_xml: ET.Element):
        """Update location state from server"""
        location_id = location_xml.attrib.get("id")

        if not location_id:
            logger.warning(f"Location update without id: {ET.tostring(location_xml, encoding='unicode')[:100]}")
            return

        # Check if location exists
        if location_id not in self._location_domain:
            logger.warning(f"Received update for unknown location: {location_id}")
            return

        # Update location attributes
        location = self._location_domain[location_id]
        for attr, value in location_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(location, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("location", location_id, location)

    def _update_weather(self, weather_xml: ET.Element):
        """Update weather state from server"""
        weather_id = weather_xml.attrib.get("id")

        if not weather_id:
            logger.warning(f"Weather update without id: {ET.tostring(weather_xml, encoding='unicode')[:100]}")
            return

        # Check if weather exists
        if weather_id not in self._weather_domain:
            logger.warning(f"Received update for unknown weather: {weather_id}")
            return

        # Update weather attributes
        weather = self._weather_domain[weather_id]
        for attr, value in weather_xml.attrib.items():
            if attr == "id":
                continue  # Don't overwrite the id
            set_attr(weather, attr, value)

        # Call change callback if registered
        if self.change_callback is not None:
            self.change_callback("weather", weather_id, weather)

    def export_state(self) -> dict:
        """Export current layout state as dictionary for emergency recovery.

        Returns a dictionary containing the current state of all locomotives, blocks,
        switches, signals, and other layout elements. This state can be saved to disk
        and used to help operators manually resync Rocrail after a connection loss.

        Returns:
            Dictionary with layout state including:
            - timestamp: Current time
            - clock: Rocrail clock state
            - locomotives: List of all locos with speed, direction, position
            - blocks: List of all blocks with occupation and reserved state
            - switches: List of all switches with current position
            - signals: List of all signals with current aspect
            - routes: List of all routes with lock state
            - feedbacks: List of all feedback sensors with state
        """
        import time as time_module

        state = {
            "timestamp": time_module.time(),
            "clock": {
                "hour": self.clock.hour,
                "minute": self.clock.minute,
                "divider": getattr(self.clock, "divider", 1),
                "freeze": getattr(self.clock, "freeze", False),
            },
            "locomotives": [
                {
                    "id": lc.idx,
                    "speed": getattr(lc, "V", 0),
                    "direction": getattr(lc, "dir", True),
                    "block": getattr(lc, "blockid", None),
                    "destblock": getattr(lc, "destblockid", None),
                    "mode": getattr(lc, "mode", None),
                    "functions": getattr(lc, "fn", []),
                }
                for lc in self._lc_domain.values()
            ],
            "blocks": [
                {
                    "id": bk.idx,
                    "occupied": getattr(bk, "occ", False),
                    "reserved": getattr(bk, "reserved", False),
                    "loco_id": getattr(bk, "locid", None),
                    "state": getattr(bk, "state", None),
                }
                for bk in self._bk_domain.values()
            ],
            "switches": [{"id": sw.idx, "state": sw.state, "type": getattr(sw, "type", None)} for sw in self._sw_domain.values()],
            "signals": [{"id": sg.idx, "aspect": getattr(sg, "aspect", None), "state": sg.state} for sg in self._sg_domain.values()],
            "routes": [{"id": st.idx, "status": getattr(st, "status", None)} for st in self._st_domain.values()],
            "feedbacks": [{"id": fb.idx, "state": fb.state} for fb in self._fb_domain.values()],
            "outputs": [{"id": co.idx, "state": getattr(co, "state", None)} for co in self._co_domain.values()],
        }

        return state
