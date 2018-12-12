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
from learn_mdl import FMDL
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




def read_model(model_file):
    model = dict()
    for line in model_file:
        col = line.rstrip("\n").split("\t")
        model[tuple(x for x in col[0])] = float(col[1])
    return model

def main(args):
    dataset = DataSet()
    model = read_model(args.model)
    for line in dataset.segment(model, args.input):
        print(line)
    
    


def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="apply learned (FMDL-based) vocab to word segmentation")
    parser.add_argument(
        '--input', '-i', type=str, metavar='PATH',
        help="Input unsegmented text for training (default: standard input).")
    parser.add_argument(
        '--output', '-o', type=argparse.FileType('w'), default=None,
        metavar='PATH',
        help="Output segmented (default: standard output)")
    parser.add_argument(
        '--model', '-m', type=argparse.FileType('r'), required=True,
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
