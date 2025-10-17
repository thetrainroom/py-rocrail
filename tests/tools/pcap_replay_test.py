#!/usr/bin/env python3
"""
PCAP Replay Test Script

Feeds PCAP messages into PyRocrail to identify:
- Which messages are handled correctly
- Which messages are ignored/unhandled
- Which messages cause errors

Usage:
    python tests/tools/pcap_replay_test.py tests/fixtures/pcap/rocrail_start.txt
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List


class MessageStats:
    """Track message handling statistics"""

    def __init__(self):
        self.total = 0
        self.handled = 0
        self.unhandled = 0
        self.errors = 0
        self.by_tag = Counter()
        self.unhandled_by_tag = Counter()
        self.error_messages = []
        self.unhandled_examples = defaultdict(list)

    def add_handled(self, tag: str):
        self.total += 1
        self.handled += 1
        self.by_tag[tag] += 1

    def add_unhandled(self, tag: str, xml: str):
        self.total += 1
        self.unhandled += 1
        self.by_tag[tag] += 1
        self.unhandled_by_tag[tag] += 1
        # Store first 3 examples of each unhandled tag
        if len(self.unhandled_examples[tag]) < 3:
            self.unhandled_examples[tag].append(xml[:200])

    def add_error(self, tag: str, error: str, xml: str):
        self.total += 1
        self.errors += 1
        self.by_tag[tag] += 1
        self.error_messages.append({
            'tag': tag,
            'error': error,
            'xml': xml[:200]
        })

    def print_summary(self):
        print("\n" + "="*80)
        print("PCAP REPLAY TEST RESULTS")
        print("="*80)
        print(f"\nTotal Messages:      {self.total:4d}")
        if self.total > 0:
            print(f"  Handled:           {self.handled:4d} ({self.handled/self.total*100:.1f}%)")
            print(f"  Unhandled:         {self.unhandled:4d} ({self.unhandled/self.total*100:.1f}%)")
            print(f"  Errors:            {self.errors:4d} ({self.errors/self.total*100:.1f}%)")
        else:
            print("  No messages found to process!")

        print(f"\n{'='*80}")
        print("Unhandled Messages by Type:")
        print(f"{'='*80}")
        for tag, count in sorted(self.unhandled_by_tag.items(), key=lambda x: -x[1]):
            print(f"  {tag:20s}: {count:4d}")
            # Show examples
            if tag in self.unhandled_examples:
                for i, example in enumerate(self.unhandled_examples[tag], 1):
                    print(f"    Example {i}: {example}...")
                print()

        if self.error_messages:
            print(f"\n{'='*80}")
            print("Error Messages:")
            print(f"{'='*80}")
            for err in self.error_messages[:10]:  # Show first 10
                print(f"  Tag: {err['tag']}")
                print(f"  Error: {err['error']}")
                print(f"  XML: {err['xml']}...")
                print()


class MockModel:
    """
    Lightweight mock of Model that tracks what gets processed
    """

    def __init__(self, stats: MessageStats):
        self.stats = stats
        self._fb_domain = {}
        self._co_domain = {}
        self._lc_domain = {}
        self._sw_domain = {}
        self._sg_domain = {}
        self._st_domain = {}
        self._bk_domain = {}
        self._car_domain = {}
        self._operator_domain = {}
        self.plan_recv = False
        self.change_callback = None

        # Track which tags we can handle
        self.handled_tags = {
            'plan', 'fblist', 'colist', 'lclist', 'swlist',
            'sglist', 'stlist', 'bklist', 'carlist', 'operatorlist', 'clock',
            'lc', 'fb', 'bk', 'sw', 'sg', 'st', 'car', 'operator'  # Added state updates
        }

        # Tags we expect to see but don't handle yet
        self.known_unhandled_tags = {
            'exception', 'scentry', 'actionctrl',
            'actioncond', 'fbevent', 'tk', 'bbt', 'fundef', 'swcmd',
            'section', 'fn', 'vr', 'ping', 'auto', 'sys', 'state',
            'text', 'tt', 'stage', 'schedule', 'tour', 'location',
            'analyser', 'booster', 'link', 'var', 'seltab', 'weather'
        }

    def decode(self, xml_root: ET.Element):
        """Process incoming XML (mimics real Model.decode)"""

        for child in xml_root:
            tag = child.tag

            try:
                # Check if it's xmlh (header)
                if tag == 'xmlh':
                    self.stats.add_handled(tag)
                    continue

                # Check if we handle this tag
                if tag in self.handled_tags:
                    self.stats.add_handled(tag)
                    # In real model, this would call _build_* methods
                    if tag == 'plan':
                        self.plan_recv = True
                    # Simulate building object lists
                    elif tag == 'lclist':
                        for lc_child in child:
                            if lc_child.tag == 'lc' and 'id' in lc_child.attrib:
                                # Add to domain (mock)
                                self._lc_domain[lc_child.attrib['id']] = {'id': lc_child.attrib['id']}
                    elif tag == 'fblist':
                        for fb_child in child:
                            if fb_child.tag == 'fb' and 'id' in fb_child.attrib:
                                # Add to domain (mock)
                                self._fb_domain[fb_child.attrib['id']] = {'id': fb_child.attrib['id']}
                    elif tag == 'bklist':
                        for bk_child in child:
                            if bk_child.tag == 'bk' and 'id' in bk_child.attrib:
                                self._bk_domain[bk_child.attrib['id']] = {'id': bk_child.attrib['id']}
                    elif tag == 'swlist':
                        for sw_child in child:
                            if sw_child.tag == 'sw' and 'id' in sw_child.attrib:
                                self._sw_domain[sw_child.attrib['id']] = {'id': sw_child.attrib['id']}
                    elif tag == 'sglist':
                        for sg_child in child:
                            if sg_child.tag == 'sg' and 'id' in sg_child.attrib:
                                self._sg_domain[sg_child.attrib['id']] = {'id': sg_child.attrib['id']}
                    elif tag == 'stlist':
                        for st_child in child:
                            if st_child.tag == 'st' and 'id' in st_child.attrib:
                                self._st_domain[st_child.attrib['id']] = {'id': st_child.attrib['id']}
                    elif tag == 'carlist':
                        for car_child in child:
                            if car_child.tag == 'car' and 'id' in car_child.attrib:
                                self._car_domain[car_child.attrib['id']] = {'id': car_child.attrib['id']}
                    elif tag == 'operatorlist':
                        for opr_child in child:
                            if opr_child.tag == 'operator' and 'id' in opr_child.attrib:
                                self._operator_domain[opr_child.attrib['id']] = {'id': opr_child.attrib['id']}
                    continue

                # Check if it's an object state update
                if tag in ['fb', 'co', 'lc', 'sw', 'sg', 'st', 'bk', 'car', 'operator']:
                    # Check if it has an id (state update vs list)
                    if 'id' in child.attrib:
                        # This is a state update
                        # For lc and fb, we now handle them!
                        if tag == 'lc':
                            # Check if we have this locomotive in our domain
                            lc_id = child.attrib.get('id')
                            if lc_id in self._lc_domain:
                                # Update handled!
                                self.stats.add_handled(f"{tag}-state-update")
                            else:
                                # Unknown locomotive
                                self.stats.add_unhandled(
                                    f"{tag}-state-update-unknown",
                                    ET.tostring(child, encoding='unicode')
                                )
                        elif tag == 'fb':
                            # Check if we have this feedback sensor in our domain
                            fb_id = child.attrib.get('id')
                            if fb_id in self._fb_domain:
                                # Update handled!
                                self.stats.add_handled(f"{tag}-state-update")
                            else:
                                # Unknown feedback sensor
                                self.stats.add_unhandled(
                                    f"{tag}-state-update-unknown",
                                    ET.tostring(child, encoding='unicode')
                                )
                        elif tag == 'bk':
                            # Check if we have this block in our domain
                            bk_id = child.attrib.get('id')
                            if bk_id in self._bk_domain:
                                # Update handled!
                                self.stats.add_handled(f"{tag}-state-update")
                            else:
                                # Unknown block
                                self.stats.add_unhandled(
                                    f"{tag}-state-update-unknown",
                                    ET.tostring(child, encoding='unicode')
                                )
                        elif tag == 'sw':
                            # Check if we have this switch in our domain
                            sw_id = child.attrib.get('id')
                            if sw_id in self._sw_domain:
                                self.stats.add_handled(f"{tag}-state-update")
                            else:
                                self.stats.add_unhandled(
                                    f"{tag}-state-update-unknown",
                                    ET.tostring(child, encoding='unicode')
                                )
                        elif tag == 'sg':
                            # Check if we have this signal in our domain
                            sg_id = child.attrib.get('id')
                            if sg_id in self._sg_domain:
                                self.stats.add_handled(f"{tag}-state-update")
                            else:
                                self.stats.add_unhandled(
                                    f"{tag}-state-update-unknown",
                                    ET.tostring(child, encoding='unicode')
                                )
                        elif tag == 'st':
                            # Check if we have this route in our domain
                            st_id = child.attrib.get('id')
                            if st_id in self._st_domain:
                                self.stats.add_handled(f"{tag}-state-update")
                            else:
                                self.stats.add_unhandled(
                                    f"{tag}-state-update-unknown",
                                    ET.tostring(child, encoding='unicode')
                                )
                        elif tag == 'car':
                            # Check if we have this car in our domain
                            car_id = child.attrib.get('id')
                            if car_id in self._car_domain:
                                self.stats.add_handled(f"{tag}-state-update")
                            else:
                                self.stats.add_unhandled(
                                    f"{tag}-state-update-unknown",
                                    ET.tostring(child, encoding='unicode')
                                )
                        elif tag == 'operator':
                            # Check if we have this operator in our domain
                            operator_id = child.attrib.get('id')
                            if operator_id in self._operator_domain:
                                self.stats.add_handled(f"{tag}-state-update")
                            else:
                                self.stats.add_unhandled(
                                    f"{tag}-state-update-unknown",
                                    ET.tostring(child, encoding='unicode')
                                )
                        else:
                            # Other state updates not yet handled
                            self.stats.add_unhandled(
                                f"{tag}-state-update",
                                ET.tostring(child, encoding='unicode')
                            )
                    else:
                        # Object definition
                        self.stats.add_handled(tag)
                    continue

                # Known unhandled
                if tag in self.known_unhandled_tags:
                    self.stats.add_unhandled(
                        tag,
                        ET.tostring(child, encoding='unicode')
                    )
                    continue

                # Unknown tag - potential bug or new Rocrail feature
                self.stats.add_unhandled(
                    f"UNKNOWN:{tag}",
                    ET.tostring(child, encoding='unicode')
                )

            except Exception as e:
                self.stats.add_error(
                    tag,
                    str(e),
                    ET.tostring(child, encoding='unicode')
                )


def parse_pcap_txt(txt_file: Path) -> List[str]:
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


def replay_messages(messages: List[str], stats: MessageStats) -> MockModel:
    """Replay messages through mock model"""

    model = MockModel(stats)

    print(f"Replaying {len(messages)} messages...")
    print("(Messages that can't be decoded will be printed below)")
    print("="*80)

    for i, xml_str in enumerate(messages, 1):
        try:
            # Parse the XML
            # Need to wrap in root element since messages can have multiple children
            lines = xml_str.split('\n')

            # Skip the XML declaration
            xml_body_lines = [line for line in lines if not line.strip().startswith('<?xml')]

            # Wrap in a root element
            wrapped_xml = '<rocrail>\n' + '\n'.join(xml_body_lines) + '\n</rocrail>'

            root = ET.fromstring(wrapped_xml)

            # Process through model
            model.decode(root)

        except ET.ParseError as e:
            stats.add_error('PARSE_ERROR', str(e), xml_str)
            print(f"\n[Parse Error] Message {i}:")
            print(f"  Error: {e}")
            print(f"  XML: {xml_str[:200]}...")
            print()
        except Exception as e:
            stats.add_error('UNKNOWN_ERROR', str(e), xml_str)
            print(f"\n[Error] Message {i}:")
            print(f"  Error: {e}")
            print(f"  XML: {xml_str[:200]}...")
            print()

    return model


def main():
    if len(sys.argv) < 2:
        print("Usage: pcap_replay_test.py <pcap_txt_file>")
        print("\nExample:")
        print("  python tests/tools/pcap_replay_test.py tests/fixtures/pcap/rocrail_start.txt")
        print("\nAvailable captures:")
        pcap_dir = Path("tests/fixtures/pcap")
        if pcap_dir.exists():
            for f in pcap_dir.glob("*.txt"):
                print(f"  {f}")
        sys.exit(1)

    txt_file = Path(sys.argv[1])

    if not txt_file.exists():
        print(f"ERROR: File not found: {txt_file}")
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"PCAP Replay Test: {txt_file.name}")
    print(f"{'='*80}\n")

    # Parse messages from PCAP
    print("Extracting messages from PCAP...")
    messages = parse_pcap_txt(txt_file)
    print(f"Found {len(messages)} server->client messages\n")

    # Replay through mock model
    stats = MessageStats()
    model = replay_messages(messages, stats)

    # Print results
    stats.print_summary()

    # Summary recommendations
    print(f"\n{'='*80}")
    print("Recommendations:")
    print(f"{'='*80}")

    if stats.unhandled_by_tag.get('lc-state-update', 0) > 0:
        print("  [!] Locomotive state updates are NOT handled")
        print("      -> Implement: Model should update existing lc objects when <lc id=...> arrives")

    if stats.unhandled_by_tag.get('bk-state-update', 0) > 0:
        print("  [!] Block state updates are NOT handled")
        print("      -> Implement: Model should update existing bk objects when <bk id=...> arrives")

    if stats.unhandled_by_tag.get('fb-state-update', 0) > 0:
        print("  [!] Feedback state updates are NOT handled")
        print("      -> Implement: Model should update existing fb objects when <fb id=...> arrives")

    if stats.unhandled_by_tag.get('sw-state-update', 0) > 0:
        print("  [!] Switch state updates are NOT handled")
        print("      -> Implement: Model should update existing sw objects when <sw id=...> arrives")

    if stats.unhandled_by_tag.get('sg-state-update', 0) > 0:
        print("  [!] Signal state updates are NOT handled")
        print("      -> Implement: Model should update existing sg objects when <sg id=...> arrives")

    if stats.unhandled_by_tag.get('exception', 0) > 0:
        print(f"  [!] {stats.unhandled_by_tag['exception']} exception messages are ignored")
        print("      -> Implement: Parse <exception> tags and expose to Python scripts")

    if stats.unhandled_by_tag.get('car', 0) > 0:
        print(f"  [!] {stats.unhandled_by_tag['car']} car objects are ignored")
        print("      -> Implement: Car object class for rolling stock")

    if stats.unhandled_by_tag.get('operator', 0) > 0:
        print(f"  [!] {stats.unhandled_by_tag['operator']} operator objects are ignored")
        print("      -> Implement: Operator object class for train compositions")

    print("\n")


if __name__ == '__main__':
    main()
