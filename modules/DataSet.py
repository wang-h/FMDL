import os
import sys
import random
import numpy as np
from tqdm import tqdm
from collections import Counter
from modules.SuffixArray.SuffixArray import IntegerSuffixArray
EOS = "\n"


def tokenizer(line, trie):
    if trie is not None:
        sentence = prefix_based_segment(
            tuple(x for x in list(line)), trie)
    else:
        sentence = [(x,) for x in list(line)]
    return sentence


def prefix_based_segment(sentence, trie):
    l = len(sentence)
    i = 0
    pieces = []
    while i < l:
        j = i + 1
        while j < l and sentence[i:j + 1] in trie and \
                sentence[i:j + 1] not in trie.stopwords:
            j += 1
        pieces.append(tuple(sentence[i:j]))
        i = j
    return pieces


class TrieTree(Counter):
    def __init__(self, codebook):
        super(TrieTree, self).__init__()
        sorted_keys = sorted(list(codebook.items()), key=lambda x: len(x[0]))
        self.stopwords = codebook.stopwords
        for key, val in sorted_keys:
            for i in range(1, len(key)):
                self[key[:i]] += val
            self[key] += val


class DataSet(object):
    def __init__(self, file_name, stoplist_size=30):
        self.file_name = file_name
        self.text = []
        self.trie = None
        self.stopwords = None
        self.sampled = None
        self.num_lines = self.count_lines()
        self.examples = self.head(5)
        self.stoplist_size = stoplist_size
    def __len__(self):
        return self.num_lines

    def __iter__(self):
        with open(self.file_name, "r") as fin:
            for i, line in enumerate(fin):
                if self.sampled is not None:
                    if i in self.sampled:
                        yield tokenizer(line, self.trie)
                else:
                    yield tokenizer(line, self.trie)
    def count_lines(self):
        # the cheapest way to count lines.
        return sum(1 for line in open(self.file_name, "r"))

    def init_sampler(self, n=100000):
        assert self.num_lines > 0
        sample_size = min(self.num_lines, n)
        self.sampled = set(random.sample(range(self.num_lines), sample_size))

    def head(self, k=5):
        sentences = []
        start = 0
        with open(self.file_name, "r") as fin:
            while start < k:
                line = fin.readline()
                sentences.append(
                    line.rstrip("\n"))
                start += 1
        return sentences

    def numericalize(self, w2i, text):
        return [w2i[x] for x in text]

    def build_suffixarray(self, array):
        # print("Building suffixarray", file=sys.stderr)
        self.sa = IntegerSuffixArray(array)

    def build_vocab(self):
        self.vocab = Counter()
        self.init_sampler()
        for sent in tqdm(self, total=0, desc="Building vocabulary"):
            self.vocab.update(sent)
        if not self.stopwords:
            self.stopwords = set(x[0] for x in self.vocab.most_common(self.stoplist_size))

        self.w2i = {w: i for i, w in enumerate(self.vocab.keys())}
        self.text = [(EOS,)] + \
            [x for sent in self for x in sent] + [(EOS,)] * 2
        self.build_suffixarray([self.w2i[x] for x in self.text])
        self.data_len = self.sa.len

    def build_pair_stats(self, min_count=5):
        pair_stats = Counter()
        #def func(x): return x[0] not in (EOS,) and x[1] != (EOS,)

        def func(
            x): return x[0] not in self.stopwords and x[1] not in self.stopwords
        iterator = tqdm(
            filter(func, zip(self.text, self.text[1:])),
            total=0, desc="Building pair statistics")
        pair_stats.update(iterator)
        return Counter({k: v for k, v in pair_stats.items() if v >= min_count})

    def search_indices(self, pair):
        w_1, w_2 = pair
        indices = [self.w2i[w_1], self.w2i[w_2]]
        for j in self.sa.search_index(indices):
            frag = self.text[j - 1:j + 3]
            yield tuple(frag)

    def apply_codebook(self, codebook, resample=True):
        self.trie = TrieTree(codebook)
        if resample:
            self.init_sampler()
            self.build_vocab()

    def show_samples(self, file=sys.stderr):
        print("Sampling segmentation results:", file=file)
        for sent in self.examples:
            print(" ".join("".join(w)
                           for w in tokenizer(sent, self.trie)), file=file)

    def segmented(self):
        for sent in self:
            yield " ".join("".join(w) for w in sent).rstrip("\n")
