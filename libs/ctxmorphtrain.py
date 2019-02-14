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
        self, db, reader, rulescoll, logger, tagparser, strictgc=False,
        applier=None, priority=None
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
            applier, priority: Applier function and priority list for
                MorphologyRecognizer.

        """

        self.db = db
        self.logger = logger
        self.reader = reader,
        self.collection = db.createCollection(db.EMENDPOS)
        self.ctxprocc = ContextualProcessor(
            collection=rulescoll,
            applier=applier,
            priority=priority,
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

    def conclude(self, ctx1, ctx2):
        """Compare two contexts and generate rule to make first context like
        the second one.

        Args:
            ctx1, ctx2 (dicts): Contexts dict as defined in strproc.context
                function.

        """

        pass

    def processSentence(self, sentence, text, r):
        """Recognize POSes of the sentence by MorphologyRecognizer and
        compare it with the given one.

        Args:
            sentence (list of dict): List of sentence with tokens.
            text (str): The same sentence but in simple string.
            r (int): Radius for comparing context.

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

        for gc, tagged in zip(
            context(sentence, r), context(tagged, r)
        ):
            pprint(self.conclude(gc, tagged), indent=4, compact=True)

    def close(self):
        """Close DB cursor.
        """

        self.db.close()


class TaggingError(Exception):
    pass
