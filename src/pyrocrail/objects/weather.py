import xml.etree.ElementTree as ET
from pyrocrail.objects import set_attr
from pyrocrail.communicator import Communicator


class Weather:
    """Weather object for atmospheric effects

    Weather controls atmospheric effects like lighting, sound, and visual
    effects to simulate different weather conditions and time of day.
    """

    def __init__(self, weather_xml: ET.Element, com: Communicator):
        self.idx = ""
        self.communicator = com
        self.build(weather_xml)

    def build(self, weather: ET.Element):
        self.idx = weather.attrib["id"]
        for attr, value in weather.attrib.items():
            if attr == "id":
                continue
            set_attr(self, attr, value)

    def setweather(self):
        """Set weather conditions"""
        cmd = f'<weather id="{self.idx}" cmd="setweather"/>'
        self.communicator.send("weather", cmd)

    def weathertheme(self):
        """Apply weather theme"""
        cmd = f'<weather id="{self.idx}" cmd="weathertheme"/>'
        self.communicator.send("weather", cmd)

    def go(self):
        """Start weather effects"""
        cmd = f'<weather id="{self.idx}" cmd="go"/>'
        self.communicator.send("weather", cmd)

    def stop(self):
        """Stop weather effects"""
        cmd = f'<weather id="{self.idx}" cmd="stop"/>'
        self.communicator.send("weather", cmd)
