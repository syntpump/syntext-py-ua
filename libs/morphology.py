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
                    }
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

        """

        funcs = [self.getExceptions, self.getStatic, self.getRulesFor]
        for func in funcs:
            query = func(token)
            if len(query) != 0:
                return query[0]
