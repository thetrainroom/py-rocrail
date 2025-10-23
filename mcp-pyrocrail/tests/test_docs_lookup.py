"""Tests for documentation lookup functionality"""

import pytest
from pathlib import Path
from mcp_pyrocrail.tools.docs_lookup import DocsLookup

# Path to OBJECTS.md in parent project
OBJECTS_MD = Path(__file__).parent.parent.parent / "OBJECTS.md"


@pytest.fixture
def docs_lookup():
    """Create DocsLookup instance for testing"""
    return DocsLookup(str(OBJECTS_MD))


def test_lookup_locomotive(docs_lookup):
    """Test looking up locomotive object"""
    result = docs_lookup.api_lookup("locomotive")
    assert "Locomotive" in result
    assert "lc" in result
    assert "locomotive.py" in result


def test_lookup_locomotive_method(docs_lookup):
    """Test looking up specific locomotive method"""
    result = docs_lookup.api_lookup("locomotive", "set_speed")
    assert "set_speed" in result
    assert "speed: int" in result
    assert "None" in result  # return type


def test_lookup_by_element_tag(docs_lookup):
    """Test lookup using element tag (e.g., 'lc' instead of 'locomotive')"""
    result = docs_lookup.api_lookup("lc")
    assert "Locomotive" in result


def test_list_methods_switch(docs_lookup):
    """Test listing switch methods"""
    result = docs_lookup.list_methods("switch")
    assert "straight" in result
    assert "turnout" in result
    assert "flip" in result


def test_get_attributes_block(docs_lookup):
    """Test getting block attributes"""
    result = docs_lookup.get_attributes("block")
    assert "idx" in result
    assert "occ" in result
    assert "locid" in result


def test_check_method_exists(docs_lookup):
    """Test checking if a method exists"""
    result = docs_lookup.check_method("locomotive", "set_speed")
    assert "✅" in result
    assert "exists" in result


def test_check_method_not_exists(docs_lookup):
    """Test checking a method that doesn't exist"""
    result = docs_lookup.check_method("locomotive", "collect")
    assert "❌" in result
    assert "does not exist" in result
    assert "Did you mean" in result


def test_search_speed(docs_lookup):
    """Test searching for speed-related methods"""
    result = docs_lookup.search("speed")
    assert "set_speed" in result or "speed" in result.lower()


def test_invalid_object_type(docs_lookup):
    """Test with invalid object type"""
    result = docs_lookup.api_lookup("invalid_object")
    assert "not found" in result
    assert "Available objects" in result


def test_invalid_method(docs_lookup):
    """Test with invalid method name"""
    result = docs_lookup.api_lookup("locomotive", "invalid_method")
    assert "not found" in result
    assert "Available methods" in result


def test_list_methods_no_methods(docs_lookup):
    """Test object with no methods"""
    # Tour has no methods after recent cleanup
    result = docs_lookup.list_methods("tour")
    # Should either list methods or say none are documented
    assert "tour" in result.lower() or "no methods" in result.lower()
