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
            wfst[i][i + 1].append({'pos': tokens[i], 'children': [None, None]})

        numtokens += 1

        for span in range(2, numtokens):
            for start in range(numtokens - span):
                end = start + span
                for mid in range(start + 1, end):

                    for left in range(len(wfst[start][mid])):
                        for right in range(len(wfst[mid][end])):
                            for rule in self.grammar:
                                if rule['prod'] == (wfst[start][mid][left]['pos']['PunctType'] if 'PunctType' in wfst[start][mid][left]['pos'] else wfst[start][mid][left]['pos']['upos'], wfst[mid][end][right]['pos']['PunctType'] if 'PunctType' in wfst[mid][end][right]['pos'] else wfst[mid][end][right]['pos']['upos']):
                                    wfst[start][end].append({'pos': rule, 'children': [wfst[start][mid][left], wfst[mid][end][right]]})

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

            if node and node['children'][0]:
                buf.append(node['children'][0])
                nextCount += 1

            if node and node['children'][1]:
                buf.append(node['children'][1])
                nextCount += 1

            if count == 0:
                count = nextCount
                nextCount = 0

        pp(output)
