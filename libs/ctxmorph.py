"""This library contains methods for processing whole sentences and contexts.
"""

from libs.strproc import tokenize
from libs.morphology import MorphologyRecognizer
from ctx19.parsers import Contextual19Parser


class ContextualProcessor:
    """Contains methods for processing sentences. DB collection with rules
    are needed for initialization.

    Properties:
        collection (Collection): Collection for Ctx19 rules.
        recognizer (MoprhologyRecognizer)
        applier (function): Applier function for MorphologyRecognizer.
        priority (dict): Priority list for MorphologyRecognizer.
        tagparser (class): Class with 'parse' function which can parse XPOSes
           from DB.
        rulescoll (Collection): A pymongo Collection that will be used for
            contextual correcting. It must contains rules in Ctx19 object
            representation.
        ctx19 (Contextual19Parser): Parser for Ctx19

    """

    def __init__(
        self, collection, applier, priority=None, tagparser=None,
        rulescoll=None
    ):
        """Init the class with specified db connection.

        Args:
            collection (Collection): A Collection from pymongo that will be
                used for rules searching.
            applier (function): Applier function for MorphologyRecognizer.
            priority (dict): Priority list for MorphologyRecognizer.
            tagparser (class): Class with 'parse' function which can parse
                XPOSes from DB.
            rulescoll (Collection): A pymongo Collection that will be used for
                contextual correcting. It must contains rules in Ctx19 object
                representation.

        For applier and priority documentation see in MorphologyRecognizer
        docstring.

        """

        self.collection = collection
        self.recognizer = MorphologyRecognizer(
            collection, tagparser=tagparser
        )
        self.tagparser = tagparser
        self.applier = applier
        self.priority = priority
        self.ctx19 = Contextual19Parser()
        self.rulescoll = rulescoll

        # Upload all the rules to Ctx19 parser
        dbcursor = rulescoll.find({})
        dbcursor.skip(1)

        for rule in dbcursor:
            self.ctx19.data.append(rule)

    def tagged(self, sentence):
        """Tokenize sentence and recognize morphology of each ones.

        Args:
            sentence (str): String of sentence.

        Returns:
            list of dict: List of dicts of tokens. Example:
                [
                    {upos:..., voice:...},
                    ...
                ]
                There will be this list of properties in each of token:
                    word (str): Word before recognizing.

        """

        tokens = tokenize(sentence)
        processed = list()

        for token in tokens:
            recognized = self.recognizer.recognize(
                token=token,
                applierFunc=self.applier,
                priorityList=self.priority
            )
            # Return empty dict if token was not recognized
            if not recognized:
                recognized = dict()
            recognized["word"] = token
            processed.append(recognized)

        return processed

    def corrected(self, sentence):
        """Apply correcting rules from self.rulescoll to the specified
        sentence.

        Args:
            sentence (list): List of sentence.

        Returns:
            list: Corrected sentence.

        """

        sentence = self.ctx19.apply(sentence)

        # Modify XPOS tags in tokens according to their new properties
        for token in sentence:
            token["xpos"] = self.tagparser.stringify(token)

        return sentence
