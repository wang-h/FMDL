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
from modules.CodeBook import CodeBook
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





def main(args):
    codebook = CodeBook()
    codebook.load(args.codebook)
    dataset = DataSet(args.input)
    dataset.apply_codebook(codebook, resample=False)
    for line in dataset.segmented():
        print(line)
    


def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="apply learned (FMDL-based) codebook to word segmentation")
    parser.add_argument(
        '--input', '-i', type=str, metavar='PATH',
        help="Input unsegmented text for training (default: standard input).")
    parser.add_argument(
        '--output', '-o', type=argparse.FileType('w'), default=None,
        metavar='PATH',
        help="Output segmented (default: standard output)")
    parser.add_argument(
        '--codebook', '-c', type=argparse.FileType('r'), required=True,
        metavar='FILE',
        help="Output file for codebook")
    parser.add_argument(
        '--verbose', '-v', action="store_true",
        help="verbose mode, print the details.")

    return parser


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    main(args)
