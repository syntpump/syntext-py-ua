"""Use this library to get predefined objects of the following classes:
    - DB
    - MorphologyRecognizer
    - ContextualProcessor
    - ConlluReader
"""

import json
from importlib import import_module
import os
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

    def getByPath(self, path):
        """Returns object by its path.

        Properties:
            path (str): Path to object.

        Returns:
            uninitialized class, function

        Raises:
            AttributeError: Given path does not exist.

        """

        path = path.split(".")
        obj = import_module(path.pop(0))

        while len(path) > 0:
            obj = getattr(obj, path.pop(0))

        return obj

    def inited(self, name=None, properties=None, location=None):
        """Returns well-initialized class using configs from self.config.

        Args:
            name (str): Name of class to initialize
            properties (dict): Properties for class to initialize. If not
                passed, then self.config will be used.
            location (str): Location where to look for class. If not passed
                then self.config will be used.

        Returns:
            initialized class

        Raises:
            KeyError: Given class does not exist in config file.

        """

        if not name and not location:
            raise TypeError("Name of class or its location must be given.")

        if name:
            location = self.config[name]["$location"] + "." + name

        obj = self.getByPath(location)
        initprops = {}

        if not properties:
            properties = self.config[name]

        for prop, value in properties.items():

            if prop[0] == "$":
                continue

            if type(value) is not dict:
                initprops[prop] = value
            else:
                if value["object"] == "function":
                    initprops[prop] = self.getByPath(value["name"])
                elif value["object"] == "class":
                    # Default properties from config.json must be used
                    if "props" not in value:
                        initprops[prop] = self.inited(value["name"])
                    # Special properties are defined
                    else:
                        initprops[prop] = self.inited(
                            properties=value["props"],
                            location=value["name"]
                        )
                elif value["object"] == "sysvar":
                    initprops[prop] = os.getenv(value["name"])

        # Unpack dictionary with properties and initialize obj, which is class
        return obj(**initprops)

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
