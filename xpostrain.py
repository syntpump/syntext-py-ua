from libs.params import Params
from libs.logs import Logger
from importlib import import_module


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
--reader ...    *requiered  Name of script and class of reader you want to
                            choose. That will be found in libs/ud directory.
                            Example:
                            conllu.ConlluReader
-unstrict ...   False       Do not check GC format strictly.
--trainer...    *requiered  Name of script and class of trainer you want to
                            choose. That will be found in libs/tmr directory.
                            Examples:
                            trainbyaffixes.TrainByAffixes
                            All before last dot must be a path to module.
--entry ...     *requiered  Name of iteration function for your class. (See
                            docs for this name). It's a function that perform
                            one step in learning process.
--limit ...     0           Limit of tokens to be processed. Can be used for
                            testing script. Pass '0' to set it to infinite.
--offset ...    0           Skip first N tokens from GC.
-test           False       Do not upload any data to dbhost.
...Plus additional parameters needed for the trainer you chose.
""" # noqa E122
    )
    raise SystemExit

if not argv.has("--path"):
    argv.request("path", text="Provide a path to UD file")


print("Loading...")


from libs.db import DB # noqa E402


trainer = argv.get("--trainer").split(".")

# Get class from module and init it
trainer = getattr(import_module("libs.tmr." + trainer[0]), trainer[1])(
    db=DB(
        host=argv.get("--dbhost", default="atlas"),
        dbname="syntextua"
    ),
    logger=Logger(
        filepath=argv.get("--logfile", default="xpostrainlog.md")
    ),
    # POSes which don't declense. Remember them as exceptions.
    staticposes=[
        "ADP", "AUX", "CCONJ", "DET", "NUM", "PART", "PRON", "SCONJ", "INTJ"
    ],
    # POSes which can be recognized automatically, skip them.
    ignoreposes=["SYM", "X", "PUNCT"],
    testenabled=True if argv.has("-test") else False,
    settings=argv.getdict()
)

reader = argv.get("--reader").split(".")

print("loaded.")


try:
    # Process all lines until EOF
    cursor = trainer.loadData(
        db=DB(
            host=argv.get("--tempdb", default="localhost"),
            dbname="syntextua_tempdb"
        ),
        # This will import class with specified name from gc module and init it
        # with given parameters.
        gcreader=getattr(import_module("libs.ud." + reader[0]), reader[1])(
            filepath=argv.get("--path"),
            ignoreComments=True,
            strict=False if argv.has("-unstrict") else True
        ),
        limit=int(argv.get("--limit", default=0)),
        offset=int(argv.get("--offset", default=0))
    )
    while True:
        counter = next(cursor)["counter"]
        print(f"{counter} lines processed so far.", end="\r")
except (StopIteration, EOFError):
    pass
finally:
    length = len(trainer.poses)
    trainer.log(f"Collected {length} XPOSes.\n")
    print(f"\nCollected {length} XPOSes.\n")

# This will get iteration function and execute it
stream = getattr(trainer, argv.get("--entry"))()

try:
    while True:
        msg = next(stream)
        print(msg)
except (StopIteration, KeyboardInterrupt):
    trainer.db.drop(trainer.tempcoll.name)
    print("End of the training.")
