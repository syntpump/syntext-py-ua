class GCReader:
    """Base class for all GC readers.

    Properties:
        COMMENTLINE = 0 (const int): Marker for comment line.
        DATALINE = 1 (const int): Marker for line with data.
        BLANKLINE = 2 (const int): Marker for blank line. Blank lines are being
            used to separate sentences.
        file (_io.TextIOWrapper): Opened file.
        ignoreComments (bool): Set this True in order to ignore comment lines.
        strict (bool): Set this to True in order to check format strictly.
        cursor (int): Pointer to the current line.

    """

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
                all comments in file will be ignored.
            strict (bool): Set this to True in order to check format strictly.

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
