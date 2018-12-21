Efficient Unsupervised Word Segmenter using Minimum Description Length for Neural Machine Translation
=======
Are you looking for a simple python implementation of [Byte Pair Encoding (BPE)](https://github.com/rsennrich/subword-nmt.git) for Chinese/Japanese? 

Though it is more than BPE, we developed yet another unsupervised subword segmenter for these languages using the principle of Minimum Description Length (MDL).

You can train an FMDL-based subword segmentation model in 1 minute!

This repository contains preprocessing scripts to segment Chinese/Japanese text into subword
units. We design a variation of MDL with additional finite vocabulary restriction. The experiment results in Neural Machine Translation have shown competitive translation scores compared with SentencePiece or subword-nmt + Segmenter.

RUN WITHOUT INSTALLATION
------------
The scripts are executable stand-alone, but you need to compile SuffixArray library in advance.
    
    bash compile.sh

REQUIREMENTS
------------

python version >= 3.6 (recommended)

SWIG Version >= 3.0.8 (recommended)

cmake version >= 3.9.4 (recommended)



After finishing the build, you can run the scripts directly.

USAGE INSTRUCTIONS
------------------
Please check the individual files for usage instructions.

To apply MDL to word segmentation, invoke these commands:

    python learn_mdl.py --train {train.unseg.txt} --vocab_size 20000 --model {fmdl.model} -v

The input of the training dataset should be unsegmented raw text, line by line.

To segment text into subword sequences, do the following:

    python apply_mdl.py --input {test.txt} --model {fmdl.model} > {test.seg.txt}


Comparison on ASPEC Corpus 
------------

| Japanese--Chinese| WER   | BLEU  | NIST  | TER   | RIBES |
| -----------------| ------| ------| ------| ------| ------|
| NMT (baseline)   | 0.4529| 30.18 | 8.147 | 0.4793| 83.34 |
| BPE              | Content Cell  |
| SentencePiece    | 0.4551| 32.14 | 8.380 | 0.4830| 83.70 |
| FM-MDL           | 0.4353| 32.12 | 8.477 | 0.4647| 84.47 |

PUBLICATIONS
------------

not yet.


