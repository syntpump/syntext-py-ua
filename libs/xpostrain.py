"""Contains classes for performing xpos-training.
"""


class MorphologyRecognizeTrainer:
    """Base class for all trainer classes.
    
    Properties:
        db (libs.DB): Main database
        collection (Collection): Collection where train data will be uploaded.
        logger (libs.Logger)
        staticposes (list): List of static POSes (if supported by this
            recognizer).
        ignoreposes (list): List of POSes to be ignored (if supported by this
            recognizer).
        poses (set, optional): Set of (UPOS, XPOS) tuples of uploaded tokens by
            loadData() method. Is None before first use.

    """

    poses = None


    def __init__(self, db, logger=None, staticposes=None, ignoreposes=None):
        """Assign __init__ arguments to class property and create new
        temporary table in db.

        Args:
            db (libs.DB)
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

    def loadData(self, db, gcreader, limit=0, offset=0):
        """Create temporary table in specified db and load tokens from gcreader
        there.

        Args:
            gb (libs.DB)
            gcreader (*): Any reader from libs.gc
            limit (int): A limit of tokens to process. '0' means infinity.
            offset (int): An offset within GC data of tokens to process.

        Yields:
            dict: {
                "record": {
                    "upos": UPOS of loaded token.
                    "xpos": XPOS of loaded token.
                    "form": Infinitive form of token (if specified in GC).
                },
                "counter" (int): Number of processed line.
            }

        """

        tempcoll = db.createCollection(db.TEMPORARY)

        if limit == 0:
            limit = float("inf")

        counter = 0

        # Collecting (UPOS, XPOS) tuples while iterating.
        self.poses = set()

        while counter < limit:
            line = gcreader.nextLine()
            counter += 1
            if counter < offset:
                continue
            if line["type"] != gcreader.DATALINE:
                continue

            upos = line["data"]["upos"]
            xpos = line["data"]["xpos"]
            self.poses.add((upos, xpos))

            record = {
                "upos": upos,
                "xpos": xpos,
                "form": line["data"]["form"].lower()
            }

            tempcoll.insert(record)

            yield {
                "record": record,
                "counter": counter
            }


class TrainByAffixes(MorphologyRecognizeTrainer):
    """This trainer will recognize similar affixes in words and adds it as
    rules. It'll also create 'static' rules for POSes that have no declension
    property and 'exception' rules for words that are too different from
    others, so no connections can be found.
    """

    def nextXPOS():
        pass
