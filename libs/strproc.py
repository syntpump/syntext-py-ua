import re


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
        RETOKENS: This function using RETOKENS which may be string at first and
            converts it to compiled regex, so no compiling may be needed in
            future.

    """

    global RETOKENS
    if type(RETOKENS) is str:
        RETOKENS = re.compile(RETOKENS)

    return RETOKENS.findall(sentence)


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
