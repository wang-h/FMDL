#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Hao WANG

"""

"""

import sys
import argparse
from modules import Data
from modules import CodeBook


def apply_codebook(data, codebook, min_count):
    iterator = data.__iter__(format="unsegmented")
    for i, unseg_sentence in enumerate(iterator):
        data[i]=segment_with_codebook(unseg_sentence, codebook, min_count)

def segment_with_codebook(unseg_sentence, codebook, min_count):
    l = len(unseg_sentence)
    i = 0
    pieces = []
    while i < l:
        j = i+1
        while j < l:
            j += 1
            left = unseg_sentence[i:j]
            freq = codebook[left]
            if freq <= min_count:
                j -= 1
                break
        pieces.append(unseg_sentence[i:j])
        i = j
    return " ".join(pieces)

def main(args):
    data = Data(segmented=False, file=args.input)
    codebook = CodeBook(file=args.codebook)
    apply_codebook(data, codebook, args.min_count)
    data.write(file=args.output)

def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="apply word segmentation according to FMDL codebook.")

    parser.add_argument(
        '--codebook', '-c', type=argparse.FileType('r'), metavar='CODEBOOK',
        help="initial codebook.")

    parser.add_argument(
        '--input', '-i', type=argparse.FileType('r'), default=sys.stdin,
        metavar='PATH',
        help="Input text (default: standard input).")

    parser.add_argument(
        '--output', '-o', type=argparse.FileType('w'), default=sys.stdout,
        metavar='PATH',
        help="Output file for BPE codes (default: standard output)")

    parser.add_argument(
        '--min_count', type=int, default=5, metavar='FREQ',
        help='Stop if no symbol pair has frequency >= FREQ (default: %(default)s))')
    
    
    parser.add_argument(
        '--verbose', '-v', action="store_true",
        help="verbose mode.")

    return parser


if __name__ == '__main__':


    parser = create_parser()
    args = parser.parse_args()


    main(args)
