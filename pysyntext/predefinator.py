"""Use this library to initialize any class defined in config.json.
"""

import json
import os
from importlib import import_module


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

    def getByPath(self, package, classobj=None, function=None):
        """Returns object by its path.

        Properties:
            package (str)
            classobj (str): If defined, returns class from package.
            function (str): If defined, function with given name will be
                returned.

        Returns:
            uninitialized class, function

        Raises:
            AttributeError: Given path does not exist.

        """

        obj = import_module(package)

        if not classobj:
            return obj

        classobj = classobj.split(".")

        while len(classobj) > 0:
            obj = getattr(obj, classobj.pop(0))

        if not function:
            return obj

        function = function.split(".")

        while len(function) > 0:
            obj = getattr(obj, function.pop(0))

        return obj

    def inited(self, name=None, properties=None, location=None, **kwargs):
        """Returns well-initialized class using configs from self.config.

        Args:
            name (str): Name of class to initialize
            properties (dict): Properties for class to initialize. If not
                passed, then self.config will be used.
            location (str): Location where to look for class. If not passed
                then self.config will be used.
            **kwargs: Lambda-functions which will return custom objects.
                (See docs for `lambda` objects).

        Returns:
            initialized class

        Raises:
            KeyError: Given class does not exist in config file.

        """

        if not name and not location:
            raise TypeError("Name of class or its location must be given.")

        if name:
            location = self.config[name]["$location"] + "," + name

        obj = self.getByPath(*location.split(','))
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
                initprops[prop] = self.parseObject(value, **kwargs)

        # Unpack dictionary with properties and initialize obj, which is class
        return obj(**initprops)

    def parseObject(self, obj, **kwargs):
        """Parse dictionary parameters from config.json.

        Arguments:
            obj (dict): Property dictionary as it defined in config.json
            **kwargs: Arguments for "lambda" and "defined" objects

        Returns:
            *: Initialized object

        """

        if obj["object"] == "function":
            return self.getByPath(
                *obj["name"].split(",")
            )

        if obj["object"] == "class":
            if "props" not in obj:
                return self.inited(obj["name"])
            else:
                return self.inited(
                    properties=obj["props"],
                    name=obj["name"]
                )
        if obj["object"] == "sysvar":
            return os.getenv(obj["name"])

        if obj["object"] == "fp":
            if isinstance(obj["address"], dict):
                return open(self.parseObject(obj["address"]))
            else:
                return open(obj["address"])

        if obj["object"] == "jsonfp":
            if isinstance(obj["address"], dict):
                return json.load(
                    open(self.parseObject(obj["address"]))
                )
            else:
                return json.load(
                    open(obj["address"])
                )

        if obj["object"] == "defined":
            return kwargs[obj["name"]]

        if obj["object"] == "lambda":
            # Following execute lambda expression.
            return kwargs[obj["name"]](obj["data"])
