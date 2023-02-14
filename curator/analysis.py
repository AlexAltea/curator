import re

YEAR_MIN = 1800
YEAR_MAX = 2030

def detect_year(name):
    """
    Extract the movie year given the file name.
    Assumptions:
    - Year is a 4-digit number, optionally surrounded by non-word characters.
    - Year is interpreted as a Gregorian calendar integer in range [YEAR_MIN, YEAR_MAX].
    - Year is the rightmost string satisfying these two conditions.
    - Year is never found at the beginning of the file name.
    """
    matches = re.finditer(r'(?:\b|_)(\d{4})(?:\b|_)', name)
    for match in reversed(list(matches)):
        if match.start() == 0:
            return None
        year = int(match.group(1))
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
        name = name.replace('_', ' ')
    # Extract matching left-starting pattern as name
    match = re.match(r'[\w\s\-\']+', name)
    if match:
        return match[0].strip()
    return None

def detect_tags(name):
    """
    Extract the file tags in the file name.
    Assumptions:
    - Tags are surrounded by square brackets.
    - Tags do not contain any kind of brackets within.
    - Multiple tags can exist.
    """
    matches = re.findall(r'\[([\w\-\,\.]+)\]', name)
    return matches
