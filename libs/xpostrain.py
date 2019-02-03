"""Contains classes for performing xpos-training.
"""


class MorphologyRecognizeTrainer:
    """Base class for all trainer classes.
    """

    def __init__(self, db, logger=None, staticposes=None, ignoreposes=None):
        """Assign __init__ arguments to class property and create new
        temporary table in db.

        Args:
            db (MongoClient)
            logger (libs.logs.Logger)

        """

        self.db = db
        self.collection = db.createCollection(db.XPOSTRAIN)
        self.logger = logger
        self.staticposes = staticposes
        self.ignoreposes = ignoreposes

    def log(self, msg):
        """Call self.logger.write if self.logger is defined.

        Args:
            msg(str, int): Message to print.

        Return:
            ?: Result of Logger executing.

        """

        if self.logger:
            return self.logger.write(msg)

    def logjson(self, obj):
        """Call self.logger.logjson if self.logger is defined.

        Args:
            obj(*): Any JSON-serializable object.

        Return:
            ?: Result of Logger executing.

        """

        if self.logger:
            return self.logger.logjson(obj)
