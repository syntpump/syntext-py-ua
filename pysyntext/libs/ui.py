"""Lib for creating console UI.
"""


def progress(current, total=100, msg=""):
    """Print rewritable message with information about some progress.
    To erase this message, call done() function.

    Args:
        current (int): Value of progress.
        total (int): Maximum value of progress.
        msg (str): Additional message that will be printed with progress
            numbers.

    STDOUT:
        Prints message:
        {current} / {total}    relation%    {msg}

    """
    print(
        (
            f"{current} / {total}\t"
            f"{percentage(current, total)}\t"
            f"{msg}"
        ),
        end="\r"
    )


def done(msg=""):
    """Erase progress message and type msg argument.

    Args:
        msg (str): Message that will be showed.

    STDOUT:
        Prints message:
        {msg}

    """
    print(f"\n{msg}")


def percentage(sub, all):
    """Calculate percent relation between "sub" and "all".

    Args:
        sub (int): Some value.
        all (int): Maximum value.

    Returns:
        int: (sum * 100) / all

    """

    return int((sub * 100) / all)


def expect(msg, what: list):
    """Expect one of the input from the given list. Repeat it infinitely.

    Args:
        msg (str): This message will be showed before input field.
        what (list): List of expected input

    Returns:
        *: Inputed data.

    STDOUT:
        Prints message:
        {msg}

    """

    data = None

    while data not in what:
        print(msg, end="")
        data = input()

    return data
