import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Car:
    """Rolling stock/freight car object

    Represents individual cars (wagons) that can be assigned to operators (trains).
    Supports status changes (empty/loaded/maintenance) and waybill assignment.
    """

    def __init__(self, car_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com

        # State attributes
        self.status = "empty"  # empty, loaded, maintenance
        self.location = ""  # Current location
        self.waybill = ""  # Assigned waybill ID
        self.fn = {}  # Function states (key = function number, value = state)

        # Configuration attributes
        self.type = "freight"  # Car type: freight, passenger, etc.
        self.subtype = ""  # Specific subtype
        self.roadname = ""  # Railroad company name
        self.number = ""  # Car number
        self.color = ""  # Car color
        self.owner = ""  # Owner
        self.home = ""  # Home location
        self.len = 0  # Length in mm
        self.weight_empty = 0  # Empty weight
        self.weight_loaded = 0  # Loaded weight
        self.maxloadweight = 0  # Maximum load weight

        # Decoder attributes
        self.addr = 0  # Decoder address
        self.fncnt = 32  # Function count
        self.uselights = False  # Use lights
        self.fnlights = 0  # Function number for lights

        self.build(car_xml)

    def build(self, car_xml: ET.Element):
        """Build car object from XML element"""
        self.idx = car_xml.attrib["id"]
        for attr, value in car_xml.attrib.items():
            set_attr(self, attr, value)

    def empty(self):
        """Set car status to empty"""
        cmd = f'<car id="{self.idx}" cmd="empty"/>'
        self.communicator.send("car", cmd)
        self.status = "empty"

    def loaded(self):
        """Set car status to loaded"""
        cmd = f'<car id="{self.idx}" cmd="loaded"/>'
        self.communicator.send("car", cmd)
        self.status = "loaded"

    def maintenance(self):
        """Set car to maintenance status"""
        cmd = f'<car id="{self.idx}" cmd="maintenance"/>'
        self.communicator.send("car", cmd)
        self.status = "maintenance"

    def assign_waybill(self, waybill_id: str):
        """Assign a waybill to this car

        Args:
            waybill_id: Waybill ID to assign
        """
        cmd = f'<car id="{self.idx}" cmd="assignwaybill" waybill="{waybill_id}"/>'
        self.communicator.send("car", cmd)
        self.waybill = waybill_id

    def reset_waybill(self):
        """Reset/clear the waybill assignment"""
        cmd = f'<car id="{self.idx}" cmd="resetwaybill"/>'
        self.communicator.send("car", cmd)
        self.waybill = ""

    def set_function(self, fn_num: int, state: bool) -> None:
        """Set decoder function state

        Args:
            fn_num: Function number (0-31)
            state: True for on, False for off

        Note:
            Cars with decoders (addr > 0) can have functions for lights, sound, etc.
            Uses <fn> tag format with all function states as required by Rocrail protocol.
        """
        # Initialize fn dict if needed
        if not hasattr(self, "fn") or not isinstance(self.fn, dict):
            self.fn = {}

        # Update function state
        self.fn[fn_num] = state

        # Build function state attributes (f0 through f31)
        fn_attrs = []
        for i in range(32):
            fn_state = "true" if self.fn.get(i, False) else "false"
            fn_attrs.append(f'f{i}="{fn_state}"')

        state_str = "true" if state else "false"

        # Build complete <fn> command with all required attributes
        cmd = f'<fn id="{self.idx}" fnchanged="{fn_num}" fnchangedstate="{state_str}" {" ".join(fn_attrs)}/>'
        self.communicator.send("fn", cmd)
