from libs.params import Params
from libs.morphology import MorphologyRecognizer
from libs.accuracy import XPOSRecognitionAnalyzer
from importlib import import_module
from libs.ui import percentage
from libs.logs import Logger
import json


argv = Params()

if argv.has("?"):
    print(
"""
Use this script to analyze MorphologyRecognizer accuracy. Just provide a UD
file and the limit.

Expected parameters:
Name             Default     Description
--dbhost ...     atlas       DB which will be used for MorphologyRecognizer
--collection ... *requiered  Name of collections where the rules stored in.
--logfile ...    amalog.md   File to write full logs in.
--path ...       *requiered  Path to Universal Dependencies file.
--reader ...     *requiered  Name of script and class of reader you want to
                             choose. That will be found in libs/ud directory.
                             Example:
                             conllu.ConlluReader
                             All before last dot must be a path to module.
-unstrict ...   False       Do not check GC format strictly.
--applier ...    -->         Path to applier function for MorphologyRecognizer.
                             Example:
                             path.module.class.function
                             module.class.property.function
                             ...
                             Default is
                             libs.morphology.MorphologyRecognizer.selectFirst
--priority ...   None        Priority list in JSON format is it documented in
                             MorhologyRecognizer module. Don't forget to
                             escape quotes!
--limit ...      0           Limit of tokens to be processed. Set to '0' to set
                             it to infinite.
--offset ...     0           Skip first N tokens from UD file you've specified.
""" # noqa E122
        )
    raise SystemExit

print("Loading...\r")


from libs.db import DB # noqa E402


logger = Logger(
    filepath=argv.get("--logfile", default="amalog.md")
)

requiered = ["path", "reader", "collection"]
for require in requiered:
    if not argv.has("--" + require):
        argv.request(require, text=f"Provide a {require} name")

applierAddr = argv.get("--applier").split(".")
# First part of address is a module
applier = import_module(
    applierAddr.pop(0)
)
# Every next part is a property of the previous one
while len(applierAddr) > 0:
    applier = getattr(
        applier, applierAddr.pop(0)
    )

reader = argv.get("--reader").split(".")
reader = getattr(import_module("libs.ud." + reader[0]), reader[1])(
    filepath=argv.get("--path"),
    ignoreComments=True,
    strict=False if argv.has("-unstrict") else True
)

priorityList = None
if argv.has("--priority"):
    priorityList = json.loads(argv.get("--priority", default=None))

limit = int(argv.get("--limit", default="0"))
offset = int(argv.get("--offset", default="0"))

analyzer = XPOSRecognitionAnalyzer(
    reader=reader,
    limit=float("inf") if limit == 0 else limit,
    offset=offset,
    recognizer=MorphologyRecognizer(
        collection=(
            DB(
                host=argv.get("--dbhost", default="atlas")
            )
        ).cli.get_collection(
            argv.get("--collection")
        )
    ),
    applierFunction=applier,
    priorityList=priorityList
)

logger.write(f"Connected to {analyzer.recognizer.collection.name}\n")

generator = analyzer.init()

print(
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
        print(
            f"{analyzer.CHECKED}\t"
            f"{percentage(analyzer.CORRECT_XPOS, analyzer.CHECKED)}% "
            f"({percentage(analyzer.IMPROVE_XPOS, analyzer.CHECKED)}%)\t"
            f"{percentage(analyzer.CORRECT_UPOS, analyzer.CHECKED)}% "
            f"({percentage(analyzer.IMPROVE_UPOS, analyzer.CHECKED)}%)",
            end="\r"
        )
except StopIteration:
    pass
except KeyboardInterrupt:
    raise SystemExit
finally:
    logger.write("\n")

print("\nDone.")
