Efficient Unsupervised Word Segmenter using Minimum Description Length for Neural Machine Translation
=======
Are you looking for a simple implementation of [Byte Pair Encoding (BPE)](https://github.com/rsennrich/subword-nmt.git) for Chinese/Japanese? 

We developed yet another unsupervised word segmenter for East Asian languages.
This is based on the principle of Minimum Description Length (MDL) imposing the restriction of finite vocabulary, so we call it "FMDL".

Theorically, FMDL considers more than BPE given the minimal coding cost in vocabulary,
while this implementation is more simple and efficient than the SentencePiece version of BPE.  It requires only 1 minute to train a segmentation model!

This repository contains main codes of FMDL for word segmentation (not only subwords, maybe longer than the plain word) for Chinese/Japanese text processing.  Experimental results in Neural Machine Translation shows competitive translation scores compared with SentencePiece or BPE.

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
Vocab = 20K

| Japanese--Chinese| WER   | BLEU  | NIST  | TER   | RIBES |
| -----------------| ------| ------| ------| ------| ------|
| NMT (baseline)   | 45.29 | 30.18 | 8.147 | 47.93 | 83.34 |
| BPE              | 46.24 | 31.63 | 8.257 | 49.32 | 83.36 |
| SentencePiece    | 45.51| **32.14** | 8.380 | 48.30 | 83.70 |
| F-MDL            | **43.22**| **32.42** | **8.476** | **46.66** | **84.28** |
| FM-MDL (min_count=5)   | **43.53**| **32.12** | **8.477** | **46.47** | **84.47** |

Boldface means no statistically significant difference with the best systems.

PUBLICATIONS
------------

not yet.


