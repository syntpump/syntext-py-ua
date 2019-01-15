import pymongo
import os


class DB:
    """Represents connection to DB and methods to deal with it.

    Properties:
        cli (MongoClient): Database connection, provided by 'pymongo' library.
        dbname (str): Name of database all methods will connect with.

    """

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

        """

        if host == 'atlas':
            login = os.getenv('SYNTEXTDBLOG')
            password = os.getenv('SYNTEXTDBPWD')
            hosturl = os.getenv('SYNTEXTDBHOST')

            if not login or not password or not hosturl:
                raise RuntimeError(
                    'No credentials found. Make sure that SYNTEXTDBLOG, '
                    'SYNTEXTDBPWD and SYNTEXTDBHOST environment variables ',
                    'is provided.'
                )

            url = 'mongodb+srv://%s:%s@%s' % (
                login,
                password,
                hosturl,
            )
            self.cli = pymongo.MongoClient(url)
        else:
            self.cli = pymongo.MongoClient()

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

        inserted = self.cli[self.dbname][collection].insert_one(doc)

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

        docs = self.cli[self.dbname][collection].find({
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

        docs = self.cli(self.dbname)[collection].find({
            field: {
                '$in': [string]
            }
        })

        return list(docs)
