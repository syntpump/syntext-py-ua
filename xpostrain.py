# TODO: write logs into file


from libs.params import Params
from libs.arrproc import unduplicate, keyExtract, reorder
from libs.strproc import groupEndings
from libs.logs import Logger
from libs.gc import ConlluReader
from difflib import SequenceMatcher


argv = Params()

if argv.has("?"):
    print(
"""
Use this script to train xpos recognition. This will create a new temporary
collection in database with training data you'll be able to merge with the main
collection later.

Expected parameters:
Name            Default     Description
--dbhost ...    atlas       DB which will be use in order to upload training
                            data.
--tempdb ...    localhost   DB which will be used as temporary memory.
--logfile ...   -->         File to write full logs in. Default:
                            xpostrainlog.md
--path ...      *requiered  Path to Universal Dependencies file.
--limit ...     0           Limit of tokens to be processed. Can be used for
                            testing script. Pass '0' to set it to infinite.
--max_common ...4           Maximum allowed intersection length.
--min_common ...2           Minimum allowed intersection length.
--min_rule ...  2           Minimum allowed length of rule to be added to DB.
-test           False       Do not upload any data to dbhost.
""" # noqa E122
    )
    raise SystemExit

if not argv.has("--path"):
    argv.request("path", text="Provide a path to UD file")

print("Loading...")


from libs.db import DB # noqa E402


logger = Logger(
    filepath=argv.get("--logfile", default="xpostrainlog.md")
)

udfile = ConlluReader(
    filepath=str(argv.get("--path")),
    ignoreComments=True,
    strict=False
)

tempdb = DB(
    host=argv.get("--tempdb", default="localhost"),
    dbname="syntextua_tempdb"
)

tempcoll = tempdb.createCollection(tempdb.TEMPORARY)

logger.write(f"Created {tempcoll.name} as temporary collection.\n")

testEnabled = argv.has("-test")

# POSes which don't declense. Remember them as exceptions.
STATICPOS = ["ADP", "AUX", "CCONJ", "DET", "NUM", "PART", "PRON", "SCONJ",
             "INTJ", "PUNCT"]

# POSes which can be recognized automatically, skip them.
IGNOREPOS = ["SYM", "X"]

# If the word cause too many intersections, then maybe we're comparing two
# words with the same roots. Here's the number of maximum allowed intersection
# length. Tokens with larger matched will be reordered with the next token.
MAXIMUM_INTERSECTION = argv.get("--max_common", default=4)

# Sometimes two words with different morphology have very small common parts.
# E.g., 'building' and 'cup' intersects only at 'u'. Set this parameter to
# prevent it.
MINIMUM_INTERSECTION = argv.get("--min_common", default=2)

# Allowed minimum of length of rule to be added to rules set.
MINIMUM_RULE_LENGTH = argv.get("--min_rule", default=2)

# Collecting UPOS and XPOS while iterating.
poses = set()

# Process all lines until EOF
try:
    counter = 0
    limit = int(argv.get("--limit", default=0))
    while counter < limit if limit != 0 else True:
        # There's no cheap way to get number of lines in file, so just print
        # info about 'processed so far'
        line = udfile.nextLine()
        counter += 1
        print(f"{counter}\tlines processed so far.", end="\r")
        # Look ConlluReader documentation for line types
        if line["type"] != udfile.DATALINE:
            continue
        upos = line["data"]["upos"]
        xpos = line["data"]["xpos"]
        poses.add((upos, xpos))
        # XPOS defines morphology of file completely
        tempcoll.insert({
            "upos": upos,
            "xpos": xpos,
            "form": line["data"]["form"].lower()
        })
except EOFError:
    pass
finally:
    logger.write(f"Collected {len(poses)} XPOSes.\n")
    print(
        f"\nReached end of the file, collected {len(poses)} XPOSes. "
        "Iterating over them...\n"
        "XPOS           Found   Common length   Exceptions"
    )

maindb = DB(
    host=argv.get("--dbhost", default="atlas"),
    dbname="syntextua"
)

maincoll = maindb.createCollection(maindb.XPOSTRAIN)
logger.write(f"Created {maincoll.name} collection in main db.\n")


def lookForIntersections(tokens: list):
    """ Intersect all the tokens in list and return its common part. Look for
    exceptions too.

    Args:
        tokens (list): List of tokens.

    Returns:
        dict: Dict with result and exceptions.

    Example of tokens:
        ["intersection", "intvention", "invent"]

    Example of result:
        {
            "result": "tion",
            "exceptions": ["invent"]
        }

    """
    base = tokens[0]
    exceptions = []

    for token in tokens[1:]:
        matcher = SequenceMatcher(a=base, b=token)
        match = matcher.find_longest_match(
            0, len(base), 0, len(token)
        )
        if match.size != 0 and match.size >= MINIMUM_INTERSECTION:
            base = base[match.a:match.a + match.size]
        else:
            exceptions.append(token)

    return {
        "result": base if len(base) <= MAXIMUM_INTERSECTION else "",
        "exceptions": exceptions
    }


for upos, xpos in poses:

    logger.write(f"Analyzing {upos}: {xpos}...\n")

    if upos in IGNOREPOS:
        logger.write("Skip IGNOREPOS.\n")
        continue

    tokens = unduplicate(
        keyExtract(
            list(
                tempcoll.find({
                    "xpos": xpos
                })
            ),
            "form"
        )
    )
    logger.write(f"Found {len(tokens)} for that:\n")
    logger.logjson(tokens)

    if upos in STATICPOS:
        if not testEnabled:
            maincoll.insert_one({
                "upos": upos,
                "xpos": xpos,
                "type": "static",
                "data": tokens
            })
        print(
            "{0:<15}{1:<8}Added as exceptions.".format(xpos, len(tokens))
        )
        logger.write("STATICPOS; Added as exception.\n")
        continue

    if len(tokens) < 2:
        print(
            "{0:<15}{1:<8}Lack of data to train.".format(xpos, len(tokens))
        )
        logger.write("Not enough data to train.\n")

    tokens = groupEndings(tokens)

    exceptions = []
    rules = set()

    exceptionsLength = len(tokens)
    # Loop through 'exceptions' while they're still appearing
    while True:

        if len(tokens) == 0:
            break

        commons = lookForIntersections(tokens)

        # If the word cause too many intersections, then maybe we're comparing
        # two words with the same roots. Just skip it.
        if len(commons["result"]) > MAXIMUM_INTERSECTION:
            reorder(tokens, 0, 1)
            print(
                "{0:<15}{1:<8}Reordering occured.".format(
                    xpos, len(tokens)
                )
            )
            continue

        # If there's no intersections, then put it to exceptions.
        if len(commons["result"]) == 0:
            print(
                "{0:<15}{1:<8}New exception occured.".format(
                    xpos, len(tokens)
                )
            )
            exceptions.append(
                tokens.pop(0)
            )
            continue

        print(
            "{0:<15}{1:<8}".format(
                xpos, len(tokens),
                len(commons["result"]), len(commons["exceptions"])
            )
        )

        # Do not add too short rules.
        if len(commons["result"]) > MINIMUM_RULE_LENGTH:
            rules.add(commons["result"])

        if len(commons["exceptions"]) < 2:
            break

        tokens = commons["exceptions"]

        # The further processing has no sense because number of exceptions are
        # not decreasing
        if len(tokens) >= exceptionsLength:
            break

        # Remember the number of generated exceptions in order to compare it at
        # the next iteration.
        exceptionsLength = len(tokens)

    if len(exceptions) != 0:
        if not testEnabled:
            maincoll.insert_one({
                "xpos": xpos,
                "upos": upos,
                "type": "exceptions",
                "data": exceptions
            })
        logger.write(f"Added {len(exceptions)} exceptions:\n")
        logger.logjson(exceptions)
    else:
        logger.write("No exceptions was noticed.\n")

    if len(rules) != 0:
        if not testEnabled:
            maincoll.insert_one({
                "xpos": xpos,
                "upos": upos,
                "type": "rules",
                "data": list(rules)
            })
        logger.write(f"Added {len(rules)} rules:\n")
        logger.logjson(list(rules))
    else:
        logger.write("No rules was made.\n")

    logger.write("\n\n")


tempcoll.drop()
tempdb.close()
maindb.close()
