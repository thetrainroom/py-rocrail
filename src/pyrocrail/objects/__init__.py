def set_attr(obj, attr, value):
    # Convert empty strings to None
    if value == "":
        setattr(obj, attr, None)
        return

    try:
        val = int(value)
    except ValueError:
        val = value
    if value in ("false", "False"):
        val = False
    if value in ("true", "True"):
        val = True
    setattr(obj, attr, val)
