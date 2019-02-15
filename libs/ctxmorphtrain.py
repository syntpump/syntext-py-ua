"""Module for training CCMR.
"""

from .ctxmorph import ContextualProcessor
from .strproc import context
from pprint import pprint


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

    def differs(self, t1, t2):
        """Generator function, yields bundle of properties that are different
        in two given tokens.

        Args:
            t1, t2 (dicts): Two tokens to be compared.

        Yields:
            tuple:
                [0] str: Name of the next different property.
                [1] *: Value of this key in the first token.
                [2] *: Value of this key in the second token.

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

        """

        # If base and gc centers are equal
        if ctxbase["center"]["xpos"] == ctxto["center"]["xpos"]:
            return None

        ifblock = list()

        pass

    def processSentence(self, sentence, text, r, parsetags=False):
        """Recognize POSes of the sentence by MorphologyRecognizer and
        compare it with the given one.

        Args:
            sentence (list of dict): List of sentence with tokens.
            text (str): The same sentence but in simple string.
            r (int): Radius for comparing context.
            parsetags (bool): Check to True if tags from sentences must be
                parsed. self.tagparser will be used.

        """

        tagged = self.ctxprocc.tagged(text)

        # Compare two gc and tagged sentence
        for gctoken, recognized in zip(sentence, tagged):
            if (
                # Some of tokens is missed, so lengths of lists differs
                not gctoken or not recognized or
                # Some token do not correspond to GC one.
                recognized["word"] != self.reader.extractProperty(
                    gctoken, self.reader.FORMNAME
                )
            ):
                raise TaggingError([tagged, sentence])

        # Extract tokens from GC data
        sentence = list(map(
            lambda token: self.reader.extractProperty(
                token, self.reader.TOKENNAME
            ),
            sentence
        ))

        # Parse XPOS tags if needed
        if parsetags:
            for token in sentence:
                token.update(self.parsetags(token["xpos"]))

        for gc, tagged in zip(
            context(sentence, r), context(tagged, r)
        ):
            rule = self.conclude(gc, tagged)
            pprint(rule, indent=4, compact=True)

    def close(self):
        """Close DB cursor.
        """

        self.db.close()


class TaggingError(Exception):
    pass
