import threading
import time
import atexit
import logging
from socket import socket, AF_INET, SOCK_STREAM, IPPROTO_TCP, TCP_NODELAY
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from pyrocrail.model import Model

# Use package-level logger
logger = logging.getLogger("pyrocrail")


def create_xml_msg(xml_type: str, xml_msg: str) -> str:
    return f'<xmlh><xml size="{len(xml_msg)}" name="{xml_type}"/></xmlh>{xml_msg}'


class Communicator:
    def __init__(
        self,
        ip: str = "localhost",
        port: int = 8051,
        verbose: bool = False,
        on_disconnect: Callable[["Model"], None] | None = None,
    ):
        self.ip = ip
        self.port = port
        self.__thread = None
        self._byte_buffer: bytearray = bytearray()
        self.__buffer: list[str] = []
        self.run = False
        self.__s: socket | None = None
        self.model: "Model | None" = None
        self.mutex = threading.Lock()
        self._stopped = False
        self.on_disconnect = on_disconnect
        self._disconnect_called = False  # Ensure callback only called once

        # Configure logging level based on verbose flag
        # verbose=True -> DEBUG (show all protocol messages)
        # verbose=False -> WARNING (default, only show issues)
        if verbose:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.WARNING)  # Explicitly set WARNING as default

        # Register cleanup handler
        atexit.register(self.stop)

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatic cleanup"""
        self.stop()
        return False

    def __del__(self):
        """Destructor - final backup cleanup"""
        self.stop()

    def send(self, xml_type: str, xml_msg: str) -> str:
        assert self.__s is not None
        xml = create_xml_msg(xml_type, xml_msg)
        logger.debug(f"SEND: {xml}")
        with self.mutex:
            self.__s.send(xml.encode("utf-8"))
        return xml

    def start(self):
        self.__thread = threading.Thread(target=self._recv, daemon=True)
        self.__thread.start()
        while not self.run:
            time.sleep(0.001)
        logger.info(f"Connected to Rocrail at {self.ip}:{self.port}")

    def stop(self):
        """Stop communicator and cleanup resources

        Safe to call multiple times (idempotent).
        """
        if self._stopped:
            return  # Already stopped

        self._stopped = True
        self.run = False

        # Stop receiver thread
        if self.__thread is not None and self.__thread.is_alive():
            self.__thread.join(timeout=2.0)

        # Close socket
        if self.__s is not None:
            try:
                self.__s.close()
            except Exception:
                pass
            self.__s = None

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
            assert self.model is not None
            self.model.decode(root)
            logger.debug(f"RECV: {ET.tostring(root, encoding='unicode')[:200]}...")
        except Exception as e:
            logger.error(f"XML decode error: {repr(e)}")

    def _recv(self):
        connection_lost = False
        try:
            self.__s = socket(AF_INET, SOCK_STREAM)
            self.__s.connect((self.ip, self.port))
            self.__s.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
            self.__s.settimeout(0.5)  # Reduced timeout for faster shutdown
            self.run = True
            while self.run:
                try:
                    with self.mutex:
                        data = self.__s.recv(2048)
                        if not data:
                            # Connection closed by server
                            logger.warning("Connection closed by Rocrail server")
                            connection_lost = True
                            break
                        self._byte_buffer.extend(data)
                except KeyboardInterrupt:
                    break
                except TimeoutError:
                    continue
                except OSError as e:
                    # Socket closed or network error
                    logger.warning(f"Network error: {e}")
                    connection_lost = True
                    break

                end_pos = -1
                while end_pos is not None:
                    end_pos = self._parse()
                    if end_pos:
                        self._decode(end_pos)
        except Exception as e:
            # Connection or network error during setup
            logger.error(f"Connection failed: {e}")
            connection_lost = True
        finally:
            self.run = False

            # Call disconnect callback if connection was lost unexpectedly
            # (not due to normal shutdown via stop() or server graceful shutdown)
            if connection_lost and not self._stopped and not self._disconnect_called:
                self._disconnect_called = True

                # Check if server sent shutdown message (graceful shutdown)
                graceful_shutdown = self.model and getattr(self.model, "server_shutting_down", False)

                if graceful_shutdown:
                    # Server shut down properly - no emergency action needed
                    logger.info("Server shutdown was graceful - emergency handler not called")
                elif self.on_disconnect and self.model:
                    # Unexpected disconnect - call emergency handler!
                    try:
                        logger.critical("UNEXPECTED DISCONNECT - Calling emergency handler")
                        self.on_disconnect(self.model)
                    except Exception as e:
                        logger.error(f"Disconnect handler failed: {e}")

            if self.__s is not None:
                try:
                    self.__s.close()
                except Exception:
                    pass
