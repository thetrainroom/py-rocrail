from typing import Any


def set_attr(obj: Any, attr: str, value: str) -> None:
    """Set attribute on object with type conversion from XML string.

    Args:
        obj: Object to set attribute on
        attr: Attribute name
        value: String value from XML
    """
    # Convert empty strings to None
    if value == "":
        setattr(obj, attr, None)
        return

    try:
        val: Any = int(value)
    except ValueError:
        val = value
    if value in ("false", "False"):
        val = False
    if value in ("true", "True"):
        val = True
    setattr(obj, attr, val)
