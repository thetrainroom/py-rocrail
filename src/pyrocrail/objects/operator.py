import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Operator:
    """Train operator/composition object (shown as "Trains" in Rocview)

    Represents a train composition linking a locomotive to cars (rolling stock).
    Manages car assignment, loading/unloading operations.

    Note: In Rocrail's Rocview GUI, these appear in the "Trains" menu/list.
    The XML element is <operator>, but they are commonly referred to as "trains".
    """

    def __init__(self, opr_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com

        # State attributes
        self.lcid = ""  # Locomotive ID
        self.carids = ""  # Comma-separated list of car IDs
        self.cargo = "none"  # Cargo type
        self.location = ""  # Current location

        # Configuration attributes
        self.home = ""  # Home location
        self.class_ = ""  # Train class (using class_ to avoid Python keyword)
        self.roadname = ""  # Railroad company name
        self.V_max = 0  # Maximum velocity
        self.length = 0  # Total train length
        self.radius = 0  # Minimum radius
        self.commuter = False  # Commuter train flag

        self.build(opr_xml)

    def build(self, opr_xml: ET.Element):
        """Build operator object from XML element"""
        self.idx = opr_xml.attrib["id"]
        for attr, value in opr_xml.attrib.items():
            # Handle 'class' attribute specially (Python keyword)
            if attr == "class":
                set_attr(self, "class_", value)
            else:
                set_attr(self, attr, value)

    def empty_car(self, car_ids: str):
        """Empty specified cars

        Args:
            car_ids: Comma-separated list of car IDs to empty
        """
        cmd = f'<operator id="{self.idx}" cmd="emptycar" carids="{car_ids}"/>'
        self.communicator.send("operator", cmd)

    def load_car(self, car_ids: str):
        """Load specified cars

        Args:
            car_ids: Comma-separated list of car IDs to load
        """
        cmd = f'<operator id="{self.idx}" cmd="loadcar" carids="{car_ids}"/>'
        self.communicator.send("operator", cmd)

    def add_car(self, car_ids: str):
        """Add cars to this operator/train

        Args:
            car_ids: Comma-separated list of car IDs to add
        """
        cmd = f'<operator id="{self.idx}" cmd="addcar" carids="{car_ids}"/>'
        self.communicator.send("operator", cmd)
        # Update the carids list (simple append for now)
        if self.carids:
            self.carids += "," + car_ids
        else:
            self.carids = car_ids

    def leave_car(self, car_ids: str):
        """Remove cars from this operator/train

        Args:
            car_ids: Comma-separated list of car IDs to remove
        """
        cmd = f'<operator id="{self.idx}" cmd="leavecar" carids="{car_ids}"/>'
        self.communicator.send("operator", cmd)
        # Update the carids list (remove cars)
        if self.carids:
            car_list = self.carids.split(",")
            cars_to_remove = car_ids.split(",")
            car_list = [c for c in car_list if c not in cars_to_remove]
            self.carids = ",".join(car_list)
