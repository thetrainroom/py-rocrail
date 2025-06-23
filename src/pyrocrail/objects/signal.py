import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Signal:
    def __init__(self, sg_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com
        
        # State attributes
        self.state = "red"  # Current aspect: red, green, yellow, white
        self.aspect = 0  # Numeric aspect value
        self.cmd = ""  # Last command
        
        # Configuration attributes
        self.addr = 0  # Signal address
        self.port = 0  # Signal port
        self.gate = 0  # Gate timing
        self.type = "light"  # Signal type: light, semaphore, dwarf
        self.aspects = 2  # Number of aspects (2, 3, 4)
        self.dwarf = False  # Dwarf signal flag
        self.distant = False  # Distant signal flag
        
        self.build(sg_xml)

    def build(self, sg_xml: ET.Element):
        self.idx = sg_xml.attrib['id']
        for attr, value in sg_xml.attrib.items():
            set_attr(self, attr, value)
            
    def red(self):
        """Set signal to red (stop)"""
        cmd = f'<sg id="{self.idx}" cmd="red"/>'
        self.communicator.send("sg", cmd)
        self.state = "red"
        self.aspect = 0
        
    def green(self):
        """Set signal to green (go)"""
        cmd = f'<sg id="{self.idx}" cmd="green"/>'
        self.communicator.send("sg", cmd)
        self.state = "green"
        self.aspect = 1
        
    def yellow(self):
        """Set signal to yellow (caution)"""
        cmd = f'<sg id="{self.idx}" cmd="yellow"/>'
        self.communicator.send("sg", cmd)
        self.state = "yellow"
        self.aspect = 2
        
    def white(self):
        """Set signal to white (shunt)"""
        cmd = f'<sg id="{self.idx}" cmd="white"/>'
        self.communicator.send("sg", cmd)
        self.state = "white"
        self.aspect = 3
        
    def set_aspect(self, aspect):
        """Set signal to specific aspect"""
        if isinstance(aspect, int):
            aspect_map = {0: "red", 1: "green", 2: "yellow", 3: "white"}
            if aspect in aspect_map:
                getattr(self, aspect_map[aspect])()
            else:
                # TODO: Handle invalid aspect number
                raise ValueError(f"Invalid aspect number: {aspect}")
        elif isinstance(aspect, str):
            aspect_lower = aspect.lower()
            if aspect_lower in ["red", "stop"]:
                self.red()
            elif aspect_lower in ["green", "go", "clear"]:
                self.green()
            elif aspect_lower in ["yellow", "caution", "approach"]:
                self.yellow()
            elif aspect_lower in ["white", "shunt"]:
                self.white()
            else:
                # TODO: Handle invalid aspect name
                raise ValueError(f"Invalid aspect name: {aspect}")
                
    def next_aspect(self):
        """Cycle to next aspect"""
        # TODO: Verify aspect cycling behavior
        current_aspects = ["red", "green", "yellow", "white"]
        try:
            current_index = current_aspects.index(self.state)
            next_index = (current_index + 1) % min(self.aspects, len(current_aspects))
            self.set_aspect(next_index)
        except ValueError:
            self.red()  # Default to red if current state unknown
            
    def auto(self):
        """Set signal to automatic mode"""
        # TODO: Verify auto command format
        cmd = f'<sg id="{self.idx}" cmd="auto"/>'
        self.communicator.send("sg", cmd)
        
    def manual(self):
        """Set signal to manual mode"""
        # TODO: Verify manual command format
        cmd = f'<sg id="{self.idx}" cmd="manual"/>'
        self.communicator.send("sg", cmd)