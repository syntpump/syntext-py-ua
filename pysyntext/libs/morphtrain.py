"""Base class for all TMR classes.
"""


class MorphologyRecognizeTrainer:
    """Base class for all trainer classes.

    Properties:
        db (libs.DB): Main database
        gcreader (?): One of readers defined in libs/ud to read GC data (set by
            loadData method).
        maincoll (Collection): Collection where train data will be uploaded.
        tempcoll (Collection): Collection for temporary/trash data.
        logger (libs.Logger): Initialized Logger.
        staticposes (list): List of static POSes (if supported by this
            recognizer).
        ignoreposes (list): List of POSes to be ignored (if supported by this
            recognizer).
        poses (set, optional): Set of (UPOS, XPOS) tuples of uploaded tokens by
            loadData() method. Is None before first use.
        settings (dict): Dictionary of params that your trainer expect.
        useUDT (bool): Use UDT tags.

    """

    poses = None

    def __init__(
        self, db, settings, logger, staticposes=None, ignoreposes=None,
        testenabled=False
    ):
        """Assign __init__ arguments to class property and create new
        table in db.

        Args:
            db (libs.DB)
            settings (dict): Dictionary of params that your trainer expect.
            logger (libs.logs.Logger)
            staticposes (list): List of static POSes (if supported by this
                recognizer).
            ignoreposes (list): List of POSes to be ignored (if supported by
                this recognizer).
            testenabled (bool): Do not upload any data to main db if True.

        """

        self.db = db
        self.maincoll = db.createCollection(db.XPOSTRAIN)
        self.logger = logger
        self.settings = settings
        self.staticposes = staticposes
        self.ignoreposes = ignoreposes
        self.testenabled = testenabled

        self.logger.write(
            f"Created {self.maincoll.name} as main collection.\n"
        )

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

        self.gcreader = gcreader

        self.tempcoll = db.createCollection(db.TEMPORARY)

        self.logger.write(
            f"Created {self.tempcoll.name} as temp collection.\n"
        )

        if limit == 0:
            limit = float("inf")

        counter = 0

        # Collecting (UPOS, XPOS) tuples while iterating.
        self.poses = set()

        while counter < limit:
            line = gcreader.nextLine()
            if counter < offset:
                offset -= 1
                continue
            else:
                counter += 1
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

            self.tempcoll.insert(record)

            yield {
                "record": record,
                "counter": counter
            }

    def close(self):
        """Delete all temporary collections and close db cursors.
        """

        self.db.drop(self.db.tempcoll.name)
        self.db.close()
