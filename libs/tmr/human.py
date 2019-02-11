"""HumanTrainer train class, child of MoprhologyRecognizeTrainer
"""

from ..morphtrain import MorphologyRecognizeTrainer

from libs.morphology import MorphologyRecognizer
from importlib import import_module
from libs.arrproc import unduplicate, keyExtract
from libs.ui import expect
from pprint import pprint
import json
from bson import ObjectId


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
            priorityList (str): Link to .json file with priority list
                (optional).

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

        recognizer = MorphologyRecognizer(
            collection=self.rulescollection
        )

        priorityList = json.load(self.settings["priorityList"])

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
                        print("\n\n")
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

        print("-" * 80)
        print("Rules manager.")

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

        print("-" * 80)

    def searchRules(self):
        """Show UI for searching rules.
        """

        print("Type a filter: ", end="")

        try:
            cursor = self.rulescollection.find(
                json.loads(
                    str(input())
                )
            )
        except Exception:
            print("There's error in your JSON.")
            return None

        print("<Start fetching response>")

        for document in cursor:
            pprint(document, indent=4, compact=True)
            print("---")

        print("<End fetching response>")

    def deleteRule(self):
        """Show UI for deleting rules.
        """

        print("Type ID to delete: ", end="")
        try:
            self.rulescollection.find_one_and_delete({
                "_id": ObjectId(str(input()))
            })
        except Exception:
            print("Exception happened:")
            print(Exception)
        print("Done.")

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
                print(
                    "Type data for your rule, separating with space: ",
                    end=""
                )
                data = str(input()).split(" ")
                print(
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

        print("Rule inserted:")
        pprint(inserted, indent=4, compact=True)



class RepeatException(Exception):
    pass


class ContinueException(Exception):
    pass
