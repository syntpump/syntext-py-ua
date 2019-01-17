from pymongo import MongoClient
import os
import time


class DB:
    """Represents connection to DB and methods to deal with it.

    Properties:
        cli (MongoClient): Database connection, provided by 'pymongo' library.
        dbname (str): Name of database all methods will connect with.
        XPOSTRAIN = 0 (const int): Marker for tables with xpos training data.
        XPOSTRAIN_KEEP = 1 (const int): Marker for tables with xpos training
            data which makes accuracy worse, but it's better to keep for some
            time and maybe makes it better in future.
        EMENDPOS = 10 (const int): Marker for tables with emendpos training
            data.
        EMENDPOS_KEEP = 11 (const int): Like XPOSTRAIN_KEEP marker.
        SYNTEXTRACT = 20 (const int): Marker for tables with syntextract
            training data.
        SYNTEXTRACT_KEEP = 21 (const int): Like XPOSTRAIN_KEEP marker.

    """

    # These constants will be used in order to mark collections
    XPOSTRAIN = 0
    XPOSTRAIN_KEEP = 1
    EMENDPOS = 10
    EMENDPOS_KEEP = 11
    SYNTEXTRACT = 20
    SYNTEXTRACT_KEEP = 21

    def __init__(self, host='atlas', dbname='syntextua'):
        """Return MongoClient() connected to 'localhost' or 'atlas'. You must
        provide %SYNTEXTDBLOG%, %SYNTEXTDBPWD% and %SYNTEXTDBHOST% environment
        variables to make it work.

        Args:
            host (str): If 'localhost' then connect to your local database; if
                'atlas' then connect to MongoDB Atlas.
            dbname (str): Name of database to use.

        Returns:
            MongoClient: Connection to database provided by pymongo lib.

        Raises:
            EnvironmentError: Some of environment variables, which contains
                credentials, are missing, so that connection is impossible.
            RuntimeError: No database with the given name exists.
            ...Errors from pymongo.errors

        """

        if host == 'atlas':
            login = os.getenv('SYNTEXTDBLOG')
            password = os.getenv('SYNTEXTDBPWD')
            hosturl = os.getenv('SYNTEXTDBHOST')

            if not login or not password or not hosturl:
                raise EnvironmentError(
                    'No credentials found. Make sure that SYNTEXTDBLOG, '
                    'SYNTEXTDBPWD and SYNTEXTDBHOST environment variables ',
                    'is provided.'
                )

            url = 'mongodb+srv://%s:%s@%s' % (
                login,
                password,
                hosturl,
            )
            self.cli = MongoClient(url)
        else:
            self.cli = MongoClient()

        if dbname not in self.cli.list_database_names():
            raise RuntimeError(
                f"No database with name '{dbname}' exists on host you're "
                f"trying to connect. "
            )

        self.cli = self.cli.get_database(dbname)
        self.dbname = dbname

    def insert(self, collection, doc):
        """Insert document to collection using credentials provided in this
        class.

        Args:
            collection (str): Name of collection to add document in.
            doc (dict): Document to upload.

        Returns:
            str: ID of inserted document.

        """

        inserted = self.cli.get_collection(collection).insert_one(doc)

        return str(inserted.inserted_id)

    def selectRe(self, collection, field, re):
        """Look for all documents in 'collection' which 'field' has the given
        regexp.

        Args:
            collection (str): Name of collection to look for document in.
            field (str): Field to search regex in.
            re (str): Regexp for searching.

        Returns:
            list: List of found documents.

        """

        docs = self.cli.get_collection(collection).find({
            '$or': [
                {
                    field: {
                        '$regex': re
                    }
                }
            ]
        })

        return list(docs)

    def selectExact(self, collection, field, string):
        """Look for all documents in 'collection' which 'field' has the same
        value as the given 'string'.

        Args:
            collection (str): Name of collection to look for document in.
            field (str): Field to search regex in.
            string (str): Value for searching.

        Returns:
            list: List of found documents.

        """

        docs = self.cli.get_collection(collection).find({
            field: {
                '$in': [string]
            }
        })

        return list(docs)

    def createCollection(self, marker, description=""):
        """Create new collection in DB and generate a unique name for it, using
        tamestamp and marker you gave. This will also write info about your
        collection to 'datainfo' collection.

        Args:
            marker (int): Marker of the type of the collection you want to
                create.
            description (str): Add some description to created collection.

        Returns:
            Collection: Created collection. An instance of pymongo.

        """

        def unique():
            """ Generates next unique name
            """

            return f'temp_{marker}_{time.time()}'

        # Trying to find unique name for collection. Request all existing names
        names = self.cli.collection_names()
        # Create new name until it'll be unique
        name = None
        while True:
            name = unique()
            if name not in names:
                break

        self.cli.get_collection("datainfo").insert_one({
            "name": name,
            "created": time.time(),
            "description": description
        })

        coll = self.cli.get_collection(name)

        # Paste empty document in order to create collection
        coll.insert_one({})

        return coll

    def getTemps(self):
        """Get names of all temporary collections.

        Return:
            list: List of found collections.

        """

        # Just filter collection names by first 5 symbols
        return list(filter(
            lambda name: name[0:5] == 'temp_',
            self.cli.collection_names()
        ))

    def drop(self, name):
        """Drop collection with the given name and delete it from "datainfo"
        collection.

        Args:
            name (str): Name of collection you're want to delete.

        """

        self.cli.get_collection(name).drop()
        self.cli.get_collection("datainfo").find_one_and_delete({
            "name": name
        })

    def compareCollections(
        self, first, second, field, compareFunc, findUnique2=True
    ):
        """Call compareFunc on each pair "document from first collection"-
        "document from second collection", which field has the same value, and
        add the result of execution to a list.
        Returns that list, unique elements from first and second collections.

        Scheme of calling compareFunc():
            collection3.append(
                compareFunc(dict document1, dict document2)
            )

        Args:
            first (str): Name of first collection.
            second (str): Name of second collection.
            field (str): Name of the field to be compared.
            compareFunc (function): Comparing function that will be executed.
            findUnique2(bool): Set this to False in order to prevent searching
                unique documents from second collection.

        Returns:
            dict: Result of comparing.

        Example of return:
            {
                "third": [
                    ...Results of comparing function.
                ],
                "unique1": [
                    ...Unique elements from first collection.
                ],
                "unique2": [ (if findUnique2 == True)
                    ...Unique elements from second collection
                ]
            }

        """

        # Get collections instead of names
        first = self.cli.get_collection(first)
        second = self.cli.get_collection(second)

        cursor = first.find()
        # The first document in collection is always empty (see, why in
        # createCollection() function).
        cursor.skip(1)

        # ID of documents in second collection which is equal to documents in
        # first collection (regulate by comparing function) will be written to
        # list in order to find unique documents in second collection in the
        # future (if findUnique2 == True).
        commonIDs = []
        collection3 = []
        unique1 = []

        # Iterate over cursor
        for document in cursor:
            match = second.find_one({
                field: document[field]
            })
            # If match was not found, then it's a unique element in first
            # collection.
            if not match:
                unique1.append(document)
            # Else append to common.
            else:
                collection3.append(
                    compareFunc(document, match)
                )
                if findUnique2:
                    commonIDs.append(str(match["_id"]))

        if not findUnique2:
            return {
                "third": collection3,
                "unique1": unique1
            }

        # This code won't be executed when findUnique2 == False.
        unique2 = []

        # Do the same iterating for documents in second collection
        cursor = second.find()
        cursor.skip(1)

        for document in cursor:
            # Skip non-unique elements
            if str(document["_id"]) in commonIDs:
                continue
            unique2.append(document)

        return {
            "third": collection3,
            "unique1": unique1,
            "unique2": unique2
        }

    def close(self):
        """Cleanup client resources and disconnect from MongoDB.
        """

        self.cli.client.close()
