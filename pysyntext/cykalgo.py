"""Contains a class which implements the CYK algorithm.
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
        self.grammar = list()

        for rule in collection.find({}):
            rule["prod"] = tuple(rule["prod"])
            self.grammar.append(rule)

    def wfst(self, sentence):
        """Create and complete a Well-Formed Substring Table
        (2-dimensional list of used by the algorithm).

        Args:
            sentence (str)

        Returns:
            list: Completed WFST.

        Raises:
            NotTaggedException: There are untagged words in the input.

        """

        def getFeature(token):
            return (
                token["PunctType"]
                if "PunctType" in token
                else token["upos"]
            )

        def isAppliable(rule):
            return rule["prod"] == (
                getFeature(left["pos"]),
                getFeature(right["pos"])
            )

        tokens = self.ctx.tagged(sentence)
        size = len(tokens)

        wfst = [
            [
                [] for _ in range(size + 1)
            ] for _ in range(size + 1)
        ]

        for i, token in enumerate(tokens):

            if "upos" not in token:
                raise NotTaggedException(
                    "Some of the words in the input are not tagged.")

            wfst[i][i + 1].append({
                "pos": token,
                "children": [None] * 2
            })

        size += 1

        for span in range(2, size):
            for start in range(size - span):
                end = start + span
                for mid in range(start + 1, end):

                    for left, right in zip(wfst[start][mid], wfst[mid][end]):

                        for rule in filter(isAppliable, self.grammar):
                            wfst[start][end].append({
                                'pos': rule,
                                'children': [left, right]
                            })

        return wfst

    def display(self, wfst):
        """Print the given WFST.

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
        """Get the syntax tree from completed WFST

        Args:
            wfst (list)

        Returns:
            list: Syntax tree of the sentence in WFST.

        Raises:
            NotTaggedException: Given WFST is not fully completed.

        """

        if len(wfst[0][len(wfst) - 1]) < 1:
            raise ProcessingException(
                "CYK was unable to create grammar tree of the given rules and "
                "tokens.")

        tree = []
        buf = [wfst[0][len(wfst) - 1][0]]

        count = 1
        nextCount = 0

        index = 0
        link_index = 0

        while count > 0:

            node = buf.pop(0)

            if node:
                if 'word' in node['pos']:
                    tree.append({'id': index,
                                 'word': node['pos']['word'],
                                 'tag': 'T',
                                 'morph': node['pos']})

                else:
                    tree.append({'id': index,
                                 'tag': node['pos']['upos'],
                                 'linksTo': [2 * link_index + 1,
                                             2 * link_index + 2]})
                    link_index += 1

                count -= 1
                index += 1

                for i in [0, 1]:
                    if node['children'][i]:
                        buf.append(node['children'][i])
                        nextCount += 1

            if count == 0:
                count = nextCount
                nextCount = 0

        return tree

    def getGrammar(self, sentence):
        """Return the syntactic tree of the sentence.

        Args:
            sentence (str)

        Returns:
            list: Result. The following format will be used:
                [
                    {
                        "id": int,
                        "word": str,
                        "tag": str, ("T" for terminal)
                        "morph": [...list of morphological properties
                                  of the word]
                        "linksTo": [...list of the ids of produced elements,
                                    if not terminal.]
                    }
                ]

        """

        return self.treefy(
            self.wfst(sentence))


class NotTaggedException(Exception):
    pass


class ProcessingException(Exception):
    pass
