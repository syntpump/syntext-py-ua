from libs.params import Params
from libs.logs import Logger
from predefinator import Predefinator
import sys


argv = Params()

if argv.has("?"):
    print(
"""
Use this script to train contextual correction of morphology recognition. This
will create a new temporary collection in database with training data you'll be
able to merge with the main collection later.

Expected parameters:
Name             Default     Description
--dbhost ...     atlas       DB which will be used.
--logfile ...    ccrlog.md   File to write full logs in.
--limit ...      0           Limit of sentences to be processed. Set to '0' to
                             set it to infinite.
--offset ...     0           Skip first N sentences from UD file you've
                             specified.
""" # noqa E122
        )
    raise SystemExit

logger = Logger(
    fp=open(
        argv.get("--logfile", default="ccrlog.md"), mode="a+", encoding="utf-8"
    ),
    stream=sys.stdout
)

logger.output("Loading...")


from libs.db import DB # noqa E402


predef = Predefinator(
    fp=open(
        argv.get("--confs", default="config.json"), encoding="utf-8"
    )
)

reader = predef.inited("ConlluReader")

db = DB(
    host=argv.get("--dbhost", default="atlas"), dbname="syntextua"
)

ctxt = predef.inited(
    "ContextualProcessorTrainer",
    db=db,
    logger=logger,
    recognizer=predef.inited(
        "MorphologyRecognizer",
        collection=lambda name: db.cli.get_collection(name)
    )
)

ctxt.train(
    limit=int(argv.get("--limit", default=0)),
    offset=int(argv.get("--offset", default=0))
)
