import re

DEFAULT_SITE_NAMES = [
    "CeeNaija.com",
    "waploaded.com",
    "waploaded",
    "jointearn.com",
    "jointearn",
    "waptrick.com",
    "waptrick",
    "naijaloaded.com",
    "naijaloaded",
    "tooxclusive.com",
    "tooxclusive",
    "justnaija.com",
    "justnaija",
]

_STRIP_CHARS = " -_()[]"


def build_site_patterns(site_names: list[str]) -> list[str]:
    """Build regex patterns for known download site watermarks."""
    patterns: list[str] = []
    for site in site_names:
        site = site.strip()
        if not site:
            continue
        escaped = re.escape(site)
        patterns.extend(
            [
                rf"\|\|\s*{escaped}",
                rf"\|\s*{escaped}",
                rf"\({escaped}\)",
                rf"\[{escaped}\]",
                rf"\{{\s*{escaped}\s*\}}",
                rf"-\s*{escaped}",
                rf"{escaped}",
            ]
        )
    return patterns


DEFAULT_WATERMARK_PATTERNS = build_site_patterns(DEFAULT_SITE_NAMES)


def clean_title(
    title: str,
    patterns: list[str] | None = None,
    site_names: list[str] | None = None,
) -> str:
    """Remove known site watermarks and trim decorative characters."""
    if not title:
        return title

    if patterns is not None:
        active_patterns = patterns
    elif site_names is not None:
        active_patterns = build_site_patterns(site_names)
    else:
        active_patterns = DEFAULT_WATERMARK_PATTERNS

    if not active_patterns:
        return title.strip(_STRIP_CHARS)

    combined = "|".join(f"(?:{pattern})" for pattern in active_patterns)
    cleaned = re.sub(combined, "", title, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*\|\s*$", "", cleaned)
    cleaned = re.sub(r"^\s*\|\s*", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip(_STRIP_CHARS)