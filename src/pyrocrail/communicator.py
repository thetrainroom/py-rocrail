import threading
import time
from socket import socket, AF_INET, SOCK_STREAM, IPPROTO_TCP, TCP_NODELAY
import xml.etree.ElementTree as ET


def create_xml_msg(xml_type: str, xml_msg: str) -> str:
    return f'<xmlh><xml size="{len(xml_msg)}" name="{xml_type}"/></xmlh>{xml_msg}\n\x00'


class Communicator:
    def __init__(self, ip: str = "localhost", port: int = 8051):
        self.ip = ip
        self.port = port
        self.__thread = None
        self._byte_buffer: bytearray = bytearray()
        self.__buffer: list[str] = []
        self.run = False
        self.__s: socket | None = None
        self.model = None
        self.mutex = threading.Lock()

    def __del__(self):
        if self.__s is not None:
            self.__s.close()

    def send(self, xml_type: str, xml_msg: str) -> str:
        assert self.__s is not None
        xml = create_xml_msg(xml_type, xml_msg)
        print(xml)
        with self.mutex:
            self.__s.send(xml.encode("utf-8"))
        return xml

    def start(self):
        self.__thread = threading.Thread(target=self._recv)
        self.__thread.start()
        while not self.run:
            pass
        print(f"Connected to {self.ip}:{self.port}")

    def stop(self):
        self.run = False
        if self.__thread is not None:
            self.__thread.join()

    def _parse(self) -> int | None:
        pos = self._byte_buffer.find(0)
        if pos < 0:
            return None
        else:
            r = self._byte_buffer[: pos + 1].decode("utf-8")
            self._byte_buffer = self._byte_buffer[pos + 1 :]

        self.__buffer.extend(list(r.split("\n")))
        while "?xml" not in self.__buffer[0] and len(self.__buffer) > 0:
            self.__buffer.pop(0)
        if len(self.__buffer) == 0:
            return None

        end_pos = None
        for i in range(len(self.__buffer) - 1, 0, -1):
            if "\0" in self.__buffer[i]:
                end_pos = i
                break
            elif "?xml" in self.__buffer[i]:
                end_pos = i
        return end_pos

    def _decode(self, end_pos: int):
        line_buffer: list[str] = self.__buffer[:end_pos]
        self.__buffer = self.__buffer[end_pos:]
        line_buffer.insert(1, "<rocrail>")
        line_buffer.append("</rocrail>")
        rm_idx: list[int] = list()
        for i in range(1, len(line_buffer)):
            if "?xml" in line_buffer[i]:
                rm_idx.insert(0, i)
        for rm in rm_idx:
            line_buffer.pop(rm)

        r = "\n".join(line_buffer)
        try:
            root = ET.fromstring(r)
            self.model.decode(root)
        except Exception as e:
            print(repr(e))

    def _recv(self):
        self.__s = socket(AF_INET, SOCK_STREAM)
        self.__s.connect((self.ip, self.port))
        self.__s.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        self.__s.settimeout(2)
        self.run = True
        while self.run:
            try:
                with self.mutex:
                    self._byte_buffer.extend(self.__s.recv(2048))
            except KeyboardInterrupt:
                self.run = False
                break
            except TimeoutError:
                time.sleep(0.1)
                continue

            end_pos = -1
            while end_pos is not None:
                end_pos = self._parse()
                if end_pos:
                    self._decode(end_pos)
        self.__s.close()
