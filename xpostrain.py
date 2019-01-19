from libs.params import Params
from libs.arrproc import unduplicate, keyExtract
from libs.strproc import groupEndings


argv = Params()

if argv.has("?"):
    print(
"""
Use this script to train xpos recognition. This will create a new temporary
collection in database with training data you'll be able to merge with the main
collaction later.

Expected paramaters:
Name            Default     Description
--dbhost ...    atlas       DB which will be use in order to upload training
                            data.
--tempdb ...    localhost   DB which will be used as temporary memory.
--logfile ...   -->         File to write full logs in. Default:
                            xpostrainlog.md
--path ...      *requiered  Path to Universal Dependencies file.
--limit ...     0           Limit of tokens to be processed. Can be used for
                            testing script. Pass '0' to set it to infinite.
-test           False       Do not upload any data to dbhost.
""" # noqa E122
    )
    raise SystemExit

if not argv.has("--path"):
    argv.request("path", text="Provide a path to UD file")


from libs.db import DB # noqa E402
from libs.logs import Logger # noqa E402
from libs.gc import ConlluReader # noqa E402

udfile = ConlluReader(
    filepath=str(argv.get("--path")),
    ignoreComments=True,
    strict=False
)

tempdb = DB(
    host=argv.get("--dbhost", default="localhost"),
    dbname="syntextua_tempdb"
)

tempcoll = tempdb.createCollection(tempdb.TEMPORARY)

logsEnabled = argv.has("--logfile")
testEnabled = argv.has("-test")

if logsEnabled:
    logger = Logger(
        filepath=argv.get("--logfile"),
        default="xpostrain.md"
    )

# POSes which don't declense. Remember them as exceptions.
STATICPOS = ["ADP", "AUX", "CCONJ", "DET", "NUM", "PART", "PRON", "SCONJ",
             "INTJ", "PUNCT"]

# POSes which can be recognized automatically, skip them.
IGNOREPOS = ["SYM", "X"]

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
    print(
        f"\nReached end of the file, collected {len(poses)} XPOSes."
        "Iterating over them...\n"
        "XPOS           Found   Common length   Exceptions"
    )

maindb = DB(
    host=argv.get("--dbhost", default="atlas"),
    dbname="syntextua"
)

maincoll = maindb.createCollection(maindb.XPOSTRAIN)

for upos, xpos in poses:

    if upos in IGNOREPOS:
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

    if upos in STATICPOS:
        if not testEnabled:
            maincoll.insert_one({
                "upos": upos,
                "xpos": xpos,
                "data": tokens
            })
        print(
            "{0:<15}{1:<8}Added as exceptions.".format(xpos, len(tokens))
        )
        continue

    if len(tokens) < 2:
        print(
            "{0:<15}{1:<8}Lack of data to train.".format(xpos, len(tokens))
        )

    tokens = groupEndings(tokens)

# tempcoll.drop()
tempdb.close()
maindb.close()
