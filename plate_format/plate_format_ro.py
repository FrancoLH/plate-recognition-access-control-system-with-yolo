import re

RO_PREFIXES = {
    "AB", "AR", "AG", "BC", "BH", "BN", "BR", "BT", "BV", "BZ",
    "CS", "CL", "CJ", "CT", "CV", "DB", "DJ", "GL", "GR", "GJ",
    "HR", "HD", "IL", "IS", "IF", "MM", "MH", "MS", "NT", "OT",
    "PH", "SM", "SJ", "SB", "SV", "TR", "TM", "TL", "VS", "VL", "VN",
    "B"
}

# Format 1: B 123 ABC
pattern_bucharest = re.compile(r"^B\s\d{3}\s[A-Z]{3}$")

pattern_arg = re.compile(r"^[A-Z]{2}\d{3}[A-Z]{2}$")

# Format 2: CJ 12 XYZ
pattern_regional = re.compile(rf"^({'|'.join(RO_PREFIXES - {'B'})})\s\d{{2}}\s[A-Z]{{3}}$")

def normalize_plate_format(plate: str) -> str:
    """
    Corrects poorly spaced plates and returns them to a standard size
    Exemples :
        'B865MHQ' => 'B 865 MHQ'
        'CJ12XYZ' => 'CJ 12 XYZ'
        'CT40LMD' => 'CT 40 LMD'
    """
    plate = plate.strip().upper().replace("-", "").replace(" ", "")

    if len(plate) == 7:
        # Format pour Bucarest (B123ABC)
        if plate[0] == 'B' and plate[1:4].isdigit() and plate[4:].isalpha():
            return f"{plate[0]} {plate[1:4]} {plate[4:]}"
        # Format pour les autres régions (CJ12XYZ)
        elif plate[:2] in RO_PREFIXES and plate[2:4].isdigit() and plate[4:].isalpha():
            return f"{plate[:2]} {plate[2:4]} {plate[4:]}"
    return plate


def is_valid_plate(plate: str) -> bool:
    """
    Checks if a plate exactly matches the RO format.
    Applies minimal normalization before testing.
    """
    plate = plate.strip().upper()
    plate = re.sub(r'\s+', ' ', plate)
    plate = normalize_plate_format(plate)

    return bool(pattern_bucharest.match(plate) or pattern_regional.match(plate) or pattern_arg.match(plate))
