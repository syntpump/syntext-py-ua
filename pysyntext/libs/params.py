"""This lib will help you to catch parameters which user are passing to script.
All bool parameters should start with "-": -quiet, -verbose, etc.
All non-bool parameters should start with "--" and must be followed with some
value: --filepath "path/to/file".

To use it, create Params class and all the parameters will be caught
automatically.
"""


import sys


class Params:
    """This class contains methods to deal with parameters user are passing to
    script.

    Properties:
        bundle (dict): Dict of parameters.

    Raises:
        TypeError: Something wrong with parameters, can't read it correctly.

    """

    def __init__(self):
        """This will catch terminal parameters which was passed to this script.
        """

        params = dict()
        i = 1
        try:
            while i < len(sys.argv):
                if sys.argv[i][:2] == '--':
                    params[sys.argv[i]] = sys.argv[i + 1]
                    i += 1
                else:
                    params[sys.argv[i]] = True
                i += 1
        except Exception as e:
            raise TypeError(
                "There's an mistake in your parameters. Use --parametername "
                "<value> to pass a value or -paramname to set something to "
                "True."
            )

        self.bundle = params

    def get(self, name, default=None):
        """Returns some parameter from self.bundle if it exists. If not, returns
        'default' parameter.

        Args:
            name (str): Name of parameter you want to get.
            default (*): Content you expect by default.

        Returns:
            str: Value of parameter you'd requested. If no such parameter
                specified, than None will be returned.

        """

        return self.bundle[name] if self.has(name) else default

    def has(self, name):
        """Returns True if the parameter with the given name exists.name

        Args:
            name (str): Name of parameter.

        Returns:
            bool: Is parameter exists in self.bundle?

        """

        return name in self.bundle

    def request(self, name, text):
        """Show a text to user and require some data to input. That data will
        be put to self.bundle then.

        Args:
            name (str): Name of data (parameter) you're requesting.
            text (str): A little description user will see.

        Returns:
            str: Some data user had typed.

        STDOUT:
            Prints a message:
            {text}:

        STDIN:
            Grab the inputted data.

        """

        print(text, end=": ")
        data = input()
        self.bundle[name] = data
        return data

    def isEmpty(self):
        """Returns True, if no parameters was passed.
        """

        return len(self.bundle) == 1

    def getdict(self):
        """Return parameters as dictionary.

        Returns:
            dict: Dictionary without '--' or '-' at the beginning of keys.

        """

        di = dict()

        for key in self.bundle:
            name = key[2:] if key[:2] == "--" else key[1:]
            di[name] = self.bundle[key]

        return di
