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


def reorder(li: list, a: int, b: int):
    """Reorder li[a] with li[b].

    Args:
        li (list): List to process.
        a (int): Index of first item.
        b (int): Index of second item.

    Returns:
        list: List of reordered items.

    Example:
        >>> reorder([a, b, c], 0, 1)
        <<< [b, a, c]

    """

    li[a], li[b] = li[b], li[a]
    return li


def containesSupsetDict(li: list, search: dict):
    """Check whether list contains dict that is superset for specified dict.

    Args:
        li (list): List to search in.
        search (dict): Dictionary to compare.

    Returns:
        True: If one was found.
        False: Otherwise.

    Example:
        Suppose:
        search = {
            a: 0,
            b: 1,
            c: 2
        }
        True will be returned if `li` contains this dictionary:
        {
            a: 0,
            b: 1,
            c: 2,
            d: 3
        }
        or this:
        {
            a: 0,
            b: 1
        }

    """

    for item in li:
        if search.items() <= item.items():
            return True

    return False
