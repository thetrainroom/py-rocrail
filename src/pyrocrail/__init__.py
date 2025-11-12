import logging
from .pyrocrail import PyRocrail, Action, Trigger
from .model import Model, Clock
from .communicator import Communicator
from .objects.feedback import Feedback
from .objects.output import Output, Color
from .objects.locomotive import Locomotive
from .objects.switch import Switch, ThreeWaySwitch, SwitchPosition
from .objects.signal import Signal, SignalAspect
from .objects.route import Route, RouteState, SwitchCmd, OutputCmd
from .objects.block import Block, BlockState
from .objects.action import ActionCtrl

# Create single logger for entire library
# Users can configure it with: logging.getLogger('pyrocrail').setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())  # No output by default unless user configures

__all__ = [
    "PyRocrail",
    "Action",
    "Trigger",
    "Model",
    "Clock",
    "Communicator",
    "Feedback",
    "Output",
    "Color",
    "Locomotive",
    "Switch",
    "SwitchPosition",
    "ThreeWaySwitch",
    "Signal",
    "SignalAspect",
    "Route",
    "RouteState",
    "SwitchCmd",
    "OutputCmd",
    "Block",
    "BlockState",
    "ActionCtrl",
    "logger",  # Export logger for users who want to configure it
]
