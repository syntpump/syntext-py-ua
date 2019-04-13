"""Contains classes for accuracy analysis.
"""

from .arrproc import keyExtract


class XPOSRecognitionAnalyzer:
    """Analyze the accuracy of recognition tokens' morphology.

    Properties:
        CHECKED (int increment): Number of analyzed tokens.
        CORRECT_XPOS (int increment): Number of correct recognized XPOS.
        CORRECT_UPOS (int increment): Number of correct recognized UPOS.
        IMPROVE_XPOS (int increment): XPOS recognition might be improved with
            changing applierFunc.
        IMPROVE_UPOS (int increment): UPOS recognition might be improved with
            changing applierFunc.
        reader (*): On of readers specified in gc.py. It should contain
            nextLine() method and DATALINE constant.
        limit (int): Limit on tokens to analyze.
        recognizer (MorphologyRecognizer): A class specified in morphology.py
            It should contain recognize() method.
        applier (function): Applier function for your recognizer.

    """

    CHECKED = 0
    CORRECT_XPOS = 0
    CORRECT_UPOS = 0
    IMPROVE_XPOS = 0
    IMPROVE_UPOS = 0

    def __init__(
        self, reader, recognizer, applierFunction, limit=0, offset=0
    ):
        """Prepare an analyser.

        Args:
            reader (*): On of readers specified in libs/ud. It should contain
                nextLine() method and DATALINE constant.
            limit (int): Limit on tokens to analyze. Set to 0 to make it
                infinite.
            offset (int): Number of tokens from the beginning of the file to
                be skipped.
            recognizer (MorphologyRecognizer): A class specified in
                morphology.py. It should contain recognize() method.
            applierFunction (function): Applier function for your recognizer.

        """
        self.reader = reader
        self.limit = limit if limit != 0 else float("inf")
        self.offset = offset if offset else 0
        self.recognizer = recognizer
        self.applier = applierFunction

    def init(self):
        """Init a generator function next() does the next check and returns
        token with info.

        Yields:
            dict: {
                token: str,
                result: list of dict: Rules as they're stored in DB,
                applierResult: dict: Rule from applierFunc
            }

        """

        try:
            # Skip offset
            if self.offset != 0:
                i = 0
                while i < self.offset:
                    line = self.reader.nextLine()
                    if line["type"] == self.reader.DATALINE:
                        i += 1

            # All non-DATALINE lines will be skipped
            while True:
                if self.limit <= self.CHECKED:
                    raise StopIteration

                line = self.reader.nextLine()
                if line["type"] != self.reader.DATALINE:
                    continue

                token = self.reader.extractProperty(
                    line, prop=self.reader.FORMNAME
                )
                upos = self.reader.extractProperty(
                    line, prop=self.reader.UPOSNAME
                )
                xpos = self.reader.extractProperty(
                    line, prop=self.reader.XPOSNAME
                )

                result = self.recognizer.recognize(token)
                applierResult = self.recognizer.recognize(
                    token, self.applier
                )

                self.CHECKED += 1

                checks = {
                    "IMPROVE_UPOS": False,
                    "IMPROVE_XPOS": False,
                    "CORRECT_UPOS": False,
                    "CORRECT_XPOS": False
                }

                if result:

                    if upos in keyExtract(result, "upos"):

                        checks["IMPROVE_UPOS"] = True
                        self.IMPROVE_UPOS += 1

                        if applierResult and upos == applierResult["upos"]:

                            checks["CORRECT_UPOS"] = True
                            self.CORRECT_UPOS += 1

                    if xpos in keyExtract(result, "xpos"):

                        checks["IMPROVE_XPOS"] = True
                        self.IMPROVE_XPOS += 1

                        if applierResult and xpos == applierResult["xpos"]:

                            checks["CORRECT_XPOS"] = True
                            self.CORRECT_XPOS += 1

                yield {
                    "checks": checks,
                    "token": token,
                    "result": result,
                    "applierResult": applierResult,
                    "gc": line
                }

        except EOFError:
            raise StopIteration
