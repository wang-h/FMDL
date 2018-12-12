#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Hao WANG

"""
FMDL Segmenter:
High-accuracy Unsupervised Subword Segmentation Using Minimum Description Length
Learn a finite vocabulary for encoding/segmentation.
"""
import os
import sys
import math
import warnings
import argparse
from collections import Counter
from modules.DataSet import EOS
from modules.DataSet import DataSet
from modules.Vocab import Vocab
try:
    from tqdm import tqdm
except ImportError:
    warnings.warn("tqdm is not installed.")
    sys.exit()

import logging
logging.basicConfig(
    format='%(asctime)s : %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S', 
    level=logging.INFO)
logger = logging.getLogger("FMDL")



class FMDL(object):
    def __init__(self, dataset, min_count, vocab_size):
        super(FMDL, self).__init__()

        self.min_count = min_count
        self.vocab_size = vocab_size
        self.log_base = 0 
        self.data_len = 0
        self.dataset = dataset
        self.model = Counter()

    def collect_candidates(self, pair_stats, threshold=0.8):
        candidates = []
        common_pair = filter(lambda x: x[1] >= self.min_count,
                             pair_stats.most_common(self.vocab_size // 2))
        for pair, total in common_pair:
            w1, w2 = pair
            logger.debug("Checking {} + {}, occ: {}".format(w1, w2, total))
            cost = self.compute_cost(w1, w2, total)  
            if sum(cost) < 0:
                candidates.append((pair, total, cost))
        ceil = math.ceil(len(candidates) * threshold)
        sorted_candidates = sorted(candidates, key=lambda x: sum(x[-1]))[:ceil]
        return sorted_candidates

    def compute_cost(self, w1, w2, total):
        c1, c2 = self.vocab[w1], self.vocab[w2]
        code_cost = self.compute_code_cost(w1, w2, c1, c2, total) * self.log_base
        data_cost = self.compute_data_cost(
            float(total), float(c1), float(c2), self.data_len)
        return code_cost, data_cost

    def compute_data_cost(self, c1w2, c1, c2, n):
        data_cost = 0.0
        data_cost += c1 * math.log(c1 / n + 1e-7)
        data_cost -= (c1 - c1w2) * \
            math.log((c1 - c1w2) / n + 1e-7) if c1 > c1w2 else 0

        data_cost += c2 * math.log(c2 / n + 1e-7)
        data_cost -= (c2 - c1w2) * \
            math.log((c2 - c1w2) / n + 1e-7) if c2 > c1w2 else 0

        data_cost -= c1w2 * math.log(c1w2 / n + 1e-7)
        data_cost += (n - c1 - c2) * math.log((n - c1w2) / n + 1e-7)
        return data_cost

    def compute_code_cost(self, w1, w2, c1, c2, total):
        code_cost = 0.0
        if total > 0:
            code_cost += len(w1 + w2)
        if total == c1:
            code_cost -= len(w1)
        if total == c2:
            code_cost -= len(w2)
        return -code_cost

    def check_valid(self, pair, total):
        indices = self.dataset.search_indices(pair)
        for (pw, w1, w2, nw) in indices:
            if pw + w1 in self.vocab:
                total -= 1
            elif w2 + nw in self.vocab:
                total -= 1
        return total

    def commit_and_success(self, pair, total, cost):
        w1, w2 = pair
        word = w1 + w2
        total = self.check_valid(pair, total)
        if total < self.min_count:
            logger.info("Ignored: {}, cost={}".format(pair, cost))  
            return False
        self.data_len -= total
        dl = sum(self.compute_cost(w1, w2, total))
        if dl > 0:
            return False
        
        self.vocab[word] += total
        self.vocab[w1] -= total
        self.vocab[w2] -= total
        if self.vocab[w1] < 1:
            del self.vocab[w1]
        if self.vocab[w2] < 1:
            del self.vocab[w2]
        self.model[word] = dl
        return True

    def update_vocab(self, candidates):
        updated = 0
        init_vocab_size = len(self.vocab)
        for candidate in tqdm(candidates, ncols=0, 
                 desc="Committing to vocab", total=len(candidates)):
            if len(self.vocab) > self.vocab_size:
                logger.info("")
                logger.info("Vocabulary size: {} -> {}".\
                    format(init_vocab_size, len(self.vocab)))
                return False
            pair, total, cost = candidate
            if self.commit_and_success(pair, total, cost):
                    updated += 1  
            else:
                logger.debug("Discard {}, with cost={}".format(pair, cost))  
        logger.info("Vocabulary size: {} -> {}".\
            format(init_vocab_size, len(self.vocab)))
        return True

    def save_model(self, model):
        for k, v in self.model.items():
            model.write("".join(k)  + "\t" + str(v) + "\n")

    def train(self, iterations, verbose):
        self.dataset.build_vocab()
        self.log_base = -math.log(len(self.dataset.vocab))
        
        for epoch in range(iterations):
            logger.info("-"* 30 + " Epoch: [{}] ".format(epoch) + "-"* 30)
            if verbose:
                self.dataset.show_samples()
            self.vocab = Vocab(self.dataset.vocab, self.dataset.stopwords)
            self.data_len = self.dataset.data_len
            # pair stats
            pair_stats = self.dataset.build_pair_stats()
            # collecting candidates
            candidates = self.collect_candidates(pair_stats)
            # iterative procedure
            if not self.update_vocab(candidates):
                break
            # apply vocab to encode data
            self.dataset.apply_model(self.model)
            

        return self.vocab


def main(args):
    dataset = DataSet(sample = 100000)
    mdl = FMDL(dataset, args.min_count, args.vocab_size)
    trainer = mdl.train
    dataset.read(args.train)
    vocab = trainer(args.iterations, args.verbose)
    mdl.save_model(args.model)
    if args.verbose:
        dataset.show_samples()
    vocab.save(args.vocab)


def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="learning FMDL-based word segmentation")
    parser.add_argument(
        '--train', '-t', type=str, required=True,
        metavar='PATH',
        help="Input unsegmented text for training (default: standard input).")
    parser.add_argument(
        '--output', '-o', type=argparse.FileType('w'), default=None,
        metavar='PATH',
        help="Output segmented (default: standard output)")
    parser.add_argument(
        '--vocab', '-c', type=argparse.FileType('w'), default="vocab",
        metavar='FILE',
        help="Output file for vocab")
    parser.add_argument(
        '--iterations', '-i', type=int, default=3,
        help="# of iterations for FMDL learning (default: %(default)s).")
    parser.add_argument(
        '--min_count', type=int, default=1,
        help="ignore the new words with a frequency lower than this. (default: %(default)s).")
    parser.add_argument(
        '--vocab_size', type=int, default=20000,
        help="vocabulary size of vocab. (default: %(default)s).")
    parser.add_argument(
        '--model', '-m', type=argparse.FileType('w'), default="model",
        metavar='FILE',
        help="Output file for model")
    parser.add_argument(
        '--verbose', '-v', action="store_true",
        help="verbose mode, print the details.")

    return parser


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    main(args)
