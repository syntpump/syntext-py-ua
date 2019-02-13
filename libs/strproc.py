import re


# Compiled regexps will be collected here. They can be accessed by their body
# as the key.
RECOMPILED = dict()


# These string constants can be used for build regexes.

REDASHSET = r'[\u2012-\u2015\u002D]'
REDASH = r'\u2012\u2013\u2014\u2015\u002D'
REELLIPSIS = r'[\u2026\u22EF\u1801]|(?:\.)(?!\.)|(?:\.\.)(?!\.)|(?:\.\.\.)'
# ~@?!&^*, symbols
REMARKS = r'[\u007E\u0040\u003F\u0021\u0026\u005E\u002A\u002C]'
REBRACKETS = r'[[\]()\{}]'
RECOLONS = r'[:;]'
# Quotation marks
REQUOT = r'[\u2018\u2019\u201C\u201D\u0022]'
RESLASH = r'[\u002F\u005C\u007C\u00A6]'
REPUNCT = (
    fr'{REDASHSET}|{REELLIPSIS}|{REMARKS}|{REQUOT}|{RECOLONS}|{RESLASH}|'
    fr'{REBRACKETS}'
)
RESPACE = r'[\u2003\u2002\u0020]'
# List of symbols that often occurs near the decimals (e.g "±5%"")
RENUM = r'[\u2213\u00B1\u002B\u002B\u0025\u2031\u00B0\u0023\u2116\u00A7]'
REMATH = r'[\u002B\u005C\u002D\u00D7\u00F7\u2213\u00B1]'
# Symbols that can separate two numbers: "5..8", "5/8", "5-8"
RENUMSEP = rf'{REELLIPSIS}|{REDASHSET}|{RECOLONS}|{RESLASH}|{REMATH}'
RECURRENCY = r'[\u20A0-\u20CF\u00A2-\u00A5\u0024]'
# List of all ukrainian symbols
RECYRRUA = r'[А-ЩЬЮ-щьюяіїґєІЇҐЄ]'
RETOKENS = (
    fr'(?:\d+{RENUMSEP}\d+)'
    fr'|(?:{RENUM}*{RECURRENCY}*\d+{RECURRENCY}*{RENUM}*)|'
    fr'{REPUNCT}|[\w{REDASH}\u0301]+'
)


def tokenize(sentence):
    """Tokenize the given sentence.

    Args:
        sentence (str): String that must be processed.

    Returns:
        list: List of tokens.

    Globals:
        RETOKENS: Regex for token in sentence.

    """

    global RETOKENS

    return getCompiled(RETOKENS).findall(sentence)


def groupEndings(words):
    """Group words by similar engings, i.e. just sort list by strings by its
    last characters. Example:

    List:       Sorted list:        Look at the endings.
    bite        mike
    chiefly     nike
    fastly      bite
    mike        namely
    namely      chiefly
    nike        fastly

    Args:
        words (list): List of words.

    Returns:
        list: List of grouped words.

    """

    def rotate(li: list):
        """Returns list with inverted strings.
        """
        return [s[::-1] for s in li]

    return rotate(
        sorted(
            rotate(words)
        )
    )


def getCompiled(reg):
    """Returns compiled regex from RECOMPILED if it exists. Compile it and
    return otherwise.

    Args:
        reg (str): Regex to be compiled.

    Returns:
        _sre.SRE_Pattern, compiled pattern

    Global:
        RECOMPILED: Dictionary with compiled expressions.

    """

    global RECOMPILED

    if reg not in RECOMPILED:
        RECOMPILED[reg] = re.compile(reg)

    return RECOMPILED[reg]


def reCoversEntire(string, regex) -> bool:
    """Return True if the given regex covers entire string.

    Args:
        string (str): String to be checked.
        regex (_sre.SRE_Match, compiled regex)

    Returns:
        bool

    """

    search = regex.search(string)

    if not search:
        return False
    else:
        span = search.span()
        if span[0] == 0 and span[1] == len(string):
            return True
        else:
            return False


def hasNonUkrainian(string) -> bool:
    """Check if the given string has the characters out of Ukrainian alphabet.

    Args:
        string (str): String to checked.

    Returns:
        bool

    Globals:
        RECYRRUASET: Set of Ukrainian characters.

    """

    global RECYRRUA

    return not reCoversEntire(string, regex=getCompiled(RECYRRUA + "+"))


def isPunct(string) -> bool:
    """Check if the given string is punctuation.

    Args:
        string (str): String to be checked.

    Returns:
        bool

    Globals:
        CREPUNCT: Compiled set of REPUNCT.
            (Variable will be created.)
        RECYRRUA: String to be compiled.

    """

    global REPUNCT

    return not reCoversEntire(string, regex=getCompiled(f"({REPUNCT})+"))
