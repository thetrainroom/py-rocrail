#!/usr/bin/env python3
"""Test MockCommunicator with all available PCAP files"""

import time
from tests.tools.mock_communicator import create_mock_pyrocrail
from pathlib import Path


def test_pcap_file(pcap_path: str):
    """Test loading and basic operations with a PCAP file"""
    print("="*80)
    print(f"Testing: {Path(pcap_path).name}")
    print("="*80)

    try:
        # Create and load
        pr, mock_com = create_mock_pyrocrail(pcap_path)
        mock_com.start()
        pr.model.init()

        # Count what was loaded
        counts = {
            'Feedback sensors': len(pr.model._fb_domain),
            'Outputs': len(pr.model._co_domain),
            'Locomotives': len(pr.model._lc_domain),
            'Switches': len(pr.model._sw_domain),
            'Signals': len(pr.model._sg_domain),
            'Routes': len(pr.model._st_domain),
            'Blocks': len(pr.model._bk_domain),
            'Cars': len(pr.model._car_domain),
            'Operators': len(pr.model._operator_domain),
            'Schedules': len(pr.model._sc_domain),
            'Stages': len(pr.model._sb_domain),
        }

        print("\nModel loaded:")
        for name, count in counts.items():
            if count > 0:
                print(f"  {name:20s}: {count:4d}")

        # Test state update if we have objects
        if len(pr.model._fb_domain) > 0:
            fb_id = list(pr.model._fb_domain.keys())[0]
            fb = pr.model._fb_domain[fb_id]

            mock_com.inject_message(f'<fb id="{fb_id}" state="true"/>')
            time.sleep(0.05)

            if hasattr(fb, 'state') and fb.state:
                print(f"\n[OK] State updates work (tested with {fb_id})")
            else:
                print(f"\n[FAIL] State update failed for {fb_id}")

        mock_com.stop()
        print("\n[OK] PCAP loaded successfully\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] Error loading PCAP: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Test all PCAP files"""
    print("\n")
    print("="*80)
    print(" "*25 + "ALL PCAP FILES TEST")
    print("="*80)
    print()

    pcap_files = [
        "tests/fixtures/pcap/rocrail_start.txt",
        "tests/fixtures/pcap/rocrail_fahren.txt",
        "tests/fixtures/pcap/rocrail_schalten.txt",
        "tests/fixtures/pcap/rocrail_edit.txt",
    ]

    results = []
    for pcap_file in pcap_files:
        if Path(pcap_file).exists():
            results.append(test_pcap_file(pcap_file))
        else:
            print(f"[SKIP] {pcap_file} not found\n")

    print("="*80)
    print("SUMMARY")
    print("="*80)

    passed = sum(results)
    total = len(results)

    print(f"\nPCAP files tested: {passed}/{total} successful")

    if all(results):
        print("\n[SUCCESS] All PCAP files work with MockCommunicator!")
        print("\nYou can use any of these captures for testing:")
        for pcap_file in pcap_files:
            if Path(pcap_file).exists():
                print(f"  - {Path(pcap_file).name}")
    else:
        print("\n[WARNING] Some PCAP files had issues")

    print()


if __name__ == "__main__":
    main()
