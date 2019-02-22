from libs.params import Params
from importlib import import_module
from libs.logs import Logger
from libs.ctxmorphtrain import ContextualProcessorTrainer
import json
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
--collection ... *requiered  Name of collections where the rules for morphology
                             recognition are stored in.
--logfile ...    ccrlog.md   File to write full logs in.
--path ...       *requiered  Path to Universal Dependencies file.
--reader ...     *requiered  Name of script and class of reader you want to
                             choose. That will be found in libs/ud directory.
                             Example:
                             conllu.ConlluReader
                             All before last dot must be a path to module.
--tagparser      None        Name of script and class which can parse XPOS
                             tags. That can be found in libs/ud directory.
                             Example:
                             mte.MTEParser
--swallexcs      None        If your tagparser raises errors in some tags,
                             sentences with these tags might be skipped. List
                             here error classes which will be imported from the
                             tagparser package separating them by a comma.
                             Example:
                             IncorrectTag,SomeOtherError
--cmpkeys        "xpos"      List of properties separated by comma, which
                             should be compared when constructing contextual
                             rules. This field is case-sensitive.
                             Example:
                             Tense,Animate,Voice,Person
-unstrict ...    False       Do not check GC format strictly.
--applier ...    -->         Path to applier function for MorphologyRecognizer.
                             Example:
                             path.module.class.function
                             module.class.property.function
                             ...
                             Default is
                             libs.morphology.MorphologyRecognizer.selectFirst
--priority ...   None        Path to .json file with priority list.
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


db = DB(
    host=argv.get("--dbhost", default="atlas"), dbname="syntextua"
)

requiered = ["path", "reader", "collection"]
for require in requiered:
    if not argv.has("--" + require):
        argv.request(require, text=f"Provide a {require} name")

applierAddr = argv.get(
    "--applier",
    default="libs.morphology.MorphologyRecognizer.selectFirst"
).split(".")
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
    fp=open(argv.get("--path"), encoding="utf-8"),
    strict=False if argv.has("-unstrict") else True
)

tagparserAddr = argv.get("--tagparser").split(".")
tagparser = import_module("libs.ud." + tagparserAddr[0])
swallowexcs = []
for err in argv.get("--swallexcs").split(","):
    swallowexcs.append(
        getattr(tagparser, err)
    )
# At `except` block only tuples of errors are allowed
swallowexcs = tuple(swallowexcs)
tagparser = getattr(tagparser, tagparserAddr[1])()

priorityList = None
if argv.has("--priority"):
    priorityList = json.load(open(argv.get("--priority", default=None)))

limit = int(argv.get("--limit", default="0"))
offset = int(argv.get("--offset", default="0"))

ctxt = ContextualProcessorTrainer(
    db,
    cmpkeys=argv.get("--cmpkeys", default="0").split(","),
    reader=reader,
    rulescoll=db.cli.get_collection(argv.get("--collection")),
    logger=logger,
    tagparser=tagparser,
    applier=applier,
    priority=priorityList
)

ctxt.train(
    swallowexcs=swallowexcs,
    limit=int(argv.get("--limit", default=0)),
    offset=int(argv.get("--offset", default=0))
)
