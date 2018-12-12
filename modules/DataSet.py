import os
import sys
import random
import numpy as np
from tqdm import tqdm
from copy import deepcopy
from collections import Counter
from modules.SuffixArray.SuffixArray import IntegerSuffixArray
EOS = "\n"


# def tokenizer(line, trie):
#     if trie is not None:
#         sentence = fmm(tuple(x for x in list(line)), trie)
#     else:
#         sentence = [(x,) for x in list(line)]
#     return sentence


# def fmm(sentence, trie):
#     l = len(sentence)
#     i = 0
#     pieces = []
#     while i < l:
#         j = i + 1
#         while j < l and sentence[i:j + 1] in trie and \
#                 sentence[i:j + 1] not in trie.stopwords:
#             j += 1
#         pieces.append(tuple(sentence[i:j]))
#         i = j
#     return pieces

def tokenizer(sent):
    return [(x,) for x in list(sent.rstrip("\n"))]


    # if model is not None:
    #     sentence = binary_merge(sent, model)
    # else:
    #     sentence = [(x,) for x in list(sent)]

def recursive_binary_merge(sent, model):
    merge = True
    while merge:
        sent, merge = binary_merge(sent, model)
    return sent

def binary_merge(sent, model):
    l = len(sent)
    i = 0
    pieces = []
    merge = False
    while i < l:
        if i < l-1 and sent[i] + sent[i + 1] in model:
            merge = True
            pieces.append(sent[i] + sent[i + 1])
            i += 2
        else:
            pieces.append(sent[i])
            i += 1
    return pieces, merge

# def reverse_binary_merge(sent, model):
#     l = len(sent)
#     i = l
#     pieces = []
#     merge = False
#     while i > 0:
#         if i > 0 and sent[i-1] + sent[i] in model:
#             merge = True
#             pieces.append(sent[i-1] + sent[i])
#             i -= 2
#         else:
#             pieces.append(sent[i])
#             i -= 1
#     return reversed(pieces), merge

class TrieTree(Counter):
    def __init__(self, vocab):
        super(TrieTree, self).__init__()
        sorted_keys = sorted(list(vocab.items()), key=lambda x: len(x[0]))
        self.stopwords = vocab.stopwords
        for key, val in sorted_keys:
            for i in range(1, len(key)):
                self[key[:i]] += val
            self[key] += val


class DataSet(list):
    def __init__(self, *arg, sample = -1, stoplist_size=20, **kwargs):
        self.path = None
        self.text = []
        self.trie = None
        self.stopwords = None
        self.sample = sample
        self.stoplist_size = stoplist_size
        super(DataSet, self).__init__(*arg, **kwargs)
        self.examples = self[:5]

    def read(self, path):
        self.path = path
        print(self.path)
        with open(self.path, "r") as fin:
            for i, line in enumerate(fin):
                if self.sample > -1:
                    if i < self.sample:
                        self.append(tokenizer(line))
    def numericalize(self, w2i, text):
        return [w2i[x] for x in text]

    def build_suffixarray(self, array):
        # print("Building suffixarray", file=sys.stderr)
        self.sa = IntegerSuffixArray(array)

    def build_vocab(self):
        self.vocab = Counter()
        for sent in tqdm(self, total=0, desc="Building vocabulary"):
            self.vocab.update(sent)
        self.vocab[(EOS,)] = 1
        if not self.stopwords:
            self.stopwords = set(
                x[0] for x in self.vocab.most_common(self.stoplist_size))

        self.w2i = {w: i for i, w in enumerate(self.vocab.keys())}
        self.text = [(EOS,)] + \
            [x for sent in self for x in sent] + [(EOS,)] * 2
        self.build_suffixarray([self.w2i[x] for x in self.text])
        self.data_len = self.sa.len

    def build_pair_stats(self, min_count=5):
        pair_stats = Counter()
        #def func(x): return x[0] not in (EOS,) and x[1] != (EOS,)

        def func(x): 
            return x[0] not in self.stopwords and x[1] not in self.stopwords
        iterator = tqdm(filter(func, zip(self.text, self.text[1:])),
            total=0, desc="Building pair statistics")
        pair_stats.update(iterator)
        return Counter({k: v for k, v in pair_stats.items() if v >= min_count})

    def search_indices(self, pair):
        w_1, w_2 = pair
        indices = [self.w2i[w_1], self.w2i[w_2]]
        for j in self.sa.search_index(indices):
            frag = self.text[j - 1:j + 3]
            yield tuple(frag)

    def apply_model(self, model):
        for i, sent in enumerate(self):
                self[i], _ = binary_merge(sent, model)
        self.examples = self[:5]
        self.build_vocab()
    
    
    def segment(self, model, path):
        self.path = path
        with open(self.path, "r") as fin:
            for i, sent in enumerate(fin):
                sent = recursive_binary_merge(sent.rstrip("\n"), model)
                yield " ".join("".join(w) for w in sent) 

    def show_samples(self, file=sys.stderr):
        print("Sampling segments:", file=file)
        for sent in self.examples:
            print(" ".join("".join(w) for w in sent), file=file)
