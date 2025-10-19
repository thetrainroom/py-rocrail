#!/usr/bin/env python3
"""
Parse Rocrail PCAP files and extract XML messages
"""

import sys
from pathlib import Path

try:
    from scapy.all import rdpcap, TCP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("WARNING: scapy not available, will try pyshark as fallback")


class RocrailPcapParser:
    """Parse PCAP files and extract Rocrail XML messages"""

    def __init__(self, pcap_file):
        self.pcap_file = Path(pcap_file)
        self.messages = []

    def extract_messages(self):
        """Extract all Rocrail XML messages from PCAP"""
        if SCAPY_AVAILABLE:
            return self._extract_with_scapy()
        else:
            return self._extract_with_pyshark()

    def _extract_with_scapy(self):
        """Extract using scapy"""
        packets = rdpcap(str(self.pcap_file))
        tcp_streams = {}

        for packet in packets:
            if TCP in packet and packet[TCP].payload:
                # Build stream key
                stream_key = (
                    packet[TCP].sport,
                    packet[TCP].dport,
                )

                # Get payload
                payload = bytes(packet[TCP].payload)

                if stream_key not in tcp_streams:
                    tcp_streams[stream_key] = bytearray()

                tcp_streams[stream_key].extend(payload)

        # Parse messages from streams
        for stream_key, data in tcp_streams.items():
            self._parse_rocrail_messages(data, stream_key)

        return self.messages

    def _extract_with_pyshark(self):
        """Extract using pyshark (Wireshark wrapper)"""
        try:
            import pyshark
        except ImportError:
            print("ERROR: Neither scapy nor pyshark available")
            print("Install one of:")
            print("  pip install scapy")
            print("  pip install pyshark")
            sys.exit(1)

        cap = pyshark.FileCapture(str(self.pcap_file), display_filter='tcp.port==8051')

        for packet in cap:
            if hasattr(packet, 'tcp') and hasattr(packet.tcp, 'payload'):
                try:
                    payload = bytes.fromhex(packet.tcp.payload.replace(':', ''))
                    direction = f"{packet.tcp.srcport}→{packet.tcp.dstport}"
                    self._parse_rocrail_messages(payload, direction)
                except Exception:
                    pass

        cap.close()
        return self.messages

    def _parse_rocrail_messages(self, data, stream_key):
        """Parse Rocrail XML messages from byte stream"""
        # Rocrail messages are null-terminated
        if isinstance(data, bytearray):
            messages = data.split(b'\x00')
        else:
            messages = data.split(b'\x00')

        for msg in messages:
            if b'<?xml' in msg:
                try:
                    xml_str = msg.decode('utf-8')

                    # Determine direction based on port
                    if isinstance(stream_key, tuple):
                        # Port 8051 is server, higher ports are client
                        if stream_key[0] == 8051:
                            direction = 'server->client'
                        elif stream_key[1] == 8051:
                            direction = 'client->server'
                        else:
                            direction = 'unknown'
                    else:
                        direction = str(stream_key)

                    self.messages.append({
                        'direction': direction,
                        'xml': xml_str,
                        'stream': str(stream_key),
                    })
                except UnicodeDecodeError:
                    pass

    def save_messages(self, output_file):
        """Save extracted messages to file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, msg in enumerate(self.messages):
                f.write(f"\n{'='*80}\n")
                f.write(f"Message {i+1}: {msg['direction']} (stream: {msg['stream']})\n")
                f.write(f"{'='*80}\n")
                f.write(msg['xml'])
                f.write('\n')

    def filter_by_direction(self, direction):
        """Filter messages by direction"""
        return [m for m in self.messages if m['direction'] == direction]

    def filter_by_tag(self, tag):
        """Filter messages by XML tag"""
        return [m for m in self.messages if f'<{tag}' in m['xml']]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: pcap_parser.py <pcap_file> [output_file]")
        print("\nExample:")
        print("  python pcap_parser.py capture.pcap")
        print("  python pcap_parser.py capture.pcap output.txt")
        sys.exit(1)

    pcap_file = Path(sys.argv[1])

    if not pcap_file.exists():
        print(f"ERROR: File not found: {pcap_file}")
        sys.exit(1)

    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else pcap_file.with_suffix('.txt')

    print(f"Parsing PCAP file: {pcap_file}")
    parser = RocrailPcapParser(pcap_file)
    messages = parser.extract_messages()

    print(f"\nExtracted {len(messages)} messages")

    # Print summary
    server_to_client = parser.filter_by_direction('server->client')
    client_to_server = parser.filter_by_direction('client->server')

    print(f"  Server -> Client: {len(server_to_client)}")
    print(f"  Client -> Server: {len(client_to_server)}")

    # Save to file
    parser.save_messages(output_file)
    print(f"\nSaved to: {output_file}")
    print("\nNext steps:")
    print(f"  1. View messages: cat {output_file} | less")
    print(f"  2. Analyze: python tests/tools/pcap_stats.py {output_file}")
