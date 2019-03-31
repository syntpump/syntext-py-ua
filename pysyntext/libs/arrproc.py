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


def isSupsetTo(d: dict, what: dict):
    """Check whether one `d` dict is supset or equal to `what` dict. This means
    that all the items from `what` is equal to `d`.

    Args:
        d, what (dict): Dicts to compare.

    Returns:
        bool: True if d > what, False otherwise.

    """

    for key, value in what.items():
        if d[key] != value:
            return False

    return True


def findIn(d: dict, equal):
    """Find and return record in dictionary which is associated with `equal`.
    May be useful for searching unique objects in large amounts of data.

    Args:
        d (dict): Dictionary where to search in.
        equal (*): What to look for. If it's a dict, item which is supset for
            the given will be found.

    Returns:
        namedtuple: DictItem(key=..., item=...)

    Example:
        >>> findIn({'a': 0,  'b': 1}, 1)
        <<< DictItem(key='b', item=1)
        >>> findIn({'a': {'b': 'c', 'd': 'e'}}, {'d': 'e'})
        <<< DictItem(key='a', item={'b': 'c', 'd': 'e'})

    """

    for key, item in d.items():
        if (
            type(equal) is dict and isSupsetTo(item, equal)
        ) or item == equal:
            return {"key": key, "item": item}

    raise KeyError("Value was not found")
