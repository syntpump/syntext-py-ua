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

        query = self.collection.find({
            "type": "rules",
            "data": {
                "$regex": rf"^[{token}]+$"
            }
        })

        def substringExists(document):
            """Returns True if one of string in document["data"] is a substring
            for token.
            """

            for string in document["data"]:
                if string in token:
                    return True
            return False

        return list(
            filter(
                substringExists,
                query
            )
        )

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
                return applierFunc(query) if applierFunc else query

    @staticmethod
    def selectFirst(bundle):
        """Returns first document in bundle.

        Args:
            bundle (list): A list of documents.

        Returns:
            dict: A document as it stored in DB.

        """

        return bundle[0]
