#!/usr/bin/env python3
"""Test exception level mapping from Rocrail server

This tests that numeric exception levels (bit flags) are correctly
mapped to Python logging levels.
"""

import xml.etree.ElementTree as ET
import logging
from unittest.mock import MagicMock, patch
from pyrocrail.model import Model


def test_numeric_debug_level():
    """Test that level=16384 (0x4000 DEBUG) maps to logger.debug"""
    print("=" * 80)
    print("TEST: Numeric DEBUG Level (16384)")
    print("=" * 80)

    model = Model(MagicMock())

    with patch("pyrocrail.model.logger") as mock_logger:
        exception_xml = ET.fromstring(
            '<exception text="loco Test function 2 set to 1" level="16384" id="9999"/>'
        )
        model._handle_exception(exception_xml)

        # Verify logger.debug was called (not warning)
        assert mock_logger.debug.called, "DEBUG level should call logger.debug()"
        assert not mock_logger.warning.called, "DEBUG level should NOT call logger.warning()"

        # Check the message
        call_args = mock_logger.debug.call_args[0][0]
        assert "Rocrail debug:" in call_args
        assert "function 2 set to 1" in call_args

    print("  [+] Level 16384 correctly mapped to logger.debug()")
    return True


def test_numeric_exception_level():
    """Test that level=1 (EXCEPTION) maps to logger.error"""
    print("\n" + "=" * 80)
    print("TEST: Numeric EXCEPTION Level (1)")
    print("=" * 80)

    model = Model(MagicMock())

    with patch("pyrocrail.model.logger") as mock_logger:
        exception_xml = ET.fromstring(
            '<exception text="Critical error occurred" level="1" id="1234"/>'
        )
        model._handle_exception(exception_xml)

        assert mock_logger.error.called, "EXCEPTION level should call logger.error()"
        call_args = mock_logger.error.call_args[0][0]
        assert "Rocrail exception:" in call_args
        assert "Critical error" in call_args

    print("  [+] Level 1 correctly mapped to logger.error()")
    return True


def test_numeric_warning_level():
    """Test that level=2 (WARNING) maps to logger.warning"""
    print("\n" + "=" * 80)
    print("TEST: Numeric WARNING Level (2)")
    print("=" * 80)

    model = Model(MagicMock())

    with patch("pyrocrail.model.logger") as mock_logger:
        exception_xml = ET.fromstring(
            '<exception text="Track speed exceeded" level="2" id="5678"/>'
        )
        model._handle_exception(exception_xml)

        assert mock_logger.warning.called, "WARNING level should call logger.warning()"
        call_args = mock_logger.warning.call_args[0][0]
        assert "Rocrail warning:" in call_args
        assert "speed exceeded" in call_args

    print("  [+] Level 2 correctly mapped to logger.warning()")
    return True


def test_numeric_info_level():
    """Test that level=4 (INFO) maps to logger.info"""
    print("\n" + "=" * 80)
    print("TEST: Numeric INFO Level (4)")
    print("=" * 80)

    model = Model(MagicMock())

    with patch("pyrocrail.model.logger") as mock_logger:
        exception_xml = ET.fromstring(
            '<exception text="System initialized successfully" level="4"/>'
        )
        model._handle_exception(exception_xml)

        assert mock_logger.info.called, "INFO level should call logger.info()"
        call_args = mock_logger.info.call_args[0][0]
        assert "Rocrail info:" in call_args
        assert "initialized" in call_args

    print("  [+] Level 4 correctly mapped to logger.info()")
    return True


def test_string_level_backward_compatibility():
    """Test that string levels still work (backward compatibility)"""
    print("\n" + "=" * 80)
    print("TEST: String Level Backward Compatibility")
    print("=" * 80)

    model = Model(MagicMock())

    # Test string 'exception' level
    with patch("pyrocrail.model.logger") as mock_logger:
        exception_xml = ET.fromstring('<exception text="Error" level="exception"/>')
        model._handle_exception(exception_xml)
        assert mock_logger.error.called, "String 'exception' should work"

    # Test string 'warning' level
    with patch("pyrocrail.model.logger") as mock_logger:
        exception_xml = ET.fromstring('<exception text="Warning" level="warning"/>')
        model._handle_exception(exception_xml)
        assert mock_logger.warning.called, "String 'warning' should work"

    # Test string 'info' level
    with patch("pyrocrail.model.logger") as mock_logger:
        exception_xml = ET.fromstring('<exception text="Info" level="info"/>')
        model._handle_exception(exception_xml)
        assert mock_logger.info.called, "String 'info' should work"

    print("  [+] String levels work for backward compatibility")
    return True


def main():
    """Run all exception level tests"""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "EXCEPTION LEVEL MAPPING TESTS")
    print("=" * 80)
    print()

    results = []
    results.append(test_numeric_debug_level())
    results.append(test_numeric_exception_level())
    results.append(test_numeric_warning_level())
    results.append(test_numeric_info_level())
    results.append(test_string_level_backward_compatibility())

    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    print("\nAll exception level mapping tests passed!")
    print("\nVerified:")
    print("  [+] Level 16384 (0x4000) -> logger.debug() [DEBUG]")
    print("  [+] Level 1 (0x0001) -> logger.error() [EXCEPTION]")
    print("  [+] Level 2 (0x0002) -> logger.warning() [WARNING]")
    print("  [+] Level 4 (0x0004) -> logger.info() [INFO]")
    print("  [+] String levels still work (backward compatibility)")

    print()
    return all(results)


if __name__ == "__main__":
    import sys

    sys.exit(0 if main() else 1)
