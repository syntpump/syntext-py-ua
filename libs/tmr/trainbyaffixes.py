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
    """

    def nextXPOS(self, maxCommon=4, minCommon=2, minRule=2):
        """Generator function. Each next iteration process one of POS from
        self.poses set, returns rules and delete POS tuple from set.

        Args:
            maxCommon (int): If the word cause too many intersections, then
                maybe we're comparing two words with the same roots. Here's the
                number of maximum allowed intersection length. Tokens with
                larger matching length will be reordered with the next token.
            minCommon (int): Sometimes two words with different morphology have
                very small common parts. E.g., 'building' and 'cup' intersects
                only at 'u'. Set this parameter to prevent it.
            minRule (int): Allowed minimum of length of rule to be added to
                rules set.

        Yields:
            Messages with info about what's going on at current iteration and
            results of processing. Can be string and dict both.

        """

        print(f"Now {len(self.poses)} will be processed.")

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
                yield f"{len(tokens)} tokens of {xpos} was added as exceptions"
                continue

            if len(tokens) < 2:
                self.log.write("Not enough data to train.\n")
                yield (
                    f"There's only {len(tokens)} of {xpos} "
                    "tokens to train. Skip."
                )

            tokens = groupEndings(tokens)

            exceptions = []
            rules = set()

            exceptionsLength = len(tokens)
            # Loop through 'exceptions' while they're still appearing
            while True:

                if len(tokens) == 0:
                    break

                commons = self.lookForIntersections(tokens)

                # If the word cause too many intersections, then maybe we're
                # comparing two words with the same roots. Just skip it.
                if len(commons["result"]) > maxCommon:
                    reorder(tokens, 0, 1)
                    yield (
                        f"Reordering occured at {xpos}; there's {len(tokens)} "
                        "of them"
                    )
                    continue

                # If there's no intersections, then put it to exceptions.
                if len(commons["result"]) == 0:
                    yield (
                        f"{len(tokens)} tokens of {xpos} was added as "
                        "exceptions"
                    )
                    exceptions.append(
                        tokens.pop(0)
                    )
                    continue

                yield (
                    f"Rule for {len(tokens)} of {xpos} contains "
                    f"{len(commons['result'])} commons and "
                    f"{len(commons['exceptions'])} exceptions now"
                )

                # Do not add too short rules.
                if len(commons["result"]) > minRule:
                    rules.add(commons["result"])
                    yield "Rule was too short to add"

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
            else:
                self.log("No rules was made.\n")

            self.log("\n\n")

    def lookForIntersections(self, tokens, minCommon, maxCommon):
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
