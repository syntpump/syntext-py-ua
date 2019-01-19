def keyExtract(array, key):
    """Returns values of specific key from list of dicts.

    Args:
        array (list): List to be processed.
        key (str): Key to extract.

    Returns:
        list: List of extracted values.

    Example:
    >>> keyExtract([
            {'a': 0, ...}, {'a': 1, ...}, {'a': 2, ...}, ...
        ], 'a')
    <<< [0, 1, 2]

    """

    res = list()
    for item in array:
        res.append(item[key])
    return res


def unduplicate(words):
    """Deletes duplicates from list.

    Args:
        words (list): List of hashable data.

    Returns:
        list: Unduplicated list.

    Raises:
        TypeError: Data of the list is not hashable (list, for example).

    """

    return list(
        set(words)
    )
