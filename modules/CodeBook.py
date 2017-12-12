import sys
from math import log2
from collections import Counter

class CodeBook(Counter):
    def __init__(self, splitter="\t", data=None, file=None, *args, **kwargs):
        super(CodeBook, self).__init__(*args, **kwargs)
        self.splitter = splitter
        self.len = len(self)
        self.changed = dict()
        if data:
            self.create_from_data(data)
        if file:
            self.load(file)

    def create_from_data(self, data):
        for i, sentence in enumerate(data.__iter__(format="list")):
            for w in sentence:
                self[w] += 1
        self.len = len(self)

    def write(self, file=sys.stdout):
        for key, value in self.items():
            file.write("{}\t{}\n".format(key, value))

    def load(self, file=None):
        if file:
            for line in file:
                key, value = line.rstrip("\n").split(self.splitter)
                self[key]= int(value)
            self.len = len(self)

    @property
    def coding_cost(self):
        return sum(len(x) for x in self.keys())

    @property    
    def data_length(self):
        return sum(x for x in self.values())

    @property    
    def mdl_score(self):
        n = self.data_length
        mdl = sum(x*(log2(x/n)) for x in self.values() if x > 0)
        return self.coding_cost - mdl

    def __repr(self):
        return "Codebook{%d}"%self.len

