"""Library for making pretty file logs in Markdown format.
"""


import datetime
import json


class Logger:
    """This class contains methods for making logs into files.
    """

    def __init__(self, filepath):
        """Opens a file in appending mode and type a datetime at the beginning.

        Args:
            filepath (str): A path to file to open.

        Raises:
            FileNotFoundError: The file is not exists.
            PermissionError: You're not allowed to access to this file. This
                error also can occur when the path you specified is directory,
                not a file.

        """

        self.file = open(filepath, mode="a+", encoding="utf-8")
        self.file.write(
            datetime.now().strftime(
                "# Started at %I:%M%p %d %h, %a '%y\n"
            )
        )

    def logjson(self, data):
        """Put a formatted json-line into file.

        Args:
            data (list, dict): Data to print.

        """

        self.file.write(
            json.dumps(
                data,
                indent=4,
                default=lambda o: "<unserializable>",
                ensure_ascii=False
            )
        )

    def write(self, string):
        """Put the data into file.

        Args:
            string (str): Data to print.

        """

        self.file.write(string)
