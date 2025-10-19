#!/usr/bin/env python3
"""Mock Communicator that replays PCAP data for testing

Allows testing real PyRocrail/Model classes with PCAP input without needing a real server.
"""

import xml.etree.ElementTree as ET
from typing import Callable
import time
from pathlib import Path


class MockCommunicator:
    """Mock Communicator that replays messages from parsed PCAP .txt file

    Usage:
        mock_com = MockCommunicator("tests/fixtures/pcap/rocrail_start.txt")
        model = Model(mock_com)
        mock_com.start()  # Starts replaying messages
        model.init()      # Will receive plan from PCAP
    """

    def __init__(self, pcap_txt_file: str = None, replay_speed: float = 1.0):
        """
        Args:
            pcap_txt_file: Path to parsed PCAP .txt file to replay
            replay_speed: Speed multiplier (1.0 = real-time, 0 = instant, 2.0 = 2x speed)
        """
        self.pcap_txt_file = pcap_txt_file
        self.replay_speed = replay_speed
        self.messages = []
        self.message_index = 0
        self.running = False
        self.decode_callback: Callable[[ET.ElementTree], None] | None = None
        self.sent_messages = []  # Track what was sent (for testing)

        if pcap_txt_file:
            self._load_pcap_txt(pcap_txt_file)

    def _load_pcap_txt(self, txt_file: str):
        """Load and parse PCAP txt file"""
        print(f"Loading PCAP: {txt_file}")

        # Parse messages from txt file (same logic as pcap_replay_test.py)
        messages_xml = self._parse_pcap_txt(Path(txt_file))

        # Convert to XML elements
        for xml_str in messages_xml:
            try:
                # Skip XML declaration lines
                lines = xml_str.split('\n')
                xml_body_lines = [line for line in lines if not line.strip().startswith('<?xml')]

                # Wrap in root element
                wrapped_xml = '<rocrail>\n' + '\n'.join(xml_body_lines) + '\n</rocrail>'
                xml_root = ET.fromstring(wrapped_xml)

                self.messages.append(xml_root)
            except ET.ParseError:
                pass

        print(f"Loaded {len(self.messages)} XML messages from PCAP")

    def _parse_pcap_txt(self, txt_file: Path):
        """Extract XML messages from parsed PCAP text file"""
        messages = []

        with open(txt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        in_server_message = False
        current_xml = []

        for line in lines:
            # Check for message header
            if 'server->client' in line or 'server→client' in line:
                # Save previous message if we have one
                if current_xml:
                    xml_str = ''.join(current_xml).strip()
                    if xml_str:
                        messages.append(xml_str)
                    current_xml = []
                in_server_message = True
                continue

            # Check for client->server (skip these)
            if 'client->server' in line or 'client→server' in line:
                if current_xml:
                    xml_str = ''.join(current_xml).strip()
                    if xml_str:
                        messages.append(xml_str)
                    current_xml = []
                in_server_message = False
                continue

            # Check for separator
            if line.strip().startswith('='):
                if in_server_message and current_xml:
                    xml_str = ''.join(current_xml).strip()
                    if xml_str:
                        messages.append(xml_str)
                    current_xml = []
                continue

            # Collect XML content if we're in a server message
            if in_server_message and line.strip():
                current_xml.append(line)

        # Don't forget the last message
        if current_xml:
            xml_str = ''.join(current_xml).strip()
            if xml_str:
                messages.append(xml_str)

        return messages

    def start(self):
        """Start the mock communicator (doesn't actually connect)"""
        self.running = True
        print("MockCommunicator started (using PCAP data)")

    def stop(self):
        """Stop the mock communicator"""
        self.running = False
        print("MockCommunicator stopped")

    def send(self, msg_type: str, msg: str):
        """Mock send - just records what was sent

        Args:
            msg_type: Message type (e.g., 'lc', 'sw', 'fb')
            msg: XML message string
        """
        self.sent_messages.append({
            'type': msg_type,
            'message': msg,
            'timestamp': time.time()
        })
        # Could optionally print for debugging
        # print(f"[SEND] {msg_type}: {msg}")

    def get_next_message(self) -> ET.Element | None:
        """Get next message from PCAP replay

        Returns:
            XML element or None if no more messages
        """
        if self.message_index >= len(self.messages):
            return None

        msg = self.messages[self.message_index]
        self.message_index += 1
        return msg

    def replay_all(self, decode_callback: Callable[[ET.Element], None]):
        """Replay all messages to a callback (instant)

        Args:
            decode_callback: Function to call with each XML element
        """
        print(f"Replaying {len(self.messages)} messages...")
        for xml_root in self.messages:
            decode_callback(xml_root)
        print("Replay complete")

    def replay_until_plan(self, decode_callback: Callable[[ET.Element], None]):
        """Replay messages until plan is received (for model.init())

        Args:
            decode_callback: Function to call with each XML element
        """
        print("Replaying messages until plan received...")
        for xml_root in self.messages:
            decode_callback(xml_root)
            self.message_index += 1

            # Stop after plan is received (check children for plan tag)
            for child in xml_root:
                if child.tag == 'plan':
                    print(f"Plan received, replayed {self.message_index} messages")
                    return

        print(f"Warning: No plan found in PCAP, replayed all {len(self.messages)} messages")

    def get_sent_messages(self, msg_type: str | None = None) -> list:
        """Get messages that were sent via send()

        Args:
            msg_type: Filter by message type, or None for all

        Returns:
            List of sent messages
        """
        if msg_type is None:
            return self.sent_messages
        return [m for m in self.sent_messages if m['type'] == msg_type]

    def clear_sent_messages(self):
        """Clear the sent message history"""
        self.sent_messages = []

    def inject_message(self, xml_string: str):
        """Inject a custom XML message (for testing state changes)

        Args:
            xml_string: XML message as string (will be wrapped in <rocrail> if not already)
        """
        try:
            # Wrap in rocrail element if not already wrapped
            if not xml_string.strip().startswith('<rocrail'):
                wrapped_xml = f'<rocrail>{xml_string}</rocrail>'
            else:
                wrapped_xml = xml_string

            xml_root = ET.fromstring(wrapped_xml)
            if self.decode_callback:
                self.decode_callback(xml_root)
        except ET.ParseError as e:
            print(f"Warning: Failed to parse injected XML: {e}")


def create_mock_pyrocrail(pcap_txt_file: str = "tests/fixtures/pcap/rocrail_start.txt"):
    """Helper function to create PyRocrail with MockCommunicator

    Args:
        pcap_txt_file: Path to parsed PCAP .txt file

    Returns:
        Tuple of (PyRocrail instance, MockCommunicator instance)

    Example:
        pr, mock_com = create_mock_pyrocrail()
        pr.start()  # Will load from PCAP instead of real server

        # Now you can test triggers, actions, etc.
        pr.model.clock.hour = 12
        pr._exec_time()

        # Check what commands were sent
        lc_commands = mock_com.get_sent_messages('lc')
    """
    from pyrocrail.pyrocrail import PyRocrail

    # Create PyRocrail with dummy IP (won't be used)
    pr = PyRocrail("localhost", 8051)

    # Replace communicator with mock
    mock_com = MockCommunicator(pcap_txt_file)
    pr.com = mock_com
    pr.model.communicator = mock_com

    # Set decode callback immediately
    mock_com.decode_callback = pr.model.decode

    def mock_init():
        """Mock init that replays PCAP until plan is received"""
        mock_com.replay_until_plan(pr.model.decode)

    pr.model.init = mock_init

    return pr, mock_com
