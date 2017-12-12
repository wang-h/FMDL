#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Hao WANG

"""
FMDL Segmenter:
Unsupervised Segmentation using Minimum Description Length
Learn a size-fixed codebook for encoding/segmentation.
"""
import sys
import os
import argparse
import warnings
from math import log2
from math import floor
from collections import Counter

from modules import Data
from modules import CodeBook
from modules import SuffixArray
from apply_codebook import apply_codebook
import time

try:
    from tqdm import tqdm
except ImportError:
    warnings.warn("tqdm not installed.")


def compute_model_length_change(w1, w2, Cw1w2, Cw1, Cw2, codebook):
    delta = len(w1 + w2) if w1 + w2 not in codebook else 0
    if Cw1w2 == Cw1:
        delta -= len(w1)
    if Cw1w2 == Cw2:
        delta -= len(w2)
    return delta


def compute_mdl_cost(bigram, codebook, pair_stats, n):
    """ n: data length
        ml: model length changes
        mdl: data length given the model changes
    """

    cost = 0.0
    w1, w2 = bigram
    cw1, cw2 = codebook[w1], codebook[w2]
    cw1w2 = pair_stats[(w1, w2)]
    assert cw1w2 > 0
    ml = compute_model_length_change(w1, w2, cw1w2, cw1, cw2, codebook)
    cost += ml
    mdl0 = (cw1 + cw2) * log2(n) - cw1 * log2(cw1) - cw2 * log2(cw2)
    new_cw1 = cw1 - cw1w2
    new_cw2 = cw2 - cw1w2
    mdl1 = - cw1w2 * log2(cw1w2)
    if new_cw1 != 0:
        mdl1 -= new_cw1 * log2(new_cw1)
    if new_cw2 != 0:
        mdl1 -= new_cw2 * log2(new_cw2)

    mdl1 += (cw1 + cw2 - cw1w2) * log2(n - cw1w2)
    cost += mdl1 - mdl0
    return cost


def get_pair_stats(data):
    pair_stats = Counter()
    for words in data.__iter__(format="list"):
        for w1, w2 in zip(words, words[1:]):
            pair_stats[(w1, w2)] += 1
    return pair_stats


def commit(bigram, pair_stats, codebook, sa, min_count):
    w1, w2 = bigram
    indices = sa[" ".join(bigram)]
    cw1w2 = pair_stats[bigram]
    if cw1w2 < min_count:
        return
    for i in indices:
        pw = sa.text[i - 1]
        sw = sa.text[i + 2]
        if (pw, w1) in pair_stats:
            pair_stats[(pw, w1)] -= 1
        if (w2, sw) in pair_stats:
            pair_stats[(w2, sw)] -= 1

    codebook[w1 + w2] += cw1w2
    codebook[w1] -= cw1w2
    codebook[w2] -= cw1w2
    if codebook[w1] < 0 or codebook[w1] < 0 or codebook[w1 + w2] < 0:
        print(codebook[w1], codebook[w1], codebook[w1 + w2], w1, w2, w1 + w2)
    if codebook[w1] == 0:
        del codebook[w1]
    if codebook[w2] == 0:
        del codebook[w2]
    del pair_stats[bigram]


def collect_candidates(pair_stats, codebook, min_count, data_length, ratio=0.8):
    candidates = []
    queue = sorted(pair_stats.items(), key=lambda x: x[1], reverse=False)
    while queue:
        pair = queue.pop()
        bigram, cw1w2 = pair
        if cw1w2 < min_count:
            continue
        cost = compute_mdl_cost(
            bigram, codebook, pair_stats, data_length)
        if cost <= 0:
            candidates.append((bigram, cost))
    sorted_candidates = sorted(
        candidates, key=lambda x: x[-1])

    threshold = floor(len(sorted_candidates) * ratio)
    return sorted_candidates[:threshold]


def print_ref_mdl_score(reffile):
    ref = Data(segmented=True, file=reffile)
    ref_codebook = CodeBook()
    ref_codebook.create_from_data(data=ref)
    if args.verbose:
        print("# Reference, MDL:{}, vocab size:{}".format(
            "{0:.2f}".format(ref_codebook.mdl_score), len(ref_codebook)), file=sys.stderr)


def learn_mdl(data, iterations, min_count, max_num, explicit):
    i = 1
    while i <= iterations:
        codebook = CodeBook()
        codebook.create_from_data(data=data)
        sa = SuffixArray(data.rawtext, unit="word")
        data_length = int(codebook.data_length)
        if args.verbose:
            print("# Iteration[{}], MDL:{}, vocab size:{}".format(
                i, "{0:.2f}".format(codebook.mdl_score), len(codebook)), file=sys.stderr)

        # pair_statistics
        pair_stats = get_pair_stats(data)

        # collecting candidates
        candidates = collect_candidates(
            pair_stats, codebook, min_count, data_length)
        if not candidates:
            if args.verbose:
                print("# Finished, no valid updates.", file=sys.stderr)
            break

        # iterative procedure
        iterator = candidates
        if args.verbose:
            iterator = tqdm(candidates,
                            desc="# Updating codebook", ncols=100,
                            ascii=False, total=len(candidates))

        for bigram, _ in iterator:
            if len(codebook) > max_num:
                break
            if pair_stats[bigram] >= min_count:
                if not explicit:
                    # approximate mode
                    commit(bigram, pair_stats, codebook, sa, min_count)
                else:
                    # explicit mode
                    delta_mdl = compute_mdl_cost(
                        bigram, codebook, pair_stats, codebook.data_length)
                    if delta_mdl <= 0:
                        commit(bigram, pair_stats, codebook, sa, min_count)

        # apply codebook to segmentation
        apply_codebook(data, codebook, min_count)
        data.segmented = True
        #
        i += 1
    return codebook


def main(args):
    if args.ref:
        print_ref_mdl_score(args.ref)

    data = Data(segmented=False, file=args.train)
    codebook = learn_mdl(data, args.iterations,
                         args.min_count, args.max_num, args.explicit)
    codebook.write(file=args.codebook)
    if args.output:
        data.write(file=args.output)


def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="learning FMDL-based word segmentation")

    parser.add_argument(
        '--train', '-t', type=argparse.FileType('r'), default=sys.stdin,
        metavar='PATH',
        help="Input unsegmented text for training (default: standard input).")

    parser.add_argument(
        '--output', '-o', type=argparse.FileType('w'), default=None,
        metavar='PATH',
        help="Output segmented (default: standard output)")

    parser.add_argument(
        '--codebook', '-c', type=argparse.FileType('w'),
        metavar='FILE',
        help="Output file for codebook")

    parser.add_argument(
        '--iterations', '-i', type=int, default=10,
        help="# of iterations for FMDL learning (default: %(default)s).")

    parser.add_argument(
        '--explicit', '-e', default=False, action="store_true",
        help="""
        explicit mode: computing delta DL again to make sure that DL really decreases. (default: %(default)s).
        """)

    parser.add_argument(
        '--min_count', type=int, default=5,
        help="ignore the new words with a frequency lower than this. (default: %(default)s).")

    parser.add_argument(
        '--max_num', type=int, default=50000,
        help="vocabulary size of codebook. (default: %(default)s).")

    parser.add_argument(
        '--ref', '-r', type=argparse.FileType('r'), default=None,
        metavar='FILE',
        help="if the reference file is provided, print more information.")

    parser.add_argument(
        '--verbose', '-v', action="store_true",
        help="verbose mode, print the details.")

    return parser


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()

    main(args)
