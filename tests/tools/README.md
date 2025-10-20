# PCAP Analysis Tools

## Quick Start

```bash
# 1. Install scapy (or pyshark as alternative)
pip install scapy

# 2. Extract XML messages from PCAP
python tests/tools/pcap_parser.py your_capture.pcap

# 3. Analyze the messages
python tests/tools/pcap_stats.py your_capture.txt
```

## Tools

- **pcap_parser.py** - Extracts XML messages from PCAP files
- **pcap_stats.py** - Analyzes extracted messages and shows statistics
