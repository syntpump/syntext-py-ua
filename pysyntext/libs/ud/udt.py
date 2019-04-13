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

import os
import json
from textwrap import wrap
from ..arrproc import findIn


class UDTParser:

    def __init__(self):
        """Open and parse udtxposdata.json file.

        Raises:
            FileNotFoundError: The file udtxposdata.json data is not exists.
            PermissionError: You're not allowed to access to udtxposdata.json
                file.

        """

        try:
            with open(
                os.path.join(
                    os.path.dirname(__file__),
                    "udtxposdata.json"
                )
            ) as fp:
                self.data = json.load(fp)
        except FileNotFoundError:
            raise FileNotFoundError("File udtxposdata.json was not found!")

    def parse(self, tag: str):
        """Returns features of the given tag.

        Args:
            tag (str): Tag of the token. Example: `namanicsnomgnneunmsin`

        Returns:
            dict: Parsed tag. Example: {
                'upos': 'Noun',
                'Animacy' : 'Inan',
                'Case' : 'Nom',
                'Gender' : 'Neut',
                'Number' : 'Sing'
            }

        Raises:
            IncorrectTag: Your tag is not valid.

        """

        #  ( (Length of tag - 1) mod 5 ) should be equal to 0:
        #  {pos letter} + {property: 3 len} + {value: 2 len} + ...
        if (len(tag) - 1) % 5 != 0:
            raise IncorrectTag(f"Something wrong with your tag: {tag}")

        feats = dict()

        try:

            #  Find name of POS by the first letter of tag
            feats["upos"] = findIn(self.data["poses"], tag[0])["key"]

            #  Unpack 'xaabbbccddd' as [aa, bbb], [cc, ddd]
            #  Response of findIn is DictItem(key=..., item=...)
            for prop, value in [
                (rec[:2], rec[2:])
                for rec
                in wrap(tag[1:], 5)
            ]:
                block = findIn(self.data["properties"], {"name": prop})

                # There's no shorten for this value
                if "props" not in block["item"]:
                    feats[block["key"]] = value.capitalize()
                    continue

                try:
                    feats[block["key"]] = findIn(
                        block["item"]["props"], value
                    )["key"]
                except KeyError:
                    feats[block["key"]] = value.capitalize()

        except (KeyError, IndexError):
            raise IncorrectTag(f"Unexisting property in your tag: {tag}")

        return feats

    def stringify(self, props):
        """Converts properties to POS tag.

        Args:
            props (dict): Properties. Example:
                {    'upos': 'NOUN', 'Animacy': 'Anim', 'Case': 'nom',
                    'Gender': 'Neut', 'Number': 'Plur'}

        Returns:
            str: Tag for this dict. Example: 'namanicsnomgnneunmsin'

        Raises:
            IndexError: There's an error in udtxposdata.json file.
            KeyError: Your props is not valid.

        """

        #  First letter of tag is POS name
        tag = self.data["poses"][props.pop("upos")]

        for key, value in props.items():
            block = self.data["properties"][key]
            tag += block["name"]
            if "props" in block and value in block["props"]:
                tag += block["props"][value]
            else:
                tag += value.lower()

        return tag


class IncorrectTag(Exception):
    pass
