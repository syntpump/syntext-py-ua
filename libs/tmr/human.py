"""HumanTrainer train class, child of MoprhologyRecognizeTrainer
"""

from ..morphtrain import MorphologyRecognizeTrainer

from ..morphology import MorphologyRecognizer
from importlib import import_module
from libs.arrproc import unduplicate, keyExtract


class HumanTrainer(MorphologyRecognizeTrainer):

    def nextXPOS(self):
        """Generator function. Each next iteration process one POS from
        self.poses, ask for XPOSRecognitionAnalyzer which of those can be
        recognize correctly and suggest human to improve the rules.

        Expected settings:
            rulescollection (str): Name of collection with rules in main DB,
                which contains rules to test.
            applierFunction (str): Name of applier function for morphology
                recognizer.

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

        # Iterate each POS
        for upos, xpos in self.poses:

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
            print("Tokens found: %s" % ', '.join(tokens), end="")

            # Iterate each token of this POS
            for token in tokens:
                    recoResponse = recognizer.recognize(
                        token, applier
                    )

                    print(f"For \"{token}\" response:")
                    print(recoResponse)

            yield "\n\n"
