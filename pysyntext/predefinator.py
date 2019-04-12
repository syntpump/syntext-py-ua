"""Use this library to initialize any class defined in config.json.
"""

import json
from importlib import import_module
import os


class Predefinator:
    """This class can initialize classes using configs from config.json in this
    directory.

    Properties:
        config (dict): Configurations.

    """

    def __init__(self, fp):
        """Reads configs from passed fp and remember it.

        Arguments:
            fp (file)

        """

        self.config = json.load(fp)

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

        while path:
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

            # '$'-marked fields are not properties for constructor
            if prop[0] == "$":
                continue

            if not isinstance(value, dict):
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
                elif value["object"] == "fp":
                    initprops[prop] = open(value["address"])
                elif value["object"] == "jsonfp":
                    initprops[prop] = json.load(open(value["address"]))

        # Unpack dictionary with properties and initialize obj, which is class
        return obj(**initprops)
