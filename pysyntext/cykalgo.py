"""Contains a class implementing the CYK algorithm.
"""

from pprint import pprint as pp


class CYKProcessingError(Exception):

    def __init__(self, message):
        self.message = message


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
        self.grammar = list()

        # This will download all the rules from DB to this class. Assume, that
        # they have correct structure.
        for rule in collection.find({}):
            rule["prod"] = tuple(rule["prod"])
            self.grammar.append(rule)

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

        wfst = [
            [
                [] for _ in range(numtokens + 1)
            ] for _ in range(numtokens + 1)
        ]

        # Place tagged tokens onto the diagonal
        for i in range(numtokens):
            wfst[i][i + 1].append({"pos": tokens[i]})

        numtokens += 1

        for span in range(2, numtokens):
            for start in range(numtokens - span):
                end = start + span
                for mid in range(start + 1, end):

                    possible_productions = [
                        (
                            a['pos']['PunctType'] if 'PunctType' in a['pos'] else a['pos']['upos'],
                            b['pos']['PunctType'] if 'PunctType' in b['pos'] else b['pos']['upos']
                        ) for a in wfst[start][mid] for b in wfst[mid][end]
                    ]

                    for rule in self.grammar:
                        if rule['prod'] in possible_productions:
                            wfst[start][end].append(
                                {'pos': rule, 'linksTo': [wfst[start][mid], wfst[mid][end]]})

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
                        wfst[i][j][0]['pos']['upos']
                        if wfst[i][j]
                        else '.'),
                    end=''
                )
            print()

    def treefy(self, wfst):

        if len(wfst[0][len(wfst) - 1]) < 1:
            raise CYKProcessingError(
                "The sentence hasn't been processed completely")

        output = []
        buf = []
        buf.append(wfst[0][len(wfst) - 1][0])
        count = 1
        nextCount = 0

        index = 0

        while count > 0:

            node = buf.pop(0)

            if node:
                output.append({'id': index, 'word': node['pos']['word'], 'tag': 'T', 'morph': node['pos']} if 'word' in node['pos'] else {
                              'id': index, 'tag': node['pos']['upos'], 'linksTo': [2 * index + 1, 2 * index + 2]})
                count -= 1
                index += 1

            if node and node['linksTo'][0]:
                buf.append(node['linksTo'][0][0])
                nextCount += 1

            if node and node['linksTo'][1]:
                buf.append(node['linksTo'][1][0])
                nextCount += 1

            if count == 0:
                count = nextCount
                nextCount = 0

        pp(output)
