"""TrainByAffixes train class, child of MorphologyRecognizeTrainer
"""

from ..morphtrain import MorphologyRecognizeTrainer

from libs.arrproc import unduplicate, keyExtract, reorder
from libs.strproc import groupEndings
from difflib import SequenceMatcher


class TrainByAffixes(MorphologyRecognizeTrainer):
    """This trainer will recognize similar affixes in words and adds it as
    rules. It'll also create 'static' rules for POSes that have no declension
    property and 'exception' rules for words that are too different from
    others, so no connections can be found.

    Iteration function for this trainer is nextXPOS method.

    """

    def nextXPOS(self):
        """Generator function. Each next iteration process one of POS from
        self.poses set, returns rules and delete POS tuple from set.

        Expected settings:
            maxcommon (int): If the word cause too many intersections, then
                maybe we're comparing two words with the same roots. Here's the
                number of maximum allowed intersection length. Tokens with
                larger matching length will be reordered with the next token.
                Default: 4.
            mincommon (int): Sometimes two words with different morphology have
                very small common parts. E.g., 'building' and 'cup' intersects
                only at 'u'. Set this parameter to prevent it.
                Default: 2.
            minrule (int): Allowed minimum of length of rule to be added to
                rules set.
                Default: 2.

        Yields:
            Messages with info about what's going on at current iteration and
            results of processing. Can be string and dict both.

        """

        maxCommon = (
            int(self.settings["maxcommon"])
            if "maxcommon" in self.settings else 4
        )
        minCommon = (
            int(self.settings["mincommon"])
            if "mincommon" in self.settings else 2
        )
        minRule = (
            int(self.settings["minrule"])
            if "minrule" in self.settings else 2
        )

        print(f"Now {len(self.poses)} POSes will be processed.")

        for upos, xpos in self.poses:

            self.log(f"Analyzing {upos}: {xpos}...\n")

            if upos in self.ignoreposes:
                self.log("Skip IGNOREPOS.\n")
                yield f"{upos} is in ingorepos, so skip it"
                continue

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
            self.log(f"Found {len(tokens)} for that:\n")
            self.logjson(tokens)

            if upos in self.staticposes:
                if not self.testenabled:
                    self.maincoll.insert_one({
                        "upos": upos,
                        "xpos": xpos,
                        "type": "static",
                        "data": tokens
                    })
                self.log("STATICPOS; Added as exception.\n")
                yield f"{len(tokens)} tokens of {xpos} was added as static"
                continue

            if len(tokens) < 2:
                self.log("Not enough data to train.\n")
                yield (
                    f"There's only {len(tokens)} of {xpos} "
                    "tokens to train. Skip."
                )
                continue

            tokens = groupEndings(tokens)

            exceptions = []
            rules = set()

            exceptionsLength = len(tokens)
            # Loop through 'exceptions' while they're still appearing
            while True:

                yield f"Processing {upos} {xpos} now"

                if len(tokens) == 0:
                    break

                commons = self.lookForIntersections(
                    tokens, maxCommon, minCommon
                )

                # If the word cause too many intersections, then maybe we're
                # comparing two words with the same roots. Just skip it.
                if len(commons["result"]) > maxCommon:
                    reorder(tokens, 0, 1)
                    yield (
                        f"Reordering occured at {xpos}; there's {len(tokens)} "
                        "of them"
                    )
                    continue

                # If there's no intersections, then first token to exceptions.
                if len(commons["result"]) == 0:
                    yield (
                        f"First of {xpos} was added as exception"
                    )
                    exceptions.append(
                        tokens.pop(0)
                    )
                    continue

                # Do not add too short rules.
                if len(commons["result"]) < minRule:
                    yield (
                        f"Rule was only {len(commons['result'])} length, "
                        "that's short to add"
                    )
                    # Add first token to exceptions
                    commons["exceptions"].append(
                        tokens.pop(0)
                    )
                    continue
                else:
                    rules.add(commons["result"])

                if len(commons["exceptions"]) < 2:
                    break

                tokens = commons["exceptions"]

                # The further processing has no sense because number of
                # exceptions are not decreasing
                if len(tokens) >= exceptionsLength:
                    break

                # Remember the number of generated exceptions in order to
                # compare it at the next iteration.
                exceptionsLength = len(tokens)

            if len(exceptions) != 0:
                if not self.testenabled:
                    self.maincoll.insert_one({
                        "xpos": xpos,
                        "upos": upos,
                        "type": "exceptions",
                        "data": exceptions
                    })
                yield (
                    f"Exception for {len(exceptions)} of {xpos} contains "
                    f"{len(exceptions)} records"
                )
                self.log(f"Added {len(exceptions)} exceptions:\n")
                self.logjson(exceptions)
            else:
                self.log("No exceptions was noticed.\n")

            if len(rules) != 0:
                if not self.testenabled:
                    self.maincoll.insert_one({
                        "xpos": xpos,
                        "upos": upos,
                        "type": "rules",
                        "data": list(rules)
                    })
                self.log(f"Added {len(rules)} rules:\n")
                self.logjson(list(rules))
                yield (
                    f"Rule for {len(tokens)} of {xpos} contains "
                    f"{len(rules)} commons "
                )
            else:
                self.log("No rules was made.\n")

            self.log("\n\n")

    def lookForIntersections(self, tokens, maxCommon, minCommon):
        """ Intersect all the tokens in list and return its common part. Look
        for exceptions too.

        Args:
            tokens (list): List of tokens.
            minCommon, maxCommon (int): Unnecessary options described in
                nextXPOS method.

        Returns:
            dict: Dict with result and exceptions.

        Example of tokens:
            ["intersection", "invention", "invent"]

        Example of result:
            {
                "result": "tion",
                "exceptions": ["invent"]
            }

        """

        base = tokens[0]
        exceptions = []

        for token in tokens[1:]:
            matcher = SequenceMatcher(a=base, b=token)
            match = matcher.find_longest_match(
                0, len(base), 0, len(token)
            )
            if match.size != 0 and match.size >= minCommon:
                base = base[match.a:match.a + match.size]
            else:
                exceptions.append(token)

        return {
            "result": base if len(base) <= maxCommon else "",
            "exceptions": exceptions
        }
