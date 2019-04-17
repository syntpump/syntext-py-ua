"""HumanTrainer train class, child of MoprhologyRecognizeTrainer
"""

from ..morphtrain import MorphologyRecognizeTrainer

from libs.morphology import MorphologyRecognizer
from importlib import import_module
from libs.arrproc import unduplicate, keyExtract
from libs.ui import expect
from pprint import pprint
from bson import ObjectId
import json


class HumanTrainer(MorphologyRecognizeTrainer):
    """This trainer can analyze errors in recognition and allow user to create
    new rules.

    Properties:
        rules (list): List of data of rules that was inputed by user before.
            This will be used for suggestions.

    """

    rules = list()

    def nextXPOS(self):
        """Generator function. Each next iteration process one POS from
        self.poses, ask for XPOSRecognitionAnalyzer which of those can be
        recognize correctly and suggest human to improve the rules.

        Expected settings:
            rulescollection (str): Name of collection with rules in main DB,
                which contains rules to test.
                Required.
            applierFunction (str): Name of applier function for morphology
                recognizer.
                Required.
            priorityList (str): Link to .json file with priority list
                Optional.
            tagparser (str): Name of the class of tag parser.

        """

        self.rulescollection = self.db.cli.get_collection(
            self.settings["rulescollection"]
        )

        applierAddr = self.settings["applierFunction"].split(".")
        # First part of address is a module
        applier = import_module(
            applierAddr.pop(0)
        )
        # Every next part is a property of the previous one
        while len(applierAddr) > 0:
            applier = getattr(
                applier, applierAddr.pop(0)
            )

        priorityList = json.load(
            open(self.settings["priorityList"])
        )

        recognizer = MorphologyRecognizer(
            collection=self.rulescollection,
            priorityList=priorityList,
            applierFunc=applier,
            tagparser=self.settings["tagparser"]
        )

        counter = 0

        # Iterate each POS
        for upos, xpos in self.poses:

            # Repeat this continuously unless user decide to break it
            while True:
                try:

                    # If some mistake in recognition will happen, this flag
                    # will be set to True, so user will be suggested to repeat
                    # processing this POS
                    mistakeExists = False

                    counter += 1

                    tokens = unduplicate(
                        keyExtract(
                            list(
                                self.tempcoll.find({
                                    "xpos": xpos
                                })
                            ),
                            "form"
                        )
                    )

                    self.logger.output(
                        f"Training {upos} {xpos}: {counter}/{len(self.poses)}"
                    )
                    self.logger.output(
                        "Tokens found: %s.\n" % ', '.join(tokens)
                    )

                    # Iterate each token of this POS
                    for token in tokens:

                            self.logger.output(f"Current token is: {token}")

                            result = recognizer.recognize(
                                token, withApplier=False)
                            appRes = recognizer.recognize(token)

                            if appRes:
                                self.logger.output(
                                    f"Recognized as {appRes['upos']} "
                                    f"{appRes['xpos']} "
                                    f"(correct is {xpos} {upos})."
                                )

                                if xpos == appRes["xpos"]:
                                    ruleType = (
                                        appRes['type']
                                        if 'type' in appRes else "<unknown>"
                                    )
                                    self.logger.output(
                                        "Recognized correctly. "
                                        f"Type of rule: {ruleType}\n"
                                    )
                                    continue
                                else:
                                    mistakeExists = True
                            else:
                                self.logger.output(
                                    "Token was not recognized at all."
                                )

                            if result and xpos in keyExtract(result, "xpos"):
                                self.logger.output(
                                    "Recognizing of this token may be "
                                    "improved. Here's the DB output:"
                                )
                            else:
                                self.logger.output(
                                    "Recognized incorrectly. Here's the "
                                    "DB output:"
                                )
                            pprint(result, indent=4, compact=True)

                            action = expect(
                                msg=(
                                    "Skip this token (s) or enter to rule "
                                    "manager (r)?: "
                                ),
                                what=["r", "s"]
                            )

                            if action == "s":
                                continue
                            elif action == "r":
                                self.rulesManager(xpos, upos)

                    if not mistakeExists:
                        raise ContinueException

                    if (
                        expect(
                            msg="Repeat processing this POS? (y|n): ",
                            what=["y", "n"]
                        ) == "y"
                    ):
                        self.logger.output("\n\n")
                        raise RepeatException
                    break

                except RepeatException:
                    continue

                except ContinueException:
                    break

            yield "\n\n"

    def rulesManager(self, xpos, upos):
        """Show UI to create new rule for DB and adds in to DB.
        """

        self.logger.output("-" * 80)
        self.logger.output("Rules manager.")

        while True:

            try:
                action = expect(
                    msg="Create, search, delete or exit?: ",
                    what=["create", "search", "delete", "exit"]
                )
                if action == "create":
                    self.newRule(xpos, upos)
                elif action == "search":
                    self.searchRules()
                elif action == "delete":
                    self.deleteRule()
                elif action == "exit":
                    raise ContinueException

            except ContinueException:
                break

        self.logger.output("-" * 80)

    def searchRules(self):
        """Show UI for searching rules.
        """

        self.logger.output("Type a filter: ", rewritable=False)

        try:
            cursor = self.rulescollection.find(
                json.loads(
                    str(input())
                )
            )
        except Exception:
            self.logger.output("There's error in your JSON.")
            return None

        self.logger.output("<Start fetching response>")

        for document in cursor:
            pprint(document, indent=4, compact=True)
            self.logger.output("---")

        self.logger.output("<End fetching response>")

    def deleteRule(self):
        """Show UI for deleting rules.
        """

        self.logger.output("Type ID to delete: ", rewritable=False)
        try:
            self.rulescollection.find_one_and_delete({
                "_id": ObjectId(str(input()))
            })
        except Exception:
            self.logger.output("Exception happened:")
            self.logger.output(Exception)
        self.logger.output("Done.")

    def newRule(self, xpos, upos):
        """Show UI for creating rules.

        Args:
            xpos (str): XPOS of inserting rule.
            upos (str): UPOS of inserting rule.

        """

        ruleType = expect(
            msg="Choose type of the rule: ",
            what=["static", "exceptions", "rules"]
        )

        data = list()

        # Repeat this until user break
        while True:
            try:
                self.logger.output(
                    "Type data for your rule, separating with space: ",
                    rewritable=False
                )
                data = str(input()).split(" ")
                self.logger.output(
                    "Your data is: %s" % json.dumps(data, ensure_ascii=False)
                )
                if (
                    expect(
                        msg="Do you want to reenter data? (n|y): ",
                        what=["n", "y"]
                    ) == "n"
                ):
                    raise ContinueException

            except ContinueException:
                break

        inserted = self.rulescollection.insert_one({
            "xpos": xpos,
            "upos": upos,
            "type": ruleType,
            "data": data
        })

        self.logger.output("Rule inserted:")
        pprint(inserted, indent=4, compact=True)


class RepeatException(Exception):
    pass


class ContinueException(Exception):
    pass
