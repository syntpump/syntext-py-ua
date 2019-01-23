# TODO: write logs into file


from libs.params import Params
from libs.morphology import MorphologyRecognizer
from libs.accuracy import XPOSRecognitionAnalyzer
from importlib import import_module
from libs.ui import percentage


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
--reader ...     *requiered  Name of UD Reader class to use. This class will
                             be imported from gc.py library.
--applier ...    -->         Path to applier function for MorphologyRecognizer.
                             Example:
                             path.module.class.function
                             module.class.property.function
                             ...
--limit ...      0           Limit of tokens to be processed. Set to '0' to set
                             it to infinite.
-strictUD        False       Use strict UD format.
""" # noqa E122
        )
    raise SystemExit

print("Loading...\r")


from libs.db import DB # noqa E402


requiered = ["path", "reader", "collection"]
for require in requiered:
    if not argv.has("--" + require):
        argv.request(require, text=f"Provide a {require} name")

applierAddr = argv.get("--applier").split(".")
# First part of adress is a module
applier = import_module(
    applierAddr.pop(0)
)
# Every next part is a property of the previous one
while len(applierAddr) > 0:
    applier = getattr(
        applier, applierAddr.pop(0)
    )

reader = getattr(import_module("libs.gc"), argv.get("--reader"))

limit = int(argv.get("--limit", default="0"))

analyzer = XPOSRecognitionAnalyzer(
    reader=reader(
        filepath=argv.get("--path"),
        ignoreComments=True,
        strict=argv.get("-strictUD", default=False)
    ),
    limit=float("inf") if limit == 0 else limit,
    recognizer=MorphologyRecognizer(
        collection=(
            DB(
                host=argv.get("--dbhost", default="atlas")
            )
        ).cli.get_collection(
            argv.get("--collection")
        )
    ),
    applierFunction=applier
)

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
        next(generator)
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

print("\nDone.")
