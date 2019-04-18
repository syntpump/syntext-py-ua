"""Contains a class implementing the CYK algorithm.
"""


class CYKAnalyzer:
    """Class that uses CYK algorithm to parse sentences with the help of
    context-free grammar.
    """

    def __init__(self, ctx):
        """Init the CYKAnalyzer, upload the rules from db to self.grammar.

        Arguments:
            ctx (ContextualProcessor): Initialized class.

        """
        self.ctx = ctx

        # Should download the grammar from db in the future.
        self.grammar = [

            {'upos': 'NP', 'prod': ('ADJ', 'NOUN')},

            {'upos': 'VP', 'prod': ('VERB', 'PRON')},
            {'upos': 'VP', 'prod': ('VERB', 'NOUN')},

            {'upos': 'S', 'prod': ('NOUN', 'VERB')},
            {'upos': 'S', 'prod': ('NP', 'VERB')},
            {'upos': 'S', 'prod': ('NOUN', 'VP')},
            {'upos': 'S', 'prod': ('NP', 'VP')},

            # more to come

        ]

    def wfst_of(self, sentence):
        """Create a Well-Formed Substring Table (2-dimensional list of
        dictionaries and chars used by the algorithm) with the tagged words
        from the given sentence on the main diagonal.

        Args:
            sentence (str)

        Returns:
            list: WFST with the tagged words from the
                given sentence on the main diagonal.

        """

        tokens = self.ctx.tagged(sentence)
        numtokens = len(tokens)

        wfst = [[None for i in range(numtokens + 1)]
                for j in range(numtokens + 1)]

        for i in range(numtokens):
            wfst[i][i + 1] = tokens[i]
        return wfst

    def display(self, wfst):
        """Print the given WFST

        Args:
            wfst (list)

        """

        print ('\nWFST ' + ' '.join([("%-4d" % i)
                                     for i in range(1, len(wfst))]))
        for i in range(len(wfst) - 1):
            print ("%d    " % i, end='')
            for j in range(1, len(wfst)):
                print ("%-5s" %
                       (wfst[i][j]['upos'] if wfst[i][j] else '.'), end='')
            print ()

    def completed(self, wfst):
        """Complete the given WFST using grammar

        Args:
            wfst (list)

        Returns:
            list: Completed WFST

        """

        numtokens = len(wfst)

        for span in range(2, numtokens):
            for start in range(numtokens - span):
                end = start + span
                for mid in range(start + 1, end):
                    nt1, nt2 = wfst[start][mid]['upos'] if wfst[start][mid] else None,wfst[mid][end]['upos'] if wfst[mid][end] else None
                    for production in self.grammar:
                        if nt1 and nt2 and (nt1, nt2) == production['prod']:
                            wfst[start][end] = production
        return wfst
