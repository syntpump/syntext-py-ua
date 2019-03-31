"""This class implements language-specific POS tags in based on Universal
Dependencies specifications.
It will use udtxposdata.json file in this directory.

Format for UDT is the following:
    1st letter: universal POS
    (2, 3)n-th letters: property
    (4. 5, 6)n-th letters: value

Example:
    namanicsnomgnneunmsin
    ->
    n
    am ani
    cs nom
    gn neu
    nm sim
    ->
    NOUN
    Animacy Anim
    Case Nom
    Gender Neut
    Number Sing

"""

import json


class UDTParser:

    def __init__(self):
        """Open and parse udtxposdata.json file.

        Raises:
            FileNotFoundError: The file udtxposdata.json data is not exists.
            PermissionError: You're not allowed to access to udtxposdata.json
                file.

        """

        try:
            with open("libs/ud/udtxposdata.json") as fp:
                self.data = json.load(fp)
        except FileNotFoundError:
            raise FileNotFoundError("File udtxposdata.json was not found!")
