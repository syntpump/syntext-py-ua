"""HumanTrainer train class, child of MoprhologyRecognizeTrainer
"""

from ..morphtrain import MorphologyRecognizeTrainer

from libs.morphology import MorphologyRecognizer
from importlib import import_module
from libs.arrproc import unduplicate, keyExtract
from libs.ui import expect
from pprint import pprint
import json

class HumanTrainer(MorphologyRecognizeTrainer):
    """This trainer can analyze errors in recognition and allow use to create
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
            applierFunction (str): Name of applier function for morphology
                recognizer.
            priorityList (str): Priority list for recognizer. (optional)

        """


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

        recognizer = MorphologyRecognizer(
            collection=self.db.cli.get_collection(
                self.settings["rulescollection"]
            )
        )

        priorityList = json.loads(self.settings["priorityList"])

        # Iterate each POS
        for upos, xpos in self.poses:

            # Repeat this continuously unless user decide to break it
            while True:
                try:

                    # If some mistake in recognition will happen, this flag
                    # will be set to True, so user will be suggested to repeat
                    # processing this POS
                    mistakeExists = False

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

                    print(f"Training {upos} {xpos}.")
                    print("Tokens found: %s.\n" % ', '.join(tokens))

                    # Iterate each token of this POS
                    for token in tokens:

                            print(f"Current token is: {token}")

                            recogn = recognizer.recognize(
                                token, applier
                            )

                            result = recognizer.recognize(token)
                            appRes = recognizer.recognize(
                                token, applier, priorityList
                            )

                            print(
                                f"Recognized as {appRes['upos']} "
                                f"{appRes['xpos']}."
                            )

                            if xpos == appRes["xpos"]:
                                ruleType = (
                                    recogn['type']
                                    if recogn['type'] else "<unknown>"
                                )
                                print(
                                    "Recognized correctly. "
                                    f"Type of rule: {ruleType}\n"
                                )
                                continue
                            else:
                                mistakeExists = True

                            if xpos in keyExtract(result, "xpos"):
                                print(
                                    "Recognizing of this token may be "
                                    "improved. Here's the DB output:"
                                )
                            else:
                                print(
                                    "Recognized incorrectly. Here's the "
                                    "DB output:"
                                )
                            pprint(result, indent=4, compact=True)

                            decision = expect(
                                msg=(
                                    "Skip this token or make a new rule? "
                                    "(s - Skip|r - Rule): "
                                ),
                                what = ["r", "s"]
                            )

                            if decision == "s":
                                continue
                            elif decision == "r":
                                self.newRule()

                    if not mistakeExists:
                        raise ContinueException

                    if (
                        expect(
                            msg="Repeat processing this POS? (y|n): ",
                            what=["y", "n"]
                        ) == "y"
                    ):
                        print("\n\n")
                        raise RepeatException
                    break

                except RepeatException:
                    continue

                except ContinueException:
                    break

            yield "\n\n"

    def newRule(self):
        """Show the UI to create new rule for DB and adds in to DB.
        """

        print("*pretends to be rule UI*")

class RepeatException(Exception):
    pass

class ContinueException(Exception):
    pass
