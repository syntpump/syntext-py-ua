import re


# Compiled regexps will be collected here. They can be accessed by their body
# as the key.
RECOMPILED = dict()


# These string constants can be used for build regexes.

REDASHSET = r'[\u2012-\u2015\u002D]'
REDASH = r'\u2012\u2013\u2014\u2015\u002D'
REELLIPSIS = r'[\u2026\u22EF\u1801]|(?:\.)(?!\.)|(?:\.\.)(?!\.)|(?:\.\.\.)'
# ~@?!&^* symbols
REMARKS = r'[\u007E\u0040\u003F\u0021\u0026\u005E\u002A]'
RECOMMA = r'[\u002C]'
REBRACKETS = r'[[\]()\{}]'
RELEFTTXTBRACKET = r'[\u0028]'
RERIGHTTXTBRACKET = r'[\u0029]'
RECOLON = r'[:]'
RESEMICOLON = r'[;]'
# Quotation marks
REQUOT = r'[\u2018\u2019\u201C\u201D\u0022\u00AB\u00BB]'
RESLASH = r'[\u002F\u005C\u007C\u00A6]'

REPUNCT = (
    fr'{REDASHSET}|{REELLIPSIS}|{REMARKS}|{RECOLON}|{RESEMICOLON}|'
    fr'{RESLASH}|{REBRACKETS}|{REQUOT}'
)

RESPACE = r'[\u2003\u2002\u0020]'
# List of symbols that often occurs near the decimals (e.g "±5%"")
RENUM = r'[\u2213\u00B1\u002B\u002B\u0025\u2031\u00B0\u0023\u2116\u00A7]'
REMATH = r'[\u002B\u005C\u002D\u00D7\u00F7\u2213\u00B1]'
# Symbols that can separate two numbers: "5..8", "5/8", "5-8"
RENUMSEP = (
    rf'{REELLIPSIS}|{REDASHSET}|{RECOLON}|{RESEMICOLON}|'
    rf'{RESLASH}|{REMATH}'
)

RECURRENCY = r'[\u20A0-\u20CF\u00A2-\u00A5\u0024]'
REAPOSTROPHE = f'\'"’'

# List of all Ukrainian symbols + dashes + apostrophes
RECYRRUA = rf'[А-ЩЬЮ-щьюяіїґєІЇҐЄ{REDASH}{REAPOSTROPHE}]'

# Regex for western smiles
REWSMILE = (
    r"[',|>dD0|{}3<>O]*"  # Hat
    r"[*:=xX8;#%\-‑Bb]*"  # Eyes
    r"['\"]*"  # Tears
    r"[\-‑~^]*"  # Nose
    r"[)(3&#\\\/Oo@<>\]\[}{cCdD\-|PÞ$0*×,SJ]*"  # Mouth
    r"[\.l:]*"  # Chin
)

# Regex for basic eastern smiles. Regex for all eastern smiles might be too
# complicated to use it.
REESMILEBASIC = (
    r"[<?\\\/]?"  # Left hand
    r"[({]*"  # Left cheek
    r"[#;dD*]?"  # Ear
    r"[<>^-~-・+°=?'\"\.]"  # Eye
    r"[_\-.oO0·;+=]?"  # Mouth/nose
    r"[<>^-~-・+°=?'\"\.]"  # Eye
    r"[#;bB*]?"  # Ear
    r"[)}]*"  # Right cheek
    r"[>?\\\/]?"  # RIght hand
)

# Formal notation of smile like :smile: or :moon:
REFORMALSMILE = r":\w+:"

# Regex for tokens in sentence
RETOKENS = (
    fr'(?:[\w{REDASH}]+)'
    fr'|[^\w\s]'
    fr'|{RECURRENCY}\d+'
)

# Simplified regex for URLs: protocol, ww?, domain, ...
REURL = r"^(.+://)?(ww.\.)?(\w+\.).*$"

# Simplified regex for emails
REEMAIL = r"^.*@.*$"

# Set of special characters
RESPECIAL = r"[!@#$%^&*(),.?\"':{}|<>]"


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


def hasNonUkrainian(token) -> bool:
    """Check if the given string has the characters out of Ukrainian alphabet.

    Args:
        token (str): String to checked.

    Returns:
        bool

    Globals:
        RECYRRUASET: Set of Ukrainian characters.

    """

    global RECYRRUA

    return not reCoversEntire(token, regex=getCompiled(RECYRRUA + "+"))


def isPunct(token) -> bool:
    """Check if the given string is punctuation.

    Args:
        token (str): String to be checked.

    Returns:
        bool

    Globals:
        REPUNCT: Set of punctuation

    """

    global REPUNCT

    return reCoversEntire(token, regex=getCompiled(f"({REPUNCT})+"))


def isDash(token) -> bool:
    """Check if the given string is dash.

    Args:
        token (str): String to be checked.

    Returns:
        bool

    Globals:
        REPUNCT: Set of dashes

    """

    global REDASHSET

    return reCoversEntire(token, regex=getCompiled(f"({REDASHSET})+"))


def isComma(token) -> bool:
    """Check if the given string is comma.

    Args:
        token (str): String to be checked.

    Returns:
        bool

    Globals:
        REPUNCT: Comma symbol

    """

    global REMARKS

    return reCoversEntire(token, regex=getCompiled(f"({REMARKS})+"))


def isColon(token) -> bool:
    """Check if the given string is punctuation.

    Args:
        token (str): String to be checked.

    Returns:
        bool

    Globals:
        REPUNCT: Set of punctuation

    """

    global RECOLON

    return reCoversEntire(token, regex=getCompiled(f"({RECOLON})+"))


def isSemicolon(token) -> bool:
    """Check if the given string is punctuation.

    Args:
        token (str): String to be checked.

    Returns:
        bool

    Globals:
        REPUNCT: Set of punctuation

    """

    global RESEMICOLON

    return reCoversEntire(token, regex=getCompiled(f"({RESEMICOLON})+"))


def isLeftBracket(token) -> bool:
    """Check if the given string is punctuation.

    Args:
        token (str): String to be checked.

    Returns:
        bool

    Globals:
        REPUNCT: Set of punctuation

    """

    global RELEFTTXTBRACKET

    return reCoversEntire(token, regex=getCompiled(f"({RELEFTTXTBRACKET})+"))


def isRightBracket(token) -> bool:
    """Check if the given string is punctuation.

    Args:
        token (str): String to be checked.

    Returns:
        bool

    Globals:
        REPUNCT: Set of punctuation

    """

    global RERIGHTTXTBRACKET

    return reCoversEntire(token, regex=getCompiled(f"({RERIGHTTXTBRACKET})+"))


def isSym(token) -> bool:
    """Check if token is SYM.

    Args:
        token (str)

    Returns:
        bool

    Globals:
        RESPECIAL: Set of special characters

    """

    global RESPECIAL

    return reCoversEntire(token, regex=getCompiled(RESPECIAL + "+"))


def isSmile(token) -> bool:
    """Check if token is smile or at least smile notation.
    (It's about :smiles_between_doublecolons:).

    Args:
        token (str)

    Returns:
        bool

    Globals
        REFORMALSMILE, REWSMILE, REESMILEBASIC: Sets of smiles
    """

    global REFORMALSMILE
    global REFORMALSMILE
    global REESMILEBASIC

    return (
        reCoversEntire(token, regex=getCompiled(REFORMALSMILE)) or
        reCoversEntire(token, regex=getCompiled(REWSMILE)) or
        reCoversEntire(token, regex=getCompiled(REESMILEBASIC))
    )


def contextOf(sentence, r, n):
    """Returns r-radius context of n-th token of the sentence.

    Args:
        sentence (list of dicts): List of tokens.
        r (int): Radius of context.
        n (int): Position of the center of the context.

    Returns:
        dict: Context within radius. Left side will be mirrored. Example:
            let sentence [a, b, c, d, e, f, g]
            for r=2 and n=0 dict becomes {
                "center": a,
                "context": [
                    {b, __position=1},
                    {c, __position=2}
                ]
            }
            for r=3 and n=2 dict becomes {
                "center": c,
                "context": [
                    {b, __position=-1},
                    {a, __position=-2},
                    {d, __position=1},
                    {e, __position=2},
                    {f, __position=3}
                ]
            }
            "__position" property enumerates context in that manner:
            center is: C
            numerals: A      B      |C|      D      E      F
            sentence: -2     -1      0       1      2      3

    """

    lRange = n - r if (n - r) >= 0 else 0

    return {
        "context": [
            # This is left context.
            # Token dict will be updated with `i` property, which is the
            # position of the token in the sentence.
            # Left context is reversed and negative-enumerated, so that tokens
            # will be enumerated in this way:
            #
            #          |------------ n     (n=3, r=3)
            # sentence: A   B   C   |D|    (here D is the center)
            # numerals: -3  -2  -1  0
            {**token, **{"__position": -i - 1}}
            for i, token
            in enumerate(list(reversed(sentence[lRange:n])))
        ] + [
            # The right context will be positive-enumerated.
            {**token, **{"__position": i + 1}}
            for i, token
            in enumerate(sentence[n + 1:n + r + 1])
        ],
        "center": sentence[n],
    }


def context(sentence, r):
    """Returns generator of contexts of all tokens in the sentence.

    Args:
        sentence (list): List of tokens (consists of objects).
        r (int): Radius of context.

    Yields:
        contextOf(sentence, r, n is iterable)
        i (int): Number of token in sentence.

    """

    for i in range(len(sentence)):
        yield {
            **contextOf(sentence, r, n=i),
            **{"i": i}
        }


def unspace(text):
    """Replace double (and n-size) spaces with single-space. Replace tabs and
    other spaces with space symbol.

    Args:
        text (str)

    Returns:
        str

    """

    for space in [
        "\u00a0", "\u1680", "\u180e", "\u2000", "\u2001", "\u2002", "\u2003",
        "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200a",
        "\u200b", "\u202f", "\u205f", "\u3000", "\ufeff"
    ]:
        text.replace(space, "\u0020")

    text = re.sub(r"\s+", "\u0020", text)

    if text == "\u0020":
        return ""
    else:
        return text

