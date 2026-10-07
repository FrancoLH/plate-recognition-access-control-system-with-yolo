import re

PATTERNS = (
    re.compile(r"^[A-Z]{2} \d{3} [A-Z]{2}$"),  
    re.compile(r"^[A-Z]{3} \d{3}$"),  
    re.compile(r"^[A-Z] \d{3} [A-Z]{3}$"),  
    re.compile(r"^\d{3} [A-Z]{3}$"),  #
)


def normalize_plate_format(plate: str) -> str:
    compact = re.sub(r"[\s-]+", "", plate.strip().upper())

    if re.fullmatch(r"[A-Z]{2}\d{3}[A-Z]{2}", compact):
        return f"{compact[:2]} {compact[2:5]} {compact[5:]}"
    if re.fullmatch(r"[A-Z]\d{3}[A-Z]{3}", compact):
        return f"{compact[0]} {compact[1:4]} {compact[4:]}"
    if re.fullmatch(r"[A-Z]{3}\d{3}", compact):
        return f"{compact[:3]} {compact[3:]}"
    if re.fullmatch(r"\d{3}[A-Z]{3}", compact):
        return f"{compact[:3]} {compact[3:]}"
    return compact


def is_valid_plate(plate: str) -> bool:
    normalized = normalize_plate_format(plate)
    return any(pattern.fullmatch(normalized) for pattern in PATTERNS)