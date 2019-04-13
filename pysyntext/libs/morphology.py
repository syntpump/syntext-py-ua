"""Use this library to recognize morphology of the token. It'll look for an
appropriate rule in DB and returns you the result.
"""

from .arrproc import isSupsetTo
import libs.strproc as strproc


class MorphologyRecognizer:
    """This class contains methods for morphology processing.
    """

    def __init__(
        self, collection, tagparser=None, priorityList=None, applierFunc=None
    ):
        """Init the recognizer with specified db connection.

        Args:
            collection (Collection): A Collection from pymongo that will be
                used for rules searching.
            tagparser (Class): Class with "parse" method which can parse XPOS
                of the token.
            priorityList (list): Specify dominating of one type over another.
                (See the example below).
            applierFunc (function): Searching might return a bundle of rules,
                not just one correct, so you can specify a function which will
                extract element you're really need. You can also use a static
                method selectFirst() from this class to select the first
                rule from the list.

        applierFunc Args:
            list: List of rules from DB.
            token: Current token.

        priorityList example:
            Suppose, we have this data:
            priorityList = [
                {
                    __what: {
                        xpos: "Q"
                    }
                    __replace: {
                        xpos: "Css",
                        upos: "CCONJ",
                        ...additional parameters
                    }
                },
                ...
            ]
            That means the every occuring of "Q" XPOS will be replaced with
            "CCONJ Css" pos, but only when both of them are presented in DB
            response. Any other parameters ("additional parameters") will be
            added to the token's rule too.
            This may be useful when two equal words appears to be different
            POS, but one of them more frequent.

        """

        self.prioritizer = Prioritizer(priorityList)
        self.collection = collection
        self.tagparser = tagparser
        self.applier = applierFunc

    def getRulesFor(self, token):
        """Guess all the rules that can be applied to this token.

        Args:
            token (str)

        Returns:
            list: A list of rules as they are stored in DB. An empty list if
                nothing works.

        """

        query = self.collection.aggregate([
            {
                "$match": {
                    "$expr": {
                        "$anyElementTrue": {
                            "$map": {
                                "input": "$data",
                                "as": "s",
                                "in": {
                                    "$ne": [
                                        -1,
                                        {
                                            "$indexOfBytes": [
                                                token, "$$s"
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    "data": {
                        "$type": "array"
                    },
                    "type": "rules"
                }
            }
        ])

        return list(query)

    def getStatic(self, token):
        """Look if this token has static POS and returns a rule for it.

        Args:
            token (str)

        Returns:
            list:  A list of rules as they are stored in DB. An empty list if
                nothing works.

        """

        return list(
            self.collection.find({
                "type": "static",
                "data": {
                    "$in": [token]
                }
            })
        )

    def getExceptions(self, token):
        """Look if this token is an exception and returns a rule for it.

        Args:
            token (str)

        Returns:
            list: A list of rules as they are stored in DB. An empty list if
                nothing works.

        """

        return list(
            self.collection.find({
                "type": "exceptions",
                "data": {
                    "$in": [token]
                }
            })
        )

    def recognize(self, token):
        """Apply exceptions, static and rules searching in order to guess XPOS
        of the given token.

        Args:
            token (str)

        Returns:
            dict: A rule as it stored in DB.
                {
                    "_id": ...,
                    "upos": "...",
                    "xpos": "..."
                }
                If XPOS wasn't recognized, returns None.
                Returns list of rules if one exist.

        """

        token = token.lower()

        special = self.recognizeSpecial(token)
        if special:
            return special if self.applier else [special]
        del special

        funcs = [self.getExceptions, self.getStatic, self.getRulesFor]
        query = None  # Response from DB
        result = None  # Result rule
        for func in funcs:
            query = func(token)
            if len(query) != 0:
                result = self.applier(query, token) if self.applier else query
                break

        if not result:
            return None

        # Prioritizer won't process a list of tokens, just one
        if self.applier:
            self.prioritizer.apply(result, query)

        # This will delete all the keys except upos and xpos and parse the XPOS
        if self.tagparser and self.applier:
            result = self.unwrapXPOS({
                "upos": result["upos"],
                "xpos": result["xpos"]
            })

        return result

    def recognizeSpecial(self, token):
        """Recognize tokens where not db querying are needed (sym, punct etc.)

        Args:
            token (str): Token to be recognized.

        Returns:
            dict: Rule for token.
                {
                    "xpos": ...,
                    "upos": ...
                }

        """

        if strproc.isPunct(token):
            return {
                "upos": "PUNCT",
                "xpos": "U",
                "name": "Punctuation"
            }

        if strproc.isSym(token):
            return {
                "upos": "SYM",
                "xpos": "X",
                "name": "Residual"
            }

        if strproc.hasNonUkrainian(token):
            return {
                "xpos": "X",
                "upos": "X",
                "name": "Residual"
            }

    def unwrapXPOS(self, rule):
        """Append properties of XPOS to the rule.

        Args:
            rule (dict): Rule with ["xpos"] property.

        Returns:
            {**rule, **parsedXPOS}

        """

        if self.tagparser:
            return {
                **rule,
                **self.tagparser.parse(rule["xpos"])
            }
        else:
            return rule

    @staticmethod
    def selectFirst(bundle, token):
        """Returns first document in bundle.

        Args:
            (See MorphologyRecognizer.recognize)

        Returns:
            dict: A document as it was stored in DB.

        """

        return bundle[0] if bundle else None

    @staticmethod
    def selectByEnding(bundle, token):
        """Returns first document in bundle, but except those which rule does
        not match with the very ending or the beginning of the token.

        Args:
            (See MorphologyRecognizer.recognize)

        Returns:
            dict: A document is it was stored in DB.

        """

        def getBiggestEdge(li, string):
            """Returns first item from list if that can be ending of beginning
            of the word.
            """
            # Longest rules first
            li.sort(key=len, reverse=True)

            for item in li:
                # Do not allow strings with len=1 recognize as the beginnings
                if len(item) == 1:
                    if string[-len(item):]:
                        return item
                elif string[:len(item)] == item or string[-len(item):] == item:
                    return item

            return None

        for rule in bundle:
            # Replace list of rules with one-element list. Element will be
            # chosen by getBiggestEdge
            rule["data"] = [getBiggestEdge(rule["data"], token)]

        bundle.sort(
            # Move down empty rules
            key=lambda rule: len(rule["data"][0]) if rule["data"][0] else 0,
            reverse=True
        )

        return bundle[0] if bundle else None


class Prioritizer:
    """This class provides interface to apply priority lists to morphology
    recognizing. For description see MorphologyRecognizer.recognize method.
    """

    def __init__(self, li=None):
        """Init the class and remember the list.

        Args:
            li (list): Priority list in the following format:
                [
                    {
                        "__what": {  # Here listed properties to replace.
                            "upos": "...",
                            ...
                        }
                        "__replace": {  # New properties which will be applied.
                            "upos": "...",
                            ...
                        }
                    },
                    ...
                ]

        """

        self.li = li

    def apply(self, token, response):
        """Apply the rules to the token.

        Args:
            token (dict): Dictionary of the token.
            response (list): Rules returned from DB.

        Return :
            dict: Resulting token.

        """

        if not self.li:
            return token

        # Unpack each {__what: .., __replace: ..} in self.li as (what, replace)
        for what, replace in [
            (rule["__what"], rule["__replace"]) for rule in self.li
        ]:

            if not isSupsetTo(token, what):
                continue

            if self.responseContains(replace, response):
                token.update(replace)
                # Do only first replacement
                break

        return token

    def responseContains(self, what, response):
        """Returns True if response contains rule with the properties defined
        in `what`.

        Args:
            what (dict): Dictionary to search.
            response (list): Response of DB.

        Returns:
            bool: True if found, False otherwise.

        """

        for item in response:
            if isSupsetTo(item, what):
                return True

        return False
