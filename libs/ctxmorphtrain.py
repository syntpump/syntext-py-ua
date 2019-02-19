"""Module for training CCMR.
"""

from .ctxmorph import ContextualProcessor
from .strproc import context
from functools import reduce


class ContextualProcessorTrainer:
    """This trainer will look for mistakes in POS recognition and compare it
    with GC data. Then rules for correction will be generated.

    """

    def __init__(
        self, db, reader, rulescoll, logger, tagparser, cmpkeys,
        strictgc=False, applier=None, priority=None
    ):
        """Init the trainer for contextual processor.

        Args:
            db (libs.DB): Database to upload generated rules in libs/ud.
            reader (initialized class): One of the classes of the readers
                defined.
            rulescoll (Collection): Collection with morphology recognition
                rules.
            logger (libs.logs.Logger)
            tagparser (?): Class of XPOS tags parser.
            cmpkeys (list): List of keys to be compared in tokens between two
                contexts.
            applier, priority: Applier function and priority list for
                MorphologyRecognizer.

        Properties:
            db, reader, logger, cmpkeys, tagparser: Values you are passing to
                init function.
            collection (Collection): A collection in DB with EMENDPOS marker,
                which are being used to upload rules.
            ctxprocc (libs.ctxmorph.ContextualProcessor)

        """

        self.db = db
        self.logger = logger
        self.reader = reader,
        self.collection = db.createCollection(db.EMENDPOS)
        self.ctxprocc = ContextualProcessor(
            collection=rulescoll, applier=applier, priority=priority,
            tagparser=tagparser
        )
        self.reader = reader
        self.cmpkeys = cmpkeys
        self.tagparser = tagparser

    def log(self, msg):
        """Call self.logger.write if self.logger is defined.

        Args:
            msg(str, int): Message to print.

        Return:
            ?: Result of Logger executing.

        """

        if self.logger:
            return self.logger.write(msg)

    def logjson(self, obj):
        """Call self.logger.logjson if self.logger is defined.

        Args:
            obj(*): Any JSON-serializable object.

        Return:
            ?: Result of Logger executing.

        """

        if self.logger:
            return self.logger.logjson(obj)

    def common(self, t1, t2):
        """Generator function, yields bundle of properties that are equal
        in two given tokens.

        Args:
            t1, t2 (dicts): Two tokens to be compared.

        Yields:
            tuple:
                [0] str: Name of the next equal property.
                [1] *: Value of this key in both tokens.

        """

        for key in t1:
            if (
                # This key was allowed to be compared
                key in self.cmpkeys and
                # This key is both in t1 and t2
                key in t2 and
                t1[key] == t2[key]
            ):
                yield (key, t1[key])

    def differs(self, t1, t2):
        """Generator function, yields bundle of properties that are differs
        in two given tokens.

        Args:
            t1, t2 (dicts): Two tokens to be compared.

        Yields:
            tuple:
                [0] str: Name of the next equal property.
                [1] *: Value of this key in first token.
                [1] *: Value of this key in second token.

        """

        for key in t1:
            if (
                # This key was allowed to be compared
                key in self.cmpkeys and
                # This key is both in t1 and t2
                key in t2 and
                t1[key] != t2[key]
            ):
                yield (key, t1[key], t2[key])

    def conclude(self, ctxbase, ctxto):
        """Compare centers in base context `ctxbase` and gc context `ctxto` and
        generate rules to make base center recognized correctly.

        Here's how it works. Suppose, we have two contexts:
        base: A1        B1        |C1|        D1        E1      (here radius=2)
        gc:   A2        B2        |C2|        D2        E2
        Here C1 and C2 is center tokens, C1 != C2 and every token was
        recognized correctly (i.e. [A..Z]1 == [A..Z]2). So the next rule will
        be generated:
            if B1==B2 and A1==A2 and D1==D2 and E1==E2
            then make C1 properties like in C2

        Suppose now, we have these contexts:
        base: A1        B1*       |C1|        D1        E1*
        gc:   A2        B2        |C2|        D2        E2
        Here tokens with star (*) was recognized incorrectly (i.e. B1!=B2 and
        E1!=E2), so they cannot be used in context-based rules. That means that
        next rule can be generated:
            if A1==A2 and D1==D2
            then C1 -> C2

        Rules are being generated according to the following rules:
            1. Every rule's `if` must contain at least two conditions.
            2. Every condition must be made in correct-recognized context.
            3. If base center and gc centers are equal, obviously no rule can
               be made.

        Args:
            ctxbase, ctxto (dicts): Contexts dict as defined in strproc.context
                function.

        Returns:
            list: List of `if` block in Ctx19 rule.

        """

        # If base and gc centers are equal
        if ctxbase["center"]["xpos"] == ctxto["center"]["xpos"]:
            return None

        ifblock = list()

        for tokenbase, tokento in zip(ctxbase["context"], ctxto["context"]):
            # If sentences was tokenized correctly (that was checked in
            # processSentence method), then tokenbase[__position] is equal
            # to tokento[__position] always.
            selectorRule = {
                "__position": abs(tokenbase["__position"]),
                "__name": (
                    "previous"
                    if tokenbase["__position"] < 0
                    else "next"
                )
            }
            for key, value in self.common(tokenbase, tokento):
                # [bool, str] list are created according to Ctx19 assignment
                # syntax in object rule representation style.
                selectorRule[key] = [True, value]

            if len(selectorRule) > 2:
                ifblock.append(selectorRule)

        return ifblock

    def adjust(self, base, gc):
        """Generate `then` block for Ctx19 rule for two tokens to make them
        equal.

        Args:
            t1, t2 (dicts): Dicts of tokens.

        Returns:
            dict: Dict of `then` block.

        """

        then = dict()

        for key, vbase, vgc in self.differs(base, gc):
            then[key] = vgc

        return then

    def processSentence(self, sentence, text, r, parseTags=False):
        """Recognize POSes of the sentence by MorphologyRecognizer and
        compare it with the given one.

        Args:
            sentence (list of dict): List of sentence with tokens.
            text (str): The same sentence but in simple string.
            r (int): Radius for comparing context.
            parsetags (bool): Check to True if tags from sentences must be
                parsed. self.tagparser will be used.

        Yields:
            tuple: A generated rule.
                [0]: `if` part;
                [1]: `then` part.

        """

        # Tag sentence using MorphologyRecognizer to compare it with GC one.
        tagged = self.ctxprocc.tagged(text)

        # Compare GC and tagged sentence
        for gctoken, recognized in zip(sentence, tagged):

            if (
                # Some of tokens is missed, so lengths of lists differs
                not gctoken or not recognized or
                # Some token do not correspond to GC one.
                recognized["word"] != self.reader.extractProperty(
                    gctoken, self.reader.FORMNAME
                )
            ):
                raise TokenizationError(
                    f"Tokenization error for sentence: {text}"
                )

            if "xpos" not in recognized:
                raise TaggingError(
                    f"Tag \"{recognized}\" was not recognized."
                )

        # Extract tokens from GC data
        sentence = list(map(
            lambda token: self.reader.extractProperty(
                token, self.reader.TOKENNAME
            ),
            sentence
        ))

        # Parse XPOS tags if needed
        if parseTags:
            for token in sentence:
                token.update(self.tagparser.parse(token["xpos"]))

        for gc, tagged in zip(
            context(sentence, r), context(tagged, r)
        ):
            ifblock = self.conclude(gc, tagged)

            # Do not add too small rules. Len of `if` must be less than 4:
            # __position + __name + ...comparisons
            if not ifblock or len(ifblock) < 4:
                continue

            thenblock = self.adjust(tagged["center"], gc["center"])

            yield (ifblock, thenblock)

    def generateRules(
        self, r=3, parsetags=True, limit=0, offset=0, swallowexcs=None
    ):
        """This function fetch sentences in self.reader by its `nextSentence`
        method and yield rules.

        Args:
            r (int): Radius of contexts to analyze.
            parsetags (bool): Set to True to parse XPOS tags in sentence using
                self.tagparser.
            limit, offset (int): Set limitations on sentences to be processed.
            swallowexcs (*): If your tag parser raises errors that can be
                ignored, pass them here.
                For example, if tag parser can't parse XPOS tag for some word
                in context, the rule with this words can be just skipped.

        Yields:
            tuple: A Ctx19 rule:
                [0]: `if` block
                [1]: `then` block

        """

        if not limit:
            limit = float("inf")

        counter = 0

        # All errors in sentence processing will be swallowed (except for
        # EOFError and BreakException)
        while True:

            try:

                sen = self.reader.nextSentence()

                counter += 1

                # Continue and break operators is not working in try...except
                # blocks for some reason
                if counter < offset:
                    raise ContinueException

                if counter > limit:
                    raise StopIteration

                # processSentence returns list of rules for some sentence
                for rule in self.processSentence(
                    sentence=sen["sentence"],
                    text=self.reader.getAttr(sen, "text"),
                    r=r, parseTags=parsetags
                ):
                    yield rule

            except (EOFError):
                break

            except swallowexcs:
                continue

            except (ContinueException, TokenizationError, TaggingError):
                continue

    def simplify(self, rules, save):
        """Looks through rules, search similar ones and merge them.

        Args:
            rules (list): List of tuples: (`if`, `then`)
            save (int, float): Saving coefficient (look for documentation in
                merge's docstring).

        Returns:
            generator or list of tuples: Resulting rule list.

        Structure of `rules`:
        [  rules (list)
            (  rule (tuple), len(rule) == 2
                {  conditions (dict)
                    {
                        "__name": "previous",
                        "__position": 1,
                        "property": "value",
                        ...
                    },
                    ...
                },
                {  assignments (dict)
                    "afterproperty": "aftervalue"
                }
            ),
            ...
        ]

        """

        # This double loop will iterate list(rules) like in bubble sort
        # algorithm.
        for i, (cond1, assign1) in enumerate(rules):

            # Here `cond` is `condition`, `assign` is `assignment`
            for j, (cond2, assign2) in enumerate(rules):

                # Skip first i elements.
                if j <= i:
                    continue

                # Two rules is equal if they're reach the same properties
                if assign1 != assign2:
                    continue

                merged = self.merge(cond1, cond2, save)

                # If rules cannot be merged with the given save coefficient,
                # skip it.
                if not merged:
                    continue

                # Change rule
                rules[i] = (list(merged), assign1)

                # And delete the second rule.
                del rules[j]

        return filter(
            lambda obj: obj is not None,
            rules
        )

    def merge(self, cond1, cond2, save=0.5):
        """Merge two conditions set with some coefficient of saving.

        Args:
            cond1, cond2 (dict): Dicts of selector.
            save (int, float): If less, then min(len(cond1), len(cond2))*save
                conditions was saved, function will return None.
                For example:
                save=0.5 means that more then half of the minimum-sized
                    selector must be saved.
                save=0.25 means one quarter of minimum-sized selector.

        Returns:
            generator of list: Selectors of merged conditions.
            bool None: If merged conditions does not meets saving coefficient.

        """

        def get(where, compareTo):
            """Returns selector from `where` which ["__name"] and
            ["__position"] properties is equal to `compareTo` ones.

            Args:
                compareTo (dict): Dict of selector.

            Returns:
                dict: Found selector.
                bool None: If no matches.

            """

            for sel in where:
                if (
                    sel["__name"] == compareTo["__name"] and
                    sel["__position"] == compareTo["__position"]
                ):
                    return sel

            return None

        def image(what, to):
            """Return intersection of `what` and `to` which consists of
            elements that meet this condition:
                every what[A][B] == to[A][B]
            Here A is iterable selector and B is iterable key of selector and
            A with B is equal in right and left parts of equation at one
            iteration.

            Args:
                what, to (list of dict): Selectors list to process.

            Returns:
                list: Resulting selectors list.

            """

            # If two rules is absolutely equal, then return just one
            if what == to:
                return what

            result = list()

            # Unpack `what` list to `sel1` (from `what`) and to `sel2` (which
            # is result of get(sel1, what) method execution)
            for sel1, sel2 in [
                (
                    sel, get(what, sel)
                )
                for sel
                in to
            ]:

                # Skip selector if it is not in `to` list
                if not sel2:
                    continue

                # If selector exists in both rules, then leave only equal keys
                # and skip different ones
                equal = dict()

                for key in sel1:

                    if key not in sel2:
                        continue

                    if sel1[key] == sel2[key]:
                        equal[key] = sel1[key]

                result.append(equal)

            return result

        merged = image(cond1, cond2)

        # This will calculate total number of conditions of `merged`.
        if reduce(
            # Every selector contains `__position` and `__name` keys which
            # should not be added to total number.
            lambda total, selector: total + len(selector) - 2,
            # List; initial value
            merged, 0
        ) <= min(
            # If save==0.5 than this condition will check if less than half of
            # the number of the original conditions was saved.
            len(cond1), len(cond2)
        ) * save:
            return None

        return filter(
            # If selector contains less then 2 keys then it don't have any
            # conditions. (Minus __position and __name).
            lambda selector: len(selector) > 2,
            merged
        )

    def train(
        self, r=3, parsetags=True, limit=0, offset=0, swallowexcs=None,
        saveCoeff=0.5
    ):
        """This will run train process: generate rules, compress them and
        upload to DB.

        Args:
            r (int): Radius of context to be processed near token.
            limit, offset (int): Limit and offset of sentences from GC.
            swallowexcs: If the tagparser you've specified raises errors on
                some sentences, this sentences can just be skipped. Specify
                these errors here.
            saveCoeff (int, float): Coefficient of saving conditions when
                merging (compressing) two rules.
                Example:
                saveCoeff=0.5 means that at least half of the minimum-sized
                    selector's condition must be saved.
                saveCoeff=0.25 means one quarter
                and so on.

        """

        generated = self.generateRules(
            r, parsetags, limit, offset, swallowexcs
        )

        simplified = list()

        for cond, assign in self.simplify(
            rules=list(generated), save=saveCoeff
        ):
            simplified.append({
                "if": cond,
                "then": assign
            })

        self.collection.insert(simplified)

    def close(self):
        """Close DB cursor.
        """

        self.db.close()


class TaggingError(Exception):
    pass


class TokenizationError(Exception):
    pass


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass
