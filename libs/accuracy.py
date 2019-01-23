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

    def __init__(self, reader, limit, recognizer, applierFunction):
        """Prepare an analyser.

        Args:
            reader (*): On of readers specified in gc.py. It should contain
                nextLine() method and DATALINE constant.
            limit (int): Limit on tokens to analyze.
            recognizer (MorphologyRecognizer): A class specified in
                morphology.py. It should contain recognize() method.
            applierFunction (function): Applier function for your recognizer.

        """
        self.reader = reader
        self.limit = limit
        self.recognizer = recognizer
        self.applier = applierFunction

    def init(self):
        """Init a generator function. next() does the next check and returns
        token with info.

        Yields:
            dict: {
                token: str,
                result: list of dict: Rules as they're stored in DB,
                applierResult: dict: Rule from applierFunc
            }

        """

        try:
            # All non-DATALINE lines will be 'continue'd
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
                applierResult = self.recognizer.recognize(token, self.applier)

                self.CHECKED += 1

                if result:
                    if upos in keyExtract(result, "upos"):
                        self.IMPROVE_UPOS += 1
                        if applierResult and upos == applierResult["upos"]:
                            self.CORRECT_UPOS += 1
                    if xpos in keyExtract(result, "xpos"):
                        self.IMPROVE_XPOS += 1
                        if applierResult and xpos == applierResult["xpos"]:
                            self.CORRECT_XPOS += 1

                yield {
                    "token": token,
                    "result": result,
                    "applierResult": applierResult
                }

        except EOFError:
            raise StopIteration
