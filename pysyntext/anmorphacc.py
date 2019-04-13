from libs.params import Params
from libs.ui import percentage
from libs.logs import Logger
from predefinator import Predefinator
import sys


argv = Params()

if argv.has("?"):
    print(
"""
Use this script to analyze MorphologyRecognizer accuracy. Just provide a UD
file and the limit.

Expected parameters:
Name             Default     Description
--dbhost ...     atlas       DB which will be used for MorphologyRecognizer
--logfile ...    amalog.md   File to write full logs in.
                             All before last dot must be a path to module.
--confs          config.json Path to .json file with configurations.
--limit ...      0           Limit of tokens to be processed. Set to '0' to set
                             it to infinite.
--offset ...     0           Skip first N tokens from UD file you've specified.
--confs         config.json Address to file with configurations.
""" # noqa E122
        )
    raise SystemExit

predef = Predefinator(
    fp=open(
        argv.get("--confs", default="config.json"), encoding="utf-8"
    )
)

logger = Logger(
    fp=open(
        argv.get("--logfile", default="amalog.md"), mode="a+", encoding="utf-8"
    ),
    stream=sys.stdout
)


logger.output("Loading...")


from libs.db import DB # noqa E402


db = DB(
    host=argv.get("--dbhost", default="atlas")
)

analyzer = predef.inited(
    "XPOSRecognitionAnalyzer",
    limit=int(argv.get("--limit", default=9e999)),
    recognizer=predef.inited(
        "MorphologyRecognizer",
        collection=lambda name: db.cli.get_collection(name)
    )
)

logger.write(f"Connected to {analyzer.recognizer.collection.name}\n")

generator = analyzer.init()

logger.output(
    "Loaded succesfully.\n"
    "Here you'll see the analyzing progress. Numbers in the brackets counts "
    "cases where applier function were unable to apply correct rule, even "
    "though DB returned one.\n"
    "Checked\tXPOS\t\tUPOS"
)

try:
    while True:
        logger.logjson(
            next(generator)
        )
        logger.output(
            (
                f"{analyzer.CHECKED}\t"
                f"{percentage(analyzer.CORRECT_XPOS, analyzer.CHECKED)}% "
                f"({percentage(analyzer.IMPROVE_XPOS, analyzer.CHECKED)}%)\t"
                f"{percentage(analyzer.CORRECT_UPOS, analyzer.CHECKED)}% "
                f"({percentage(analyzer.IMPROVE_UPOS, analyzer.CHECKED)}%)"
            ),
            rewritable=True
        )
except StopIteration:
    pass
except KeyboardInterrupt:
    raise SystemExit
finally:
    logger.write("\n")

logger.output("\nDone.")
