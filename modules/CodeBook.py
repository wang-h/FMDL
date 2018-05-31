from collections import Counter
from modules.DataSet import EOS


class CodeBook(Counter):
    def __init__(self, vocab=None, stopwords=None):
        super(CodeBook, self).__init__(vocab)
        self.stopwords = stopwords

    def save(self, save_file):
        for key in self.stopwords:
            if key != (EOS,):
                save_file.write("".join(key) + "\t" + "<\\w>" + "\n")
        for key in self.keys():
            if key != (EOS,):
                save_file.write("".join(key) + "\n")

    def load(self, save_file):
        self.stopwords = set()
        self.stopwords.add((EOS,))
        for line in save_file:
            cols = line.rstrip("\n").split("\t")
            if len(cols) > 1 and cols[-1] == "<\\w>":
                self.stopwords.add((cols[0],))
            else:
                self[tuple(x for x in cols[0])] = 1
