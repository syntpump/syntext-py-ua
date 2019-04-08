"""Use this library to get predefined instances of the following classes:
    - DB
    - MorphologyRecognizer
    - ContextualProcessor
    - ConlluReader
"""

import json
from libs.db import DB
from libs.morphology import MorphologyRecognizer
from libs.ctxmorph import ContextualProcessor
from libs.ud.conllu import ConlluReader


class Predefinator:
    """This class contains methods returning predefined objects
    """

    def __init__(self):

        with open('config.json') as configuration_file:
            config = json.load(configuration_file)

        self.db_config = config["DB"]
        self.mr_config = config["MorphologyRecognizer"]
        self.cp_config = config["ContextualProcessor"]
        self.cr_config = config["ConlluReader"]

    def defineDB(self):
        """Returns predefined DB instance
        """

        return DB(self.db_config["host"], self.db_config["dbname"])

    def defineMorphRec(self):
        """Returns predefined MorphologyRecognizer instance
        """

        return MorphologyRecognizer(self.mr_config["collection"], self.mr_config["tagparser"], self.mr_config["priorityList"])

    def defineConProc(self):
        """Returns predefined ContextualProcessor instance
        """

        return ContextualProcessor(self.cp_config["collection"], self.cp_config["applier"], self.cp_config["priority"], self.cp_config["tagparser"], self.cp_config["rulescoll"])

    def defineCollRead(self):
        """Returns predefined ConlluReader instance
        """

        return ConlluReader(self.cr_config["fp"], self.cr_config["ignoreComments"], self.cr_config["strict"])
