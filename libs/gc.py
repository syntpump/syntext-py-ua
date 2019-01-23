"""This library can be used to read and parse files with morphosyntactic data.

== Currently supported formats ==
Name:           Class:
CoNLL-U         conlluReader

To perform reading, init the class you need and pass the path to file. You'll
be given access to nextLine() and nextSentence() methods.
"""


class ConlluReader:
    """Use this class to read and parse Universal Dependencies data in CoNLL-U
    format.

    Properties:
        COMMENTLINE = 0 (const int): Marker for comment line.
        DATALINE = 1 (const int): Marker for line with data.
        BLANKLINE = 2 (const int): Marker for blank line. Blank lines are being
            used to separate sentences.
        file (_io.TextIOWrapper): Opened file.
        ignoreComments (bool): Set this True in order to ignore comment lines.
        strict (bool): Set this to True in order to allow 'id', 'upos',
            'head', 'deprel' fields be unspecified, 'form' and 'lemma' fields
            to contain space characters and let some fields be empty.
        cursor (int): Pointer to the current line.

    """

    # nextLine()'s output will be marked with this constants.
    COMMENTLINE = 0
    DATALINE = 1
    BLANKLINE = 2

    # Since these fields are different from format to format, the universal
    # interface should be provided.
    # Name of field which contains language-specific POS.
    XPOSNAME = 'xpos'
    # Name of field which contains universal POS.
    UPOSNAME = 'upos'
    # Name of field which contains token as it occurs in the text.
    FORMNAME = 'form'
    # Name of field which contains lemma.
    LEMMANAME = 'lemma'

    def __init__(self, filepath=None, ignoreComments=False, strict=True):
        """Open the file for parsing and set cursor to 0.

        Args:
            filepath (str): Path to a file you want to read.
            ignoreComments (bool): When this variable is set to True,
                nextLine() method will ignore lines staring with '#'.
            strict (bool): Set this to True in order to allow 'id', 'upos',
                'head', 'deprel' fields be unspecified, 'form' and 'lemma'
                fields to contain space characters and let some fields be
                empty.

        Raises:
            TypeError: The path to file was not given.
            FileNotFoundError: The file is not exists.
            PermissionError: You're not allowed to access to this file. This
                error also can occur when the path you specified is directory,
                not a file.

        """

        if not filepath:
            raise TypeError("You need to provide a path to file with data.")

        self.file = open(filepath, mode='r', encoding="utf-8")
        self.ignoreComments = ignoreComments
        self.cursor = 0
        self.strict = strict

    def rewind(self):
        """Move reading cursor to the beginning.
        """

        self.file.seek(0)
        self.cursor = 0

    def parseFeats(self, line):
        """Convert FEATS line to a dict object. The FEATS field contains a list
        of morphological features, with vertical bar (|) as list separator and
        with underscore to represent the empty list. All features should be
        represented as attribute-value pairs, with an equals sign (=)
        separating the attribute from the value.

        Here's the example for line:
            (1) Case=Nom|Definite=Def|Gender=Com|Number=Sing
            (2) _

        Args:
            line (str): FEATS line.

        Returns:
            dict: Converted line.

        Example of return (correspond to 'line' examples):
        (1) {
            "Case": "Nom",
            "Definite": "Def",
            "Gender": "Com",
            "Number": "Sing"
        }
        (2) False

        """

        if line == '_':
            return False

        data = dict()

        line = line.split('|')
        for feature in line:
            pair = feature.split('=')
            data[pair[0]] = pair[1]

        return data

    def nextLine(self):
        """Parse the next line of the file, return it and increase cursor.

        Raises:
            EOFError: End of the file was reached.
            TypeError: Some of the fields in line is missing.
            TypeError: Some specified field is missing.
            TypeError: Fields other than 'form' and 'lemma' must not contain
                space characters.
            TypeError: Fields 'id', 'upos', 'head', 'deprel' cannot be
                unspecified.
            ...Errors from self.parseFeats()

        Returns:
            dict: A parsed line.

        Examples of return:
            (1)
            {
                "type": self.DATALINE,
                "data": {
                    "id": "9",
                    "form": "самовладності",
                    "lemma": "самовладність",
                    "upos": "NOUN",
                    "xpos": "Ncfsgn",
                    "feats": {
                        "Animacy": "Inan",
                        "Case": "Gen",
                        "Gender": "Fem",
                        "Number": "Sing"
                    },
                    "head": "7",
                    "deprel": "conj",
                    "deps": "6:obj|7:conj",
                    "misc": "Id=01rm|LTranslit=samovladnisť"
                }
            }

            (2)
            {
                "type": self.COMMENTLINE,
                "data": {
                    "doc_title": "«Я обізвуся до них…»"
                }
            }

            (3)
            {"type": self.BLANKLINE}

        """

        line = self.file.readline()

        # Increase cursor to remember current reading line.
        self.cursor += 1

        # Even empty lines contains '\n', so when length of the line is 0,
        # end of the file was reached.
        if len(line) == 0:
            raise EOFError("End of the file was reached.")

        # Blank lines contains at least '\n'.
        if len(line) == 1:
            return {
                "type": self.BLANKLINE
            }

        # Go to the next line if current is a comment.
        if line[0] == '#':
            if self.ignoreComments:
                return self.nextLine()
            else:
                # Lines like: "# newdoc id = abracadabra\n" will be converted
                # to the following dict:
                # {
                #     "type": ConlluReader.COMMENTLINE,
                #     "data": {
                #         "newdoc id": "abracadabra"
                #     }
                # }
                #
                # Furthermore, if line contains several ' = ', it will be
                # splited only by first one. So that "value = data = 8" becomes
                # {"value": "data = 8"}.
                data = line[2:-1]
                # Avoid splitting comment which don't contain equal sign.
                if " = " in data:
                    data = data.split(" = ", maxsplit=1)
                    data = {data[0]: data[1]}
                return {
                    "type": self.COMMENTLINE,
                    "data": data
                }

        # Here's how fields of file us named in CoNLL-U Format:
        fields = [
            "id", "form", "lemma", "upos", "xpos", "feats", "head", "deprel",
            "deps", "misc"
        ]
        line = line.split('\t', maxsplit=10)
        if len(line) != 10:
            raise TypeError(
                f"Some of the field is missing. When you want to make field "
                f"blank, just leave it with '_'. Error at {self.cursor} line "
                f"in {self.file.name}."
            )

        data = dict()

        for i, value in enumerate(line):

            field = fields[i]

            if self.strict:

                if not value or value == ' ':
                    raise TypeError(
                        f"The '{field}' field field is missing at "
                        f"{self.cursor} line in {self.file.name}."
                    )

                if ' ' in value and field in ['form', 'lemma']:
                    raise TypeError(
                        f"Fields other than 'form' and 'lemma' must not "
                        f"contain space characters. Error at {self.cursor} "
                        f"line in {self.file.name}."
                    )

                if value == '_' and field in ['id', 'upos', 'head', 'deprel']:
                    raise TypeError(
                        f"Fields 'id', 'upos', 'head', 'deprel' cannot be "
                        f"unspecified. Error at {self.cursor} line in "
                        f"{self.file.name}."
                    )

            if field == 'feats':
                value = self.parseFeats(value)

            data[field] = value

        return {
            "type": self.DATALINE,
            "data": data
        }

    @staticmethod
    def extractProperty(line, prop="form"):
        """Returns property from the result of nextLine() execution.
        Since the every format is different and nextLine() reader may returns
        different results, the universal interface for extracting specified
        properties from line must be provided.

        Args:
            line (dict): A result of nextLine() execution.
            prop (str): A property to extract. "form" by default, which means
                "token as it occurs in text".

        Returns:
            str: If the line is DATALINE.
            bool: False otherwise.

        """

        return line["data"][prop]

    def nextSentence(self):
        """Parse the next sentence.

        Returns:
            dict: Dict that contains datalines and comments.

        Raises:
            ...Errors from nextLine()

        Example of return:
            {
                "sentence": [
                    ...list of nextLine() outputs which .data == self.DATALINE
                ],
                "comments": [
                    ...list of nextLine() outputs
                    which .data == self.COMMENTLINE
                ]
            }

        """

        sentence = []
        comments = []

        line = self.nextLine()

        while line["type"] != self.BLANKLINE:
            if line["type"] == self.DATALINE:
                sentence.append(line)
            else:
                comments.append(line)
            line = self.nextLine()

        return {
            "sentence": sentence,
            "comments": comments
        }

    def get(self, attribute, default=None):
        """Look for some property, defined in the comment, at the beginning of
        the file. (E.g., "newdoc id" or "doc_tittle").

        Args:
            attribute (str): Name of attribute you want to get.
            default (*): Data that will be returned if not such attribute
                specified.

        Return:
            str: Parameter you'd requested. If no such parameter specified,
                None will be returned.

        """

        # Remember current position.
        cursor = self.file.tell()

        # Go to the beginning of the file.
        self.rewind()

        respond = None
        line = self.nextLine()

        while line["type"] == self.COMMENTLINE:
            if attribute in line["data"]:
                respond = line["data"][attribute]
            line = self.nextLine()

        # Return to prevoius position.
        self.file.seek(cursor)

        return respond if respond else default
