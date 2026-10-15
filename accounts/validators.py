import re

MC_PATTERN = re.compile(r"^mc\d+$", re.IGNORECASE)
CPM_PATTERN = re.compile(r"^cpm\d+$", re.IGNORECASE)


def normalize_mc_number(value: str) -> str:
    cleaned = value.strip().lower()
    if not MC_PATTERN.match(cleaned):
        raise ValueError(
            "MC number must look like mc112202 (mc followed by digits)."
        )
    return cleaned


def normalize_cpm_number(value: str) -> str:
    cleaned = value.strip().lower()
    if not CPM_PATTERN.match(cleaned):
        raise ValueError(
            "CPM number must look like cpm25666 (cpm followed by digits)."
        )
    return cleaned
