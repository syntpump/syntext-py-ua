"""This class implements language-specific POS tags parsing in MULTEXT-East
Morphosyntactic Specifications, Version 4.
It will use mtexposdata.json file in this directory in order to encode XPOS
tag.
"""

import json


class MTEParser:

    def __init__(self):
        """Open and parse mtexposdata.json file.

        Raises:
            FileNotFoundError: The file mtexposdata.json data is not exists.
            PermissionError: You're not allowed to access to mtexposdata.json
                file.

        """

        try:
            with open("libs/ud/mtexposdata.json") as file:
                self.data = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("File mtexposdata.json was not found!")

    def parse(self, tag: str):
        """Returns features of the given XPOS.

        Args:
            tag (str): XPOS of the token. Example: ' Ncfpnn'

        Returns:
            dict: Parsed tag. Example: {
                'upos': 'Noun',
                'Type': 'Common',
                'Gender': 'Female',
                'Number': 'Plural',
                'Case': 'Nominative',
                'Animacy': 'No'
            }

        Raises:
            TypeError: Something wrong with your tagM.

        """

        feats = dict()

        try:

            block = self.data[tag[0]]
            feats["name"] = block["upos"]

            for i, letter in enumerate(tag[1:]):
                prop = block["attrs"][i]
                if letter == "-":
                    continue
                else:
                    feats[prop] = block[prop][letter]

        except (KeyError, IndexError):
            raise IncorrectTag(
                f"Something wrong with your XPOS: {tag}. Please, check it with"
                " MULTEXT-East Morphosyntactic Specifications, Version 4."
            )

        return feats

    def stringify(self, props):
        """Converts properties to XPOS tag.

        Args:
            props (dict): Properties. Example:
                {   'name': 'Conjunction', 'Type': 'coordinating',
                    'Formation': 'simple'}

        Returns:
            str: XPOS tag to this dict. Example: 'Ccs'

        Raises:
            KeyError: Some of properties in your props absent.
            IndexError: There's error in mtexposdata.json file.

        """

        letter = str()
        tag = str()

        # Iterate data to find letter for UPOS specified in props
        for posname, nested in self.data.items():
            if nested["upos"] == props["name"]:
                # Remember the letter
                letter = posname
                # Add it to the tag
                tag += letter
                break

        if len(tag) == 0:
            raise IncorrectTag(
                "No POS name found for properties you specified."
            )

        for attr in self.data[letter]["attrs"]:
            # Undefined properties must be denoted with a dash
            if attr not in props:
                tag += "-"
                continue
            for value in self.data[letter][attr]:
                if self.data[letter][attr][value] == props[attr]:
                    tag += value
                    break

        # Dashes for undefined properties are not necessary at the end
        return tag.rstrip("-")


class IncorrectTag(Exception):
    pass
