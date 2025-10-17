# PCAP-Based Testing Guide for PyRocrail

**Purpose**: Use real Rocrail network captures to create realistic tests
**Date**: 2025-10-12

---

## 1. Overview

Capturing real Rocrail communication provides authentic test data including:
- Exact XML message formats
- Real state update sequences
- Timing and ordering of events
- Error scenarios and edge cases
- Complete request/response pairs

---

## 2. Capturing PCAP Files

### 2.1 Using Wireshark (Windows/Cross-platform)

1. **Install Wireshark**: https://www.wireshark.org/download.html

2. **Start Capture**:
   - Open Wireshark
   - Select your network interface (usually "Loopback: lo0" for localhost or your Ethernet/WiFi adapter)
   - Start capture

3. **Apply Filter** (optional during capture):
   ```
   tcp.port == 8051
   ```

4. **Run Your Layout**:
   - Start Rocrail
   - Run your test scenario (trains moving, switches changing, etc.)
   - Let it run for a few minutes to capture various events

5. **Stop Capture** and **Save**:
   - File → Save As
   - Choose location: `tests/fixtures/pcap/`
   - Filename examples:
     - `startup_and_plan.pcap` - Initial connection and plan loading
     - `locomotive_control.pcap` - Moving trains
     - `feedback_events.pcap` - Sensor activations
     - `full_session.pcap` - Complete operating session

### 2.2 Using tcpdump (Linux/macOS)

```bash
# Capture on loopback interface (localhost)
sudo tcpdump -i lo -w tests/fixtures/pcap/rocrail_capture.pcap port 8051

# Capture on specific interface
sudo tcpdump -i eth0 -w tests/fixtures/pcap/rocrail_capture.pcap port 8051

# Stop with Ctrl+C
```

### 2.3 Using tshark (Command-line Wireshark)

```bash
# Install tshark (comes with Wireshark)
# Capture for 5 minutes
tshark -i lo -f "tcp port 8051" -w tests/fixtures/pcap/rocrail_5min.pcap -a duration:300
```

---

## 3. Recommended Capture Scenarios

Create separate PCAP files for different scenarios:

### 3.1 Basic Scenarios

1. **`connection_and_plan.pcap`**
   - Start PyRocrail
   - Connect to Rocrail
   - Receive plan
   - Stop

2. **`locomotive_basic.pcap`**
   - Set speed 0 → 50 → 100 → 0
   - Change direction
   - Toggle lights
   - Activate functions

3. **`feedback_sensors.pcap`**
   - Manually trigger feedback sensors
   - Watch automatic detection from trains

4. **`block_operations.pcap`**
   - Reserve block
   - Train enters block
   - Block occupied event
   - Block freed

5. **`switch_control.pcap`**
   - Switch straight/turnout
   - Multiple switches in sequence

6. **`route_activation.pcap`**
   - Activate route
   - Watch switches change
   - Route locked/unlocked

7. **`clock_sync.pcap`**
   - Let fast clock run for a few minutes
   - Capture clock updates

### 3.2 Advanced Scenarios

8. **`auto_mode.pcap`**
   - Enable auto mode
   - Watch automated train movements
   - Dispatch/collect operations

9. **`error_scenarios.pcap`**
   - Invalid commands (unknown loco ID)
   - Short circuits
   - Emergency stop

10. **`long_session.pcap`**
    - 30-60 minute operating session
    - Multiple trains running
    - All object types in use

---

## 4. Extracting Data from PCAP

### 4.1 Python PCAP Parser

Create `tests/tools/pcap_parser.py`:

```python
#!/usr/bin/env python3
"""
Parse Rocrail PCAP files and extract XML messages
"""

import sys
from pathlib import Path
try:
    from scapy.all import rdpcap, TCP
except ImportError:
    print("Install scapy: pip install scapy")
    sys.exit(1)


class RocrailPcapParser:
    """Parse PCAP files and extract Rocrail XML messages"""

    def __init__(self, pcap_file):
        self.pcap_file = pcap_file
        self.packets = rdpcap(str(pcap_file))
        self.messages = []

    def extract_messages(self):
        """Extract all Rocrail XML messages from PCAP"""
        tcp_streams = {}

        for packet in self.packets:
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

    def _parse_rocrail_messages(self, data, stream_key):
        """Parse Rocrail XML messages from byte stream"""
        # Rocrail messages are null-terminated
        messages = data.split(b'\x00')

        for msg in messages:
            if b'<?xml' in msg:
                try:
                    xml_str = msg.decode('utf-8')
                    self.messages.append({
                        'direction': 'client→server' if stream_key[0] > stream_key[1] else 'server→client',
                        'xml': xml_str,
                        'stream': stream_key,
                    })
                except UnicodeDecodeError:
                    pass

    def save_messages(self, output_file):
        """Save extracted messages to file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, msg in enumerate(self.messages):
                f.write(f"\n{'='*80}\n")
                f.write(f"Message {i+1}: {msg['direction']}\n")
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
        sys.exit(1)

    pcap_file = Path(sys.argv[1])
    output_file = sys.argv[2] if len(sys.argv) > 2 else pcap_file.with_suffix('.txt')

    parser = RocrailPcapParser(pcap_file)
    messages = parser.extract_messages()

    print(f"Extracted {len(messages)} messages")

    # Print summary
    server_to_client = parser.filter_by_direction('server→client')
    client_to_server = parser.filter_by_direction('client→server')

    print(f"  Server → Client: {len(server_to_client)}")
    print(f"  Client → Server: {len(client_to_server)}")

    # Save to file
    parser.save_messages(output_file)
    print(f"\nSaved to: {output_file}")
```

### 4.2 Usage

```bash
# Install scapy
pip install scapy

# Extract messages from PCAP
python tests/tools/pcap_parser.py tests/fixtures/pcap/locomotive_control.pcap

# Output will be in tests/fixtures/pcap/locomotive_control.txt
```

---

## 5. PCAP Replay for Testing

### 5.1 PCAP-Based Mock Server

Create `tests/integration/pcap_mock_server.py`:

```python
"""
Mock Rocrail server that replays messages from PCAP capture
"""

import threading
import socket
import time
from pathlib import Path
from typing import List, Dict
import xml.etree.ElementTree as ET


class PcapMockServer:
    """Mock server that replays captured Rocrail messages"""

    def __init__(self, pcap_file: Path, port: int = 18051):
        self.pcap_file = pcap_file
        self.port = port
        self.messages = []  # Server→Client messages to replay
        self.received = []  # Client→Server messages received
        self._socket = None
        self._client = None
        self._thread = None
        self._running = False

        # Load messages from PCAP
        self._load_messages()

    def _load_messages(self):
        """Load server messages from extracted PCAP"""
        # Read from .txt file created by pcap_parser.py
        txt_file = self.pcap_file.with_suffix('.txt')

        if not txt_file.exists():
            raise FileNotFoundError(f"Extract PCAP first: {txt_file}")

        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse messages
        sections = content.split('='*80)
        for section in sections:
            if 'server→client' in section and '<?xml' in section:
                # Extract XML
                xml_start = section.find('<?xml')
                if xml_start >= 0:
                    xml_msg = section[xml_start:].strip()
                    self.messages.append(xml_msg)

    def start(self):
        """Start mock server"""
        self._running = True
        self._thread = threading.Thread(target=self._run_server)
        self._thread.start()
        time.sleep(0.5)  # Give server time to start

    def stop(self):
        """Stop mock server"""
        self._running = False
        if self._client:
            self._client.close()
        if self._socket:
            self._socket.close()
        if self._thread:
            self._thread.join()

    def _run_server(self):
        """Server thread"""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('localhost', self.port))
        self._socket.listen(1)
        self._socket.settimeout(1.0)

        try:
            while self._running:
                try:
                    self._client, addr = self._socket.accept()
                    self._handle_client()
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"Server error: {e}")

    def _handle_client(self):
        """Handle client connection"""
        self._client.settimeout(0.1)
        msg_index = 0

        while self._running and msg_index < len(self.messages):
            # Check for incoming client messages
            try:
                data = self._client.recv(4096)
                if data:
                    self.received.append(data.decode('utf-8'))

                    # Send next server message in response
                    if msg_index < len(self.messages):
                        msg = self.messages[msg_index]
                        self._client.send(msg.encode('utf-8') + b'\x00')
                        msg_index += 1
            except socket.timeout:
                pass
            except Exception as e:
                break

            time.sleep(0.01)


class PcapScenarioPlayer:
    """Play back captured scenarios for testing"""

    def __init__(self, scenario_name: str):
        self.scenario_name = scenario_name
        self.pcap_file = Path(f"tests/fixtures/pcap/{scenario_name}.pcap")
        self.server = None

    def __enter__(self):
        """Start server on context enter"""
        self.server = PcapMockServer(self.pcap_file)
        self.server.start()
        return self.server

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop server on context exit"""
        if self.server:
            self.server.stop()
```

### 5.2 PCAP-Based Tests

Create `tests/integration/test_pcap_scenarios.py`:

```python
"""
Tests using real PCAP captures
"""

import pytest
import time
from pyrocrail import PyRocrail
from tests.integration.pcap_mock_server import PcapScenarioPlayer


@pytest.mark.pcap
def test_connection_from_pcap():
    """Test connection using captured PCAP"""
    with PcapScenarioPlayer('connection_and_plan') as server:
        rr = PyRocrail('localhost', 18051)
        rr.start()

        # Plan should load
        time.sleep(1)
        assert rr.model.plan_recv == True

        rr.stop()


@pytest.mark.pcap
def test_locomotive_control_from_pcap():
    """Test locomotive control using captured PCAP"""
    with PcapScenarioPlayer('locomotive_basic') as server:
        rr = PyRocrail('localhost', 18051)
        rr.start()
        time.sleep(0.5)

        lc = rr.model.get_lc('BR01')  # Adjust to your capture

        # Send commands (server will replay responses from PCAP)
        lc.set_speed(50)
        time.sleep(0.1)

        lc.set_direction(False)
        time.sleep(0.1)

        lc.set_lights(True)
        time.sleep(0.1)

        rr.stop()


@pytest.mark.pcap
def test_feedback_events_from_pcap():
    """Test feedback event handling using captured PCAP"""
    with PcapScenarioPlayer('feedback_sensors') as server:
        rr = PyRocrail('localhost', 18051)
        rr.start()
        time.sleep(0.5)

        # Server will send feedback events from capture
        time.sleep(2)

        # Verify feedback states updated
        fb = rr.model.get_fb('FB01')  # Adjust to your capture
        # Check state based on what was captured

        rr.stop()


@pytest.mark.pcap
def test_full_session_from_pcap():
    """Test complete operating session using captured PCAP"""
    with PcapScenarioPlayer('long_session') as server:
        rr = PyRocrail('localhost', 18051)
        rr.start()

        # Let it run through captured events
        time.sleep(5)

        # Verify state matches expectations
        assert rr.model.plan_recv == True

        rr.stop()
```

---

## 6. PCAP Analysis Tools

### 6.1 Message Statistics

Create `tests/tools/pcap_stats.py`:

```python
#!/usr/bin/env python3
"""
Analyze PCAP files and show statistics
"""

import sys
from pathlib import Path
from collections import Counter
import re


def analyze_pcap_messages(txt_file):
    """Analyze extracted PCAP messages"""

    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count message types
    tag_pattern = r'<(\w+)'
    tags = re.findall(tag_pattern, content)
    tag_counts = Counter(tags)

    # Direction counts
    server_to_client = content.count('server→client')
    client_to_server = content.count('client→server')

    # Command counts
    cmd_pattern = r'cmd="(\w+)"'
    commands = re.findall(cmd_pattern, content)
    cmd_counts = Counter(commands)

    # Print statistics
    print(f"\n{'='*60}")
    print(f"PCAP Analysis: {txt_file.name}")
    print(f"{'='*60}\n")

    print(f"Message Direction:")
    print(f"  Server → Client: {server_to_client}")
    print(f"  Client → Server: {client_to_server}")
    print(f"  Total: {server_to_client + client_to_server}\n")

    print(f"Top Message Types:")
    for tag, count in tag_counts.most_common(10):
        print(f"  {tag:20s}: {count:4d}")

    print(f"\nTop Commands:")
    for cmd, count in cmd_counts.most_common(10):
        print(f"  {cmd:20s}: {count:4d}")

    # Unique object IDs
    id_pattern = r'id="([^"]+)"'
    ids = re.findall(id_pattern, content)
    unique_ids = set(ids)
    print(f"\nUnique Objects: {len(unique_ids)}")
    print(f"  Sample: {', '.join(list(unique_ids)[:10])}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: pcap_stats.py <pcap_txt_file>")
        sys.exit(1)

    txt_file = Path(sys.argv[1])
    analyze_pcap_messages(txt_file)
```

### 6.2 Usage

```bash
python tests/tools/pcap_stats.py tests/fixtures/pcap/locomotive_control.txt
```

---

## 7. Directory Structure

```
tests/
├── fixtures/
│   └── pcap/
│       ├── connection_and_plan.pcap
│       ├── connection_and_plan.txt        # Extracted
│       ├── locomotive_basic.pcap
│       ├── locomotive_basic.txt
│       ├── feedback_sensors.pcap
│       ├── feedback_sensors.txt
│       ├── block_operations.pcap
│       ├── block_operations.txt
│       ├── route_activation.pcap
│       ├── route_activation.txt
│       ├── auto_mode.pcap
│       ├── auto_mode.txt
│       ├── long_session.pcap
│       ├── long_session.txt
│       └── README.md                      # Capture descriptions
├── tools/
│   ├── pcap_parser.py                     # Extract XML from PCAP
│   ├── pcap_stats.py                      # Analyze captures
│   └── README.md                          # Tool documentation
└── integration/
    ├── pcap_mock_server.py                # PCAP replay server
    └── test_pcap_scenarios.py             # PCAP-based tests
```

---

## 8. Workflow

### 8.1 Complete Workflow

```bash
# 1. Capture traffic
# Run Wireshark or tcpdump while operating layout

# 2. Save PCAP file
# Save to tests/fixtures/pcap/my_scenario.pcap

# 3. Extract messages
python tests/tools/pcap_parser.py tests/fixtures/pcap/my_scenario.pcap

# 4. Analyze messages
python tests/tools/pcap_stats.py tests/fixtures/pcap/my_scenario.txt

# 5. Write tests using PCAP
# Edit tests/integration/test_pcap_scenarios.py

# 6. Run tests
pytest tests/integration/test_pcap_scenarios.py -v -m pcap
```

### 8.2 Continuous Capture

Set up automated capture during development:

```bash
#!/bin/bash
# capture_during_dev.sh

PCAP_DIR="tests/fixtures/pcap"
DATE=$(date +%Y%m%d_%H%M%S)
PCAP_FILE="$PCAP_DIR/dev_session_$DATE.pcap"

echo "Starting capture: $PCAP_FILE"
echo "Press Ctrl+C to stop"

tcpdump -i lo -w "$PCAP_FILE" port 8051

echo "Capture saved: $PCAP_FILE"
echo "Extract with: python tests/tools/pcap_parser.py $PCAP_FILE"
```

---

## 9. Benefits of PCAP Testing

### 9.1 Advantages

✅ **Real data** - Exact messages from actual Rocrail
✅ **Complete coverage** - Captures all message types
✅ **Timing preserved** - Realistic event sequences
✅ **Reproducible** - Same data every test run
✅ **Regression testing** - Detect protocol changes
✅ **Documentation** - Shows actual communication patterns

### 9.2 Use Cases

1. **Protocol reverse engineering** - Understand undocumented features
2. **State update testing** - Verify state changes from server
3. **Error handling** - Capture error scenarios
4. **Performance testing** - Replay high-traffic sessions
5. **Regression testing** - Detect breaking changes
6. **Documentation** - Example messages for developers

---

## 10. Privacy and Sharing

### 10.1 What to Include in Git

✅ **Include**:
- Small, generic PCAP files (< 1MB)
- Extracted .txt files (anonymized)
- Basic scenarios (connection, simple commands)

❌ **Don't Include**:
- Large PCAP files (> 1MB) - use Git LFS
- Personal layout details (if sensitive)
- Long sessions with private data

### 10.2 Anonymizing Captures

```python
# tests/tools/anonymize_pcap.py

def anonymize_xml(xml_str):
    """Replace sensitive IDs with generic ones"""
    import re

    # Replace locomotive names
    xml_str = re.sub(r'id="[^"]+"', lambda m: f'id="LOCO{hash(m.group())%100:02d}"', xml_str)

    # Replace block names
    # Replace other sensitive info

    return xml_str
```

---

## 11. Integration with CI/CD

### 11.1 GitHub Actions with PCAP

```yaml
# .github/workflows/test.yml

- name: Run PCAP-based tests
  run: |
    poetry run pytest tests/integration/test_pcap_scenarios.py -m pcap -v
```

### 11.2 PCAP as Test Fixtures

Store small PCAP files in Git:

```gitattributes
# .gitattributes
*.pcap filter=lfs diff=lfs merge=lfs -text
```

---

## 12. Next Steps

1. **Start simple**: Capture basic connection + plan loading
2. **Extract messages**: Run pcap_parser.py
3. **Analyze**: Look at message formats and sequences
4. **Write tests**: Use extracted data in unit tests
5. **Build mock server**: Replay captures for integration tests
6. **Capture more**: Add scenarios as you develop features

---

## References

- [Wireshark](https://www.wireshark.org/)
- [Scapy Documentation](https://scapy.readthedocs.io/)
- [tcpdump Tutorial](https://www.tcpdump.org/manpages/tcpdump.1.html)
- [PCAP File Format](https://wiki.wireshark.org/Development/LibpcapFileFormat)
