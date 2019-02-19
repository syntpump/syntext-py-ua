"""Library for making pretty file logs in Markdown format and printing data
into streams.
"""


import time
import json


class Logger:
    """This class contains methods for making logs into files and print them
    to console (or any other stream).

    Properties:
        stream: A stream to print short messages in.
        fp (file): A file to write big logs in.
        enabled (bool): Set this to False in order to disable any logs.

    """

    def __init__(self, enabled=True, stream=None, fp=None):
        """Initialize class, write datetime info into file if specified.
        You can use `stream` for warnings, short messages and progress info and
        `fp` to print big data in Markdown.

        Args:
            stream: A stream to print messages in.
            fp (file): A file to write big logs in.
            enabled (bool): If False, then no logs will be printed. You can set
                initial state here.

        """

        self.enabled = enabled

        self.stream = stream
        self.fp = fp

        if fp:
            print(
                time.strftime(
                    "# Started at %I:%M%p %d %h, %a '%y"
                ),
                file=fp
            )

    def logjson(self, data):
        """Put a formatted json-line into self.fp.

        Args:
            data (list, dict): Data to print.

        """

        if not self.enabled:
            return

        dumps = json.dumps(
            data,
            indent=4,
            default=lambda obj: str(type(obj)),
            ensure_ascii=False
        )
        print(f"```json\n{dumps}\n```", file=self.fp)

    def write(self, string):
        """Put the data into self.fp.

        Args:
            string (str): Data to print.

        """

        if not self.enabled:
            return

        print(string, end="", file=self.fp)

    def output(self, string, rewritable=False):
        """Print a message into self.stream.

        Args:
            string (str): Data to print.
            rewritable (bool): Set to True to print \r after message.

        """

        if not self.enabled:
            return

        print(string, end=("\r" if rewritable else "\n"), file=self.stream)
