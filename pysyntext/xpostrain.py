from libs.params import Params
from libs.logs import Logger
from predefinator import Predefinator
import sys


argv = Params()

if argv.has("?"):
    print(
"""
Use this script to train POS recognition. This will create a new temporary
collection in database with training data you'll be able to merge with the main
collection later.

Expected parameters:
Name            Default     Description
--dbhost ...    atlas       DB which will be use in order to upload training
                            data.
--tempdb ...    localhost   DB which will be used as temporary memory.
--logfile ...   -->         File to write full logs in. Default:
                            xpostrainlog.md
--reader ...    *requiered  Name of class of reader. Example: ConlluReader.
--trainer...    *requiered  Name of class of trainer. Example: HumanTrainer.
--entry ...     *requiered  Name of iteration function for your class. (See
                            docs for this name). It's a function that perform
                            one step in learning process.
--limit ...     0           Limit of tokens to be processed. Can be used for
                            testing script. Pass '0' to set it to infinite.
--offset ...    0           Skip first N tokens from GC.
--confs         config.json Address to file with configurations.
...Plus additional parameters needed for the trainer you chose.
""" # noqa E122
    )
    raise SystemExit

predef = Predefinator(
    fp=open(
        argv.get("--confs", default="config.json"), encoding="utf-8"
    )
)

logger = Logger(
    fp=open(argv.get("--logfile", default="xpostrainlog.md"), mode="a+"),
    stream=sys.stdout
)

logger.output("Loading...")


from libs.db import DB # noqa E402

db = DB(
    host=argv.get("--dbhost", default="atlas"),
    dbname="syntextua"
)

trainer = predef.inited(
    argv.get("--trainer"),
    db=db,
    settings=argv.getdict(),
    logger=logger
)

logger.output("loaded.")


try:
    # Process all lines until EOF
    cursor = trainer.loadData(
        db=DB(
            host=argv.get("--tempdb", default="localhost"),
            dbname="syntextua_tempdb"
        ),
        # This will import class with specified name from gc module and init it
        # with given parameters.
        gcreader=predef.inited(argv.get("--reader")),
        limit=int(argv.get("--limit", default=0)),
        offset=int(argv.get("--offset", default=0))
    )
    while True:
        counter = next(cursor)["counter"]
        logger.output(f"{counter} lines processed so far.", rewritable=True)
except (StopIteration, EOFError):
    pass
finally:
    length = len(trainer.poses)
    logger.write(f"Collected {length} XPOSes.\n")
    logger.output(f"\nCollected {length} XPOSes.\n")

# This will get iteration function and execute it
stream = getattr(trainer, argv.get("--entry"))()

try:
    while True:
        msg = next(stream)
        logger.output(msg)
except (StopIteration, KeyboardInterrupt):
    trainer.db.drop(trainer.tempcoll.name)
    logger.output("End of the training.")
