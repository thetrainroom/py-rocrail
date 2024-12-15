import time
from typing import Callable
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, Future

from pyrocrail.model import Model
from pyrocrail.communicator import Communicator


class Trigger(Enum):
    TIME = 0
    EVENT = 1


class Action:
    def __init__(self, script: Callable, trigger_type: Trigger = Trigger.TIME, trigger="", condition: str = "", timeout: int | float = 60):
        self.script = script
        self.trigger_type = trigger_type
        self.trigger = trigger
        self.condition = condition
        self.timeout = timeout
        self._start_time = 0.0


class PyRocrail:
    def __init__(self, ip: str = "localhost", port: int = 8051):
        self.com = Communicator(ip, port)
        self.model = Model(self.com)
        self._event_actions: list[Action] = []
        self._time_actions: list[Action] = []
        self._executor = ThreadPoolExecutor()
        self.__threads: list[Future] = []
        self.running = True
        self.__clean_thread = None

    def __del__(self):
        self.stop()

    def start(self):
        self.com.start()
        self.model.init()
        self.model.time_callback = self._exec_time
        self.__clean_thread = threading.Thread(target=self.__clean)
        self.__clean_thread.start()

    def stop(self):
        self.running = False
        if self.__clean_thread is not None:
            self.__clean_thread.join()
        self.com.stop()

    def add(self, action: Action):
        if action.trigger_type == Trigger.TIME:
            self._time_actions.append(action)
        else:
            self._event_actions.append(action)

    def _exec_time(self):
        for ac in self._time_actions:
            ac._start_time = time.monotonic()
            self.__threads.append(self._executor.submit(ac.script, self.model))
        return

    def __clean(self):
        while self.running:
            if len(self.__threads) > 0:
                t = self.__threads.pop(0)
                if t.done():
                    exp = t.exception(0)
                    if exp:
                        print("Failed Thread:", repr(exp))
                    continue
                self.__threads.append(t)
