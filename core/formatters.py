def format_artist(name: str) -> str:
    """
    Format artist name: first word lowercase, rest unchanged, spaces become hyphens.

    Example: "Nathaniel Bassey" -> "nathaniel-Bassey"
    """
    name = name.strip()
    if not name:
        return ""

    parts = name.split()
    if len(parts) == 1:
        return parts[0].lower()

    first = parts[0].lower()
    rest = "-".join(parts[1:])
    return f"{first}-{rest}"