#!/usr/bin/env python3
"""Test staging block section parsing and querying

Verifies that staging blocks correctly parse and manage their sections.
"""

from ..tools.mock_communicator import create_mock_pyrocrail


def test_stage_section_parsing():
    """Test that sections are parsed from staging blocks"""
    print("=" * 80)
    print("TEST: Staging Block Section Parsing")
    print("=" * 80)

    pr, mock_com = create_mock_pyrocrail("tests/fixtures/pcap/rocrail_start.txt")
    mock_com.start()
    pr.model.init()

    # Get a staging block (SB_T0 from the PCAP has 4 sections)
    stage = pr.model.get_stage("SB_T0")
    assert stage is not None, "Should find SB_T0 staging block"

    # Check sections were parsed
    assert hasattr(stage, "sections"), "Stage should have sections attribute"
    assert len(stage.sections) > 0, "Staging block should have sections"

    print(f"\n  Staging block: {stage.idx}")
    print(f"  Total sections: {len(stage.sections)}")
    print(f"  Expected (totalsections): {stage.totalsections}")

    # Verify section count matches
    assert len(stage.sections) == stage.totalsections, \
        f"Section count {len(stage.sections)} should match totalsections {stage.totalsections}"

    mock_com.stop()
    print("\n  [+] Sections parsed correctly")
    return True


def test_section_attributes():
    """Test that section attributes are populated"""
    print("\n" + "=" * 80)
    print("TEST: Section Attributes")
    print("=" * 80)

    pr, mock_com = create_mock_pyrocrail("tests/fixtures/pcap/rocrail_start.txt")
    mock_com.start()
    pr.model.init()

    stage = pr.model.get_stage("SB_T0")
    assert stage is not None

    if len(stage.sections) > 0:
        section = stage.sections[0]

        print(f"\n  Section ID: {section.idx}")
        print(f"  Section number: {section.nr}")
        print(f"  Feedback ID: {section.fbid}")
        print(f"  Length: {section.len}")
        print(f"  Locomotive: {section.lcid if section.lcid else '(empty)'}")

        # Check required attributes exist
        assert hasattr(section, "idx"), "Section should have idx"
        assert hasattr(section, "nr"), "Section should have nr"
        assert hasattr(section, "fbid"), "Section should have fbid"
        assert hasattr(section, "len"), "Section should have len"
        assert hasattr(section, "lcid"), "Section should have lcid"

        # Check is_occupied works
        occupied = section.is_occupied()
        print(f"  Is occupied: {occupied}")
        assert isinstance(occupied, bool), "is_occupied should return bool"

    mock_com.stop()
    print("\n  [+] Section attributes correct")
    return True


def test_section_query_methods():
    """Test section query methods"""
    print("\n" + "=" * 80)
    print("TEST: Section Query Methods")
    print("=" * 80)

    pr, mock_com = create_mock_pyrocrail("tests/fixtures/pcap/rocrail_start.txt")
    mock_com.start()
    pr.model.init()

    stage = pr.model.get_stage("SB_T0")
    assert stage is not None

    # Test get_section_count
    count = stage.get_section_count()
    print(f"\n  Section count: {count}")
    assert count == len(stage.sections)

    # Test get_section_by_number
    section_0 = stage.get_section_by_number(0)
    assert section_0 is not None, "Should find section 0"
    assert section_0.nr == 0, "Section number should be 0"
    print(f"  Section 0: {section_0.idx}")

    # Test get_occupied_sections and get_free_sections
    occupied = stage.get_occupied_sections()
    free = stage.get_free_sections()
    print(f"  Occupied sections: {len(occupied)}")
    print(f"  Free sections: {len(free)}")
    assert len(occupied) + len(free) == count, "Occupied + free should equal total"

    # Test get_locomotives_in_staging
    locos = stage.get_locomotives_in_staging()
    print(f"  Locomotives in staging: {locos}")
    assert len(locos) == len(occupied), "Should have one loco per occupied section"

    # Test get_section by ID
    if len(stage.sections) > 0:
        section_id = stage.sections[0].idx
        found_section = stage.get_section(section_id)
        assert found_section is not None, f"Should find section {section_id}"
        assert found_section.idx == section_id

    mock_com.stop()
    print("\n  [+] All query methods work correctly")
    return True


def test_multiple_staging_blocks():
    """Test that multiple staging blocks each have their own sections"""
    print("\n" + "=" * 80)
    print("TEST: Multiple Staging Blocks")
    print("=" * 80)

    pr, mock_com = create_mock_pyrocrail("tests/fixtures/pcap/rocrail_start.txt")
    mock_com.start()
    pr.model.init()

    # Get multiple staging blocks
    stages = [
        pr.model.get_stage("SB_T0"),
        pr.model.get_stage("SB_T1"),
        pr.model.get_stage("SB_T2"),
    ]

    stages = [s for s in stages if s is not None]

    if len(stages) >= 2:
        print(f"\n  Found {len(stages)} staging blocks")

        for stage in stages:
            print(f"\n  {stage.idx}:")
            print(f"    Sections: {len(stage.sections)}")
            print(f"    Occupied: {len(stage.get_occupied_sections())}")
            print(f"    Free: {len(stage.get_free_sections())}")
            print(f"    Locomotives: {stage.get_locomotives_in_staging()}")

            # Each stage should have its own sections
            assert len(stage.sections) > 0, f"{stage.idx} should have sections"

        # Verify sections are independent (different IDs)
        section_ids_0 = {s.idx for s in stages[0].sections}
        section_ids_1 = {s.idx for s in stages[1].sections}
        assert section_ids_0.isdisjoint(section_ids_1), \
            "Different staging blocks should have different section IDs"

    mock_com.stop()
    print("\n  [+] Multiple staging blocks handled correctly")
    return True


def test_front_and_exit_locomotives():
    """Test getting front and exit locomotives"""
    print("\n" + "=" * 80)
    print("TEST: Front and Exit Locomotives")
    print("=" * 80)

    pr, mock_com = create_mock_pyrocrail("tests/fixtures/pcap/rocrail_start.txt")
    mock_com.start()
    pr.model.init()

    stage = pr.model.get_stage("SB_T0")
    assert stage is not None

    # Get front locomotive (section 0 or lowest occupied)
    front_loco = stage.get_front_locomotive()
    print(f"\n  Front locomotive: {front_loco}")

    # Get exit locomotive (highest section or last occupied)
    exit_loco = stage.get_exit_locomotive()
    print(f"  Exit locomotive: {exit_loco}")

    if len(stage.get_occupied_sections()) > 0:
        assert front_loco is not None, "Should have front loco if sections occupied"
        assert exit_loco is not None, "Should have exit loco if sections occupied"

        # Get entry and exit sections
        entry = stage.get_entry_section()
        exit_sec = stage.get_exit_section()

        assert entry is not None, "Should have entry section"
        assert exit_sec is not None, "Should have exit section"

        print(f"  Entry section: {entry.idx} (nr={entry.nr})")
        print(f"  Exit section: {exit_sec.idx} (nr={exit_sec.nr})")

        # Exit section should have highest number
        assert exit_sec.nr >= entry.nr, "Exit section should be >= entry section"

        # If all sections occupied, front should be in entry, exit in exit section
        if len(stage.get_free_sections()) == 0:
            assert front_loco == entry.lcid, "Front loco should be in entry section when full"
            assert exit_loco == exit_sec.lcid, "Exit loco should be in exit section when full"

    mock_com.stop()
    print("\n  [+] Front/exit locomotive queries work correctly")
    return True


def main():
    """Run all staging section tests"""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "STAGING BLOCK SECTION TESTS")
    print("=" * 80)
    print()

    results = []
    results.append(test_stage_section_parsing())
    results.append(test_section_attributes())
    results.append(test_section_query_methods())
    results.append(test_multiple_staging_blocks())
    results.append(test_front_and_exit_locomotives())

    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    print("\nAll staging section tests passed!")
    print("\nVerified:")
    print("  [+] Sections parsed from <section> child elements")
    print("  [+] Section attributes populated correctly")
    print("  [+] Query methods work (get_section, get_occupied_sections, etc.)")
    print("  [+] Multiple staging blocks maintain independent sections")
    print("  [+] Front/exit locomotive queries work correctly")

    print()
    return all(results)


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
