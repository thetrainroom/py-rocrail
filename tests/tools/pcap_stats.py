#!/usr/bin/env python3
"""
Analyze PCAP files and show statistics
"""

import sys
from pathlib import Path
from collections import Counter
import re
import xml.etree.ElementTree as ET


def analyze_pcap_messages(txt_file):
    """Analyze extracted PCAP messages"""

    txt_file = Path(txt_file)

    if not txt_file.exists():
        print(f"ERROR: File not found: {txt_file}")
        print("Run pcap_parser.py first to extract messages")
        sys.exit(1)

    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count message types
    tag_pattern = r'<(\w+)'
    tags = re.findall(tag_pattern, content)
    tag_counts = Counter(tags)

    # Direction counts
    server_to_client = content.count('server->client')
    client_to_server = content.count('client->server')

    # Command counts
    cmd_pattern = r'cmd="(\w+)"'
    commands = re.findall(cmd_pattern, content)
    cmd_counts = Counter(commands)

    # Attribute analysis
    attr_pattern = r'(\w+)="[^"]*"'
    attrs = re.findall(attr_pattern, content)
    attr_counts = Counter(attrs)

    # Print statistics
    print(f"\n{'='*80}")
    print(f"PCAP Analysis: {txt_file.name}")
    print(f"{'='*80}\n")

    print("Message Direction:")
    print(f"  Server -> Client: {server_to_client:4d}")
    print(f"  Client -> Server: {client_to_server:4d}")
    print(f"  Total:            {server_to_client + client_to_server:4d}\n")

    print("Top Message Types (XML root tags):")
    for tag, count in tag_counts.most_common(15):
        if tag != 'xml':  # Skip XML declaration
            bar = '#' * min(50, count)
            print(f"  {tag:20s}: {count:4d} {bar}")

    if cmd_counts:
        print("\nTop Commands:")
        for cmd, count in cmd_counts.most_common(15):
            bar = '#' * min(50, count)
            print(f"  {cmd:20s}: {count:4d} {bar}")

    # Unique object IDs
    id_pattern = r'id="([^"]+)"'
    ids = re.findall(id_pattern, content)
    unique_ids = set(ids)
    print(f"\nUnique Object IDs: {len(unique_ids)}")
    if unique_ids:
        print(f"  Sample: {', '.join(sorted(list(unique_ids))[:15])}")

    # Common attributes
    print("\nTop Attributes Used:")
    for attr, count in attr_counts.most_common(10):
        if attr not in ['xml', 'version', 'encoding']:
            print(f"  {attr:20s}: {count:4d}")

    # State changes
    state_pattern = r'state="([^"]+)"'
    states = re.findall(state_pattern, content)
    if states:
        state_counts = Counter(states)
        print("\nState Values:")
        for state, count in state_counts.most_common(10):
            print(f"  {state:20s}: {count:4d}")

    # Find interesting patterns
    print(f"\n{'='*80}")
    print("Interesting Patterns:")
    print(f"{'='*80}")

    # Feedback events
    fb_events = len(re.findall(r'<fb\s', content))
    if fb_events:
        print(f"  Feedback sensor events: {fb_events}")

    # Block events
    bk_events = len(re.findall(r'<bk\s', content))
    if bk_events:
        print(f"  Block events: {bk_events}")

    # Locomotive events
    lc_events = len(re.findall(r'<lc\s', content))
    if lc_events:
        print(f"  Locomotive events: {lc_events}")

    # Clock events
    clock_events = len(re.findall(r'<clock\s', content))
    if clock_events:
        print(f"  Clock updates: {clock_events}")

    # Switch events
    sw_events = len(re.findall(r'<sw\s', content))
    if sw_events:
        print(f"  Switch events: {sw_events}")

    # Signal events
    sg_events = len(re.findall(r'<sg\s', content))
    if sg_events:
        print(f"  Signal events: {sg_events}")

    # System events
    sys_events = len(re.findall(r'<sys\s', content))
    if sys_events:
        print(f"  System events: {sys_events}")

    # Auto events
    auto_events = len(re.findall(r'<auto\s', content))
    if auto_events:
        print(f"  Auto mode events: {auto_events}")

    print()


def extract_unique_messages(txt_file):
    """Extract one example of each message type"""

    txt_file = Path(txt_file)
    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = content.split('='*80)
    unique_messages = {}

    for section in sections:
        if '<?xml' in section:
            # Extract XML
            xml_start = section.find('<?xml')
            if xml_start >= 0:
                xml_msg = section[xml_start:].strip()

                # Get root tag
                try:
                    root = ET.fromstring(xml_msg.split('\n')[0] + '</root>')
                    tag = root.tag

                    # Get command if present
                    cmd = root.attrib.get('cmd', 'no-cmd')

                    key = f"{tag}:{cmd}"
                    if key not in unique_messages:
                        unique_messages[key] = xml_msg[:200]  # First 200 chars
                except Exception:
                    pass

    print(f"\n{'='*80}")
    print("Unique Message Examples:")
    print(f"{'='*80}\n")

    for key, msg in sorted(unique_messages.items()):
        print(f"{key}:")
        print(f"  {msg}...\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: pcap_stats.py <pcap_txt_file>")
        print("\nExample:")
        print("  python pcap_stats.py capture.txt")
        sys.exit(1)

    txt_file = Path(sys.argv[1])
    analyze_pcap_messages(txt_file)

    # Ask if user wants to see examples
    print("\nWould you like to see unique message examples? (y/n)")
    # For now, skip interactive mode
    # extract_unique_messages(txt_file)
