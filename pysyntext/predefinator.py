"""Use this library to get predefined objects of the following classes:
    - DB
    - MorphologyRecognizer
    - ContextualProcessor
    - ConlluReader
"""

import json
from importlib import import_module
import pymongo
from libs.db import DB
from libs.morphology import MorphologyRecognizer
from libs.ctxmorph import ContextualProcessor
from libs.ud.conllu import ConlluReader


class Predefinator:
    """This class can initialize classes using configs from config.json in this
    directory.

    Properties:
        config (dict): Configurations.

    """

    def __init__(self):

        with open('config.json') as fp:
            self.config = json.load(fp)

        db_config = config["DB"]
        mr_config = config["MorphologyRecognizer"]
        cp_config = config["ContextualProcessor"]
        cr_config = config["ConlluReader"]

    def getClass(self, path):
        """Return class by its path.

        Properties:
            path (str): Path to class.

        Returns:
            uninitialized class

        Throws:
            AttributeError: Given path does not exist.

        """

        path = path.split(".")
        obj = import_module(path.pop(0))

        while len(path) > 0:
            obj = getattr(obj, path.pop(0))

        return obj

    def defineDB(self):
        """Returns predefined DB object
        """

        return DB(db_config["host"], db_config["dbname"])

    def defineMorphRec(self):
        """Returns predefined MorphologyRecognizer object
        """

        return MorphologyRecognizer(mr_config["collection"], mr_config["tagparser"], mr_config["priorityList"])

    def defineConProc(self):
        """Returns predefined ContextualProcessor object
        """

        return ContextualProcessor(cp_config["collection"], cp_config["applier"], cp_config["priority"], cp_config["tagparser"], cp_config["rulescoll"])

    def defineCollRead(self):
        """Returns predefined ConlluReader object
        """

        return ConlluReader(cr_config["fp"], cr_config["ignoreComments"], cr_config["strict"])
