import re

YEAR_MIN = 1800
YEAR_MAX = 2100

def detect_year(name):
    """
    Extract the movie year given the file name.
    Assumptions:
    - Year is a 4-digit number, optionally surrounded by non-word characters.
    - Year is interpreted as a Gregorian calendar integer in range [YEAR_MIN, YEAR_MAX].
    - Year is the rightmost string satisfying these two conditions.
    """
    matches = re.findall(r'(?:\b|_)(\d{4})(?:\b|_)', name)
    for match in reversed(matches):
        year = int(match)
        if YEAR_MIN <= year <= YEAR_MAX:
            return year
    return None

def detect_name(name, year=None):
    """
    Extract the movie name given the file name.
    Optionally provide the movie release year, as tokenization hint.
    Assumptions:
    - Name appears before the year.
    - Name does not contatain parenthesis or brackets.
    """
    # Trim anything after year
    if year is None:
        year = detect_year(name)
    if year:
        name = name[:name.rfind(str(year))]
    # Normalize scene releases
    if not ' ' in name:
        name = name.replace('.', ' ')
    # Extract matching left-starting pattern as name
    match = re.match(r'[\w\s\-\']+', name)
    if match:
        return match[0].strip()
    return None
