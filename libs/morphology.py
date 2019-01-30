"""Use this library to recognize morphology of the token. It'll look for an
appropriate rule in DB and returns you the result.
"""


class MorphologyRecognizer:
    """This class contains methods for morhology processing.
    """

    def __init__(self, collection):
        """Init the recognizer with specified db connetion.

        Args:
            collection (Collection): A Collection from pymongo that will be
                used for rules searching.

        """

        self.collection = collection

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

    def recognize(self, token, applierFunc=None):
        """Apply exceptions, static and rules searching in order to guess XPOS
        of the given token.

        Args:
            token (str)
            applierFunc (function): Searching might return a bundle of rules,
                not just one correct, so you can specify a function which will
                extract element you're really need. You can also use a static
                method selectFirst() from this class to select the first
                rule from the list.

        applierFunc Args:
            list: List of rules from DB.
            token: Current token.

        Returns:
            dict: A rule as it stored in DB.
                {
                    "_id": ...,
                    "upos": "...",
                    "xpos": "..."
                }
                If XPOS wasn't recognized, returns None.

        """

        token = token.lower()
        funcs = [self.getExceptions, self.getStatic, self.getRulesFor]
        for func in funcs:
            query = func(token)
            if len(query) != 0:
                return applierFunc(query, token) if applierFunc else query

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
            key=lambda rule: len(rule["data"][0]),
            reverse=True
        )

        return bundle[0] if bundle else None
