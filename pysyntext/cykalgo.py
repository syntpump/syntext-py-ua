"""Contains a class implementing the CYK algorithm.
"""


class CYKAnalyzer:
    """Class that uses CYK algorithm to parse sentences with the help of
    context-free grammar.
    """

    def __init__(self, ctx, collection):
        """Init the CYKAnalyzer, upload the rules from db to self.grammar.

        Args:
            ctx (ContextualProcessor): Initialized class.
            collection (pymongo.Collection): MongoDB collection which store
                grammar rules.

        """
        self.ctx = ctx

        # This will download all the rules from DB to this class. Assume, that
        # they have correct structure.
        self.grammar = [doc for doc in collection.find({})]

        for rule in self.grammar:
            rule['prod'] = tuple(rule['prod'])

    def wfst_of(self, sentence):
        """Create and complete a Well-Formed Substring Table (2-dimensional list of
        dictionaries and chars used by the algorithm).

        Args:
            sentence (str)

        Returns:
            list: Completed WFST.

        """

        tokens = self.ctx.tagged(sentence)
        numtokens = len(tokens)

        wfst = [[[] for i in range(numtokens + 1)]
                for j in range(numtokens + 1)]

        for i in range(numtokens):
            wfst[i][i + 1].append(tokens[i])

        numtokens += 1

        for span in range(2, numtokens):
            for start in range(numtokens - span):
                end = start + span
                for mid in range(start + 1, end):

                    possible_productions = [
                        (
                            a['PunctType'] if 'PunctType' in a else a['upos'],
                            b['PunctType'] if 'PunctType' in b else b['upos']
                        ) for a in wfst[start][mid] for b in wfst[mid][end]
                    ]

                    for rule in self.grammar:
                        if rule['prod'] in possible_productions:
                            wfst[start][end].append(rule)

        return wfst

    def display(self, wfst):
        """Print the given WFST

        Args:
            wfst (list)

        """

        print('\nWFST ' + ' '.join(
            [("%-4d" % i)
             for i
             in range(1, len(wfst))])
        )
        for i in range(len(wfst) - 1):
            print("%d    " % i, end='')
            for j in range(1, len(wfst)):
                print(
                    "%-5s" % (
                        wfst[i][j][0]['upos']
                        if wfst[i][j]
                        else '.'),
                    end=''
                )
            print()

