#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import doctest
import time
import collections
import pickle as pickle
import gc
from functools import reduce
import SuffixArray
from _drittel import suffix_array

###############################################################################

__author__ = '##'
# Program a Python interface for the C++ program:
__date__, __version__ = '12/03/2014', '1.0'
                                            # Kärkkäinen and Sanders algorithm in C++ as _drittel.so using SWIG.
__date__, __version__ = '14/03/2014', '1.1'  # Start the class design.
# Program computation of lcp in C++.
__date__, __version__ = '14/03/2014', '1.2'
                                            # Change interface in C++ and integrate into _drittel.so.
# Bug in IntegerSuffixArray._dichotomic_search on word of index 0 with 1 occurrence:
__date__, __version__ = '12/09/2014', '1.3'
                                            # was while inf+1 < sup, replaced by correct while inf+1 <= sup.
                                            # WAS A WRONG CORRECTION. SEE NEXT VERSION.
# Bug in IntegerSuffixArray._dichotomic_search: inf <= sup, but
__date__, __version__ = '25/11/2014', '1.4'
                                            # first sup should be self.len-1, corrected when calling _dichotomic_search
                                            # in search_index and nbr_of_occs.
                                            # Added doctests with unsuccessful searches, all passed.
                                            # Added doctests with word on index 0 with 1 occurrence, all passed.
                                            # Added doctests with words, all passed.

__description__ = """Class for suffix arrays in characters or words."""

__verbose__ = False
__trace__ = False

###############################################################################


class IntegerSuffixArray:
    # Class for list of integers.
    # See UnicodeSuffixArray below for strings of characters.
    # See WordSuffixArray below for strings of words.

    def __init__(self, int_array):
        self.text = int_array
        self.len = n = len(self.text)
        self.sa, self.lcp = [0] * n, [0] * n

        if __verbose__: print >> sys.stderr, '# Computing suffix array...'
        t1 = time.time()
        # from _drittel, i.e., Kärkkäinen and Sanders algorithm
        suffix_array(self.text, self.sa, self.lcp)
        if __verbose__: print >> sys.stderr, '# Suffix array computed in %.2fs.' % (
            time.time() - t1)

    def __iter__(self):
        """
        >>> [ i for i in IntegerSuffixArray([ 105, 104, 103, 102,101, 100 ]) ]
        [5L, 4L, 3L, 2L, 1L, 0L]
        """
        return iter(self.sa)

    def keys(self):
        """
        This is an iterator.
        Yield the suffixes of the text in the order of the suffix array, i.e., sorted.

        >>> list( IntegerSuffixArray([ 102, 101, 100 ]).keys() )
        [[100], [101, 100], [102, 101, 100]]
        """
        for i in range(len(self)):
            yield self.text[self.sa[i]:]

    def values(self):
        """
        This is an iterator.
        Yield the indices in the text in the order of the suffix array.

        >>> list( IntegerSuffixArray([ 102, 101, 100 ]).values() )
        [2L, 1L, 0L]
        """
        for id in self.sa:
            yield id

    def _dichotomic_search(self, inf, sup, key, length):
        # Dichotomic search in the suffix array.
        if __trace__: print >> sys.stderr, '# Text = %s' % self.text
        while inf <= sup:
            mid = int((inf + sup) / 2)
            if __trace__: print >> sys.stderr, '# inf=%d <= sup=%d, mid = %d' % (
                inf, sup, mid)
            midindex = self.sa[mid]
            midtext = self.text[midindex:midindex + length]
            midtextlength = len(midtext)
            if __trace__: print >> sys.stderr, '# key = "%s" <?=?> self.sa[%d] = "%s", length = %d' % \
                                    (key, mid, midtext, midtextlength)
            if key == midtext:
                # The key has been found.
                if __trace__: print >> sys.stderr, '# key = "%s" == self.sa[%d] = "%s", length = %d' % \
                                    (key, mid, midtext, midtextlength)
                inf, sup = mid, mid
                while 0 <= inf and length <= self.lcp[inf]: inf -= 1
                while sup + \
                    1 < self.len and length <= self.lcp[sup + 1]: sup += 1
                return (inf, sup + 1)
            elif key < midtext:
                if __trace__: print >> sys.stderr, '# key = "%s" < self.sa[%d] = "%s", length = %d' % \
                                    (key, mid, midtext, midtextlength)
                inf, sup = inf, mid - 1
            elif midtext < key:
                if __trace__: print >> sys.stderr, '# key = "%s" > self.sa[%d] = "%s", length = %d' % \
                                    (key, mid, midtext, midtextlength)
                inf, sup = mid + 1, sup
        if __trace__: print >> sys.stderr, '# inf=%d > sup=%d' % (inf, sup)
        # The key has not been found.
        return None

    # Input: a list of integers (= the key).
    # Output: a list of positions in the array of integers, where the key starts and is found.
    def search_index(self, key):  # Should be called pos in text.
        interval = self._dichotomic_search(0, self.len - 1, key, len(key))
        if interval == None:
            return []
        else:
            return [self.sa[i] for i in range(*interval)]

    # Return the number of occurrences of a list of integers (= key) in the text.
    def nbr_of_occs(self, key):
        interval = self._dichotomic_search(0, self.len - 1, key, len(key))
        if interval == None:
            return 0
        else:
            return interval[1] - interval[0]

    # Input: a string of integers (= the key).
    # Output: the set of the longest substrings of the string
    # which appear strictly more than a certain number of times in the text.
    def substrings_in_text(self, key, min=0):
        keylen = len(key)
        result = set()
        length = 0
        for start in range(keylen):
                if length != 0: length -= 1
                for end in reversed(range(start + 1 + length, keylen + 1)):
                    subkey, subkeylen = key[start:end], end - start
                    if tuple(subkey) not in result:
                        if min < self.nbr_of_occs(subkey):
                            result.add(tuple(subkey))
                            length = subkeylen
                            break
        return result

    # Input: a string of integers (= the key).
    # Output: the set of the shortest substrings of the string which DO NOT appear in the text,
    # or appear less than a certain number of times in the text.
    def substrings_not_in_text(self, key, max=0):
        keylen = len(key)
        result = set()
        stoplist = set()
        for subkeylen in range(1, keylen):
            newstoplist = set( start-1 for start in stoplist if start > 0 )
            stoplist = stoplist.union(newstoplist)
            for start in range(keylen-subkeylen):
                if start not in stoplist:
                    subkey = key[start:start+subkeylen]
                    if max >= self.nbr_of_occs(subkey):
                        result.add(tuple(subkey))
                        stoplist.add(start)
        return result

    def __getitem__(self, indices):
        """
        >>> IntegerSuffixArray([ 102, 101, 100 ])[2]
        102
        >>> IntegerSuffixArray([ 102, 101, 100 ])[2:]
        [102]
        >>> IntegerSuffixArray([ 102, 101, 100 ])[1:]
        [101, 102]
        """
        if isinstance(indices, int) or isinstance(indices, long):
            return self.text[self.sa[indices]]
        elif isinstance(indices, slice):
            start, stop, step = indices.indices(len(self))
            return [ self.text[position] for position in self.sa[start:stop:step] ]
        else:
            raise TypeError("indices must be int, or slice, or list of ints or slices")

    def compose_text(self, indices):
        """
        Indices is a list of positions in the text.
        >>> sa = IntegerSuffixArray([ 100, 101, 102, 103, 104, 105, 106, 107, 108, 109 ])
        >>> sa.compose_text([])
        []
        >>> sa.compose_text([8,3,4,1,2])
        [108, 103, 104, 101, 102]
        >>> sa.compose_text([7,6,5])
        [107, 106, 105]
        >>> sa.compose_text([9,0,8,1])
        [109, 100, 108, 101]
        >>> sa.compose_text([2])
        [102]
        """
        if isinstance(indices, list) or isinstance(indices, tuple):
            return reduce( type(self.text).__add__, (self.text[id:id+1] for id in indices), type(self.text)() )
        else:
            raise TypeError("indices must be list or tuple of ints")

    def __len__(self):
        return self.len

    def __repr__(self, span=5):
        s = ''
        for i in range(self.len):
            s += 'sa[%d] = ' % i
            k = self.sa[i]
            s += '%s' % self.text[k:k+span]
            if len(self.text[k:k+span]) >= span:
                s += u'...'
            s += '\tlcp = %d' % self.lcp[i]
            s += '\n'
        return s.encode('UTF-8')

###############################################################################

class UnicodeSuffixArray(IntegerSuffixArray):

    def __init__(self, s):
        # Convert the string into an array of integers: call ord for that.
        IntegerSuffixArray.__init__(self, [ ord(c) for c in s ])
        # Store the text as a UnicodeTextForSuffixArray to be able to output properly.
        self.text = s

    def _unicode_to_int(self, s):
        for c in s.decode('UTF-8'):
            yield ord(c)

    def keys(self):
        """
        This is an iterator.
        Yield the suffixes of the text in the order of the suffix array, i.e., sorted.
        
        >>> sa = UnicodeSuffixArray('hgfedcba')
        >>> sa.text                # The text.
        'hgfedcba'
        >>> list( sa.values() )    # All positions in the string sorted by suffix.
        [7L, 6L, 5L, 4L, 3L, 2L, 1L, 0L]
        >>> list( sa[''] )        # All possible positions in the suffix array, as the empty string occurs everywhere.
        [7L, 6L, 5L, 4L, 3L, 2L, 1L, 0L]
        >>> list( sa.keys() )    # All suffixes sorted, i.e., the suffix array.
        ['a', 'ba', 'cba', 'dcba', 'edcba', 'fedcba', 'gfedcba', 'hgfedcba']
        """
        for i in range(len(self)):
            yield self.text[self.sa[i]:]

    def __getitem__(self, string):
        """
        >>> sa = UnicodeSuffixArray(u'hgfedcba')
        >>> sa[u'ed']
        [3L]
        >>> sa[u'fed']
        [2L]
        >>> sa[u'edc']
        [3L]
        >>> sa[u'gfed']
        [1L]
        >>> sa[sa.text]        # 0L as the entire text starts at position 0.
        [0L]
        >>> sa[u'xyz']        # Empty list of positions for a string not present in the text.
        []
        >>> sa[u'abcdefghijklmno']        # Empty list of positions for a string not present in the text.
        []
        >>> sa[u'fed']
        [2L]
        >>> sa.text[2]
        u'f'
        >>> sa.text[2:]
        u'fedcba'
        >>> sa.text[2:99]
        u'fedcba'
        >>> sa = UnicodeSuffixArray('a'*2)
        >>> sa[u'a']
        [1L, 0L]
        >>> sa[u'a'*3]
        []
        >>> sa = UnicodeSuffixArray('a'*6)
        >>> sa[u'a']
        [5L, 4L, 3L, 2L, 1L, 0L]
        >>> sa[u'a'*7]
        []
        """
        if isinstance(string, str) or isinstance(string, unicode): 
            # In this case, string is a unicode key to be searched in the suffix array.
            return self.search_index(string)
        else:
            raise TypeError("argument must be string")

    def glue(self, list):
        return ''.join(list)

    def compose_text(self, indices):
        """
        Indices is a list of positions in the text.
        >>> sa = UnicodeSuffixArray(' abcdefghi')
        >>> sa.compose_text([])
        ''
        >>> sa.compose_text([8,3,4,1,2])
        'hcdab'
        >>> sa.compose_text([7,6,5])
        'gfe'
        >>> sa.compose_text([9,0,8,1])
        'i ha'
        >>> sa.compose_text([2])
        'b'
        """
        return self.glue([ self.text[id] for id in indices ])

    def dump(self, file=sys.stdout):
        if __verbose__: print >> sys.stderr, '# Saving suffix array...'
        t1 = time.time()
        gc.disable()
#        pickle.dump(sa, open('tmp.p','wb'), protocol=-1)
        pickle.dump(sa, file, protocol=-1)
        gc.enable()
        if __verbose__: print >> sys.stderr, '# Suffix array saved in %.2fs.' % (time.time() - t1)

    def load(self, file=sys.stdin):
        if __verbose__: print >> sys.stderr, '# Loading suffix array...'
        t1 = time.time()
        gc.disable()
#        sa = pickle.load(open('tmp.p','rb'))
        sa = pickle.load(file)
        gc.enable()
        if __verbose__: print >> sys.stderr, '# Suffix array loaded in %.2fs.' % (time.time() - t1)

    def __repr__(self, span=10):
        s = ''
        for i in range(self.len):
            s += 'sa[%d] = ' % i
            k = self.sa[i]
            s += self.text[k:k+span]
            if len(self.text[k:k+span]) >= span:
                s += '...'
            s += '\tlcp = %d' % self.lcp[i]
            s += '\n'
        return s.encode('UTF-8')

###############################################################################

class WordListForSuffixArray:

    def __init__(self, list_of_words):
        self.list = list_of_words
        self.len = len(list_of_words)

    def glue(self, words):
        """
        >>> words = WordListForSuffixArray([])
        >>> words.glue([])
        ''
        >>> words.glue(['d', 'c', 'b', 'a'])
        'd c b a'
        """
        return ' '.join(words)

    def __getitem__(self, indices):
        """
        >>> sa = WordSuffixArray('the quick brown fox is quick and brown')
        >>> sa.text[3]
        'fox'
        >>> sa.text[1:5]
        'quick brown fox is'
        >>> sa.text[6:99] # Will be truncated by slice of list.
        'and brown'
        """
        if isinstance(indices, slice):
            return ' '.join( self.list[id] for id in range(*indices.indices(self.len)) )
        elif isinstance(indices, int) or isinstance(indices, long):
            return self.list[indices]
        else:
            raise TypeError("indices must be int, or slice, or list of ints or slices")

class WordSuffixArray:
    # Two extra attributes:
    # vocabulary: a dictionary with all words
    # vocabularysize: the vocabulary size

    def __init__(self, s):
        # Split the text into typographic words.
        words = s.strip().split()
        length = len(words)
        # Vocabulary is a dictionary, words to integers.
        voc = list(set(words))
        vocabularysize = len(voc)
        _id_to_word_dict = dict( enumerate(voc) )
        _word_to_id_dict = dict( (word,i) for (i,word) in enumerate(voc) )
        # Compute the suffix array using the integer array representing the text, i.e., each word replaced by its id.
        self.idsa = IntegerSuffixArray( [ _word_to_id_dict[word] for word in words ] )
        # Memorize the list of words as a special text for suffix arrays of words.
        self.text = WordListForSuffixArray(words)
        self.len = length
        self.vocabulary = voc
        self.vocabularysize = vocabularysize
        self._id_to_word_dict = _id_to_word_dict
        self._word_to_id_dict = _word_to_id_dict
        self._average_word_length = len(s) / len(words)

    def average_word_length(self):
        return self._average_word_length

    def keys(self):
        """
        This is an iterator.
        Yield the suffixes of the text in the order of the suffix array, i.e., sorted.
        
        >>> sa = WordSuffixArray('the quick brown fox')
        >>> list( sa.keys() )
        ['quick brown fox', 'brown fox', 'the quick brown fox', 'fox']
        >>> list( sa.values() )
        [1L, 2L, 0L, 3L]
        """
        for i in range(len(self.idsa)):
            yield self._id_array_to_word_list(self.idsa.text[self.idsa.sa[i]:])

    def values(self):
        return self.idsa.values()
        
    def _word_to_id(self, word):
        if word in self._word_to_id_dict:
            return self._word_to_id_dict[word]
        else:
            return -1

    def _word_list_to_id_array(self, s):
        return [ self._word_to_id(word) for word in s.strip().split() ]

    def _id_to_word(self, id):
        if 0 <= id < self.vocabularysize:
            return self._id_to_word_dict[id]
        else:
            return 'UNK'

    def _id_array_to_word_list(self, id_array):
        return ' '.join([ self._id_to_word(id) for id in id_array ])

    # Input: a string of characters that will be converted into a list of words.
    # Output: a list of positions in the text, where the key starts.
    def search_index(self, key):
        idarray = self._word_list_to_id_array(key)
        if -1 in set(idarray):
            return []
        else:
            return self.idsa.search_index(idarray)
        
    # Return the number of occurrences of a string in the text.
    def nbr_of_occs(self, key):
        # if __trace__: print >> sys.stderr, '%s: %s' % (key, self._word_list_to_id_array(key))
        return self.idsa.nbr_of_occs(self._word_list_to_id_array(key))

    # Functional to pass a key (= words) to the suffix array and get back words.
    def _encode_decode(self, fct, key, *args):
        return [ self._id_array_to_word_list(indices) for indices in fct(self._word_list_to_id_array(key), *args) ]

    # Input: a string (= the key).
    # Output: a list of the longest substrings that appear in the text.
    def substrings_in_text(self, key, min=1):
        return sorted(self._encode_decode(self.idsa.substrings_in_text, key, min))

    # Input: a string (= the key).
    # Output: a list of the shortest substrings that DO NOT appear in the text.
    def substrings_not_in_text(self, key, max=0):
        return sorted(self._encode_decode(self.idsa.substrings_not_in_text, key, max))

    def __getitem__(self, string):
        """
        >>> sa = WordSuffixArray(u'the quick brown fox is quick and brown')
        >>> sa[u'the']
        [0L]
        >>> sa[u'quick']
        [5L, 1L]
        >>> sa[u'brown']
        [7L, 2L]
        >>> sa[u'fox']
        [3L]
        >>> sa[u'quick brown']
        [1L]
        >>> sa[u'the quick brown']
        [0L]
        >>> sa[u'quark']
        []
        >>> sa[u'Higgs boson']
        []
        >>> sa = WordSuffixArray(u'aa b c d e')
        >>> sa[u'aa']
        [0L]
        >>> sa[u'aa b']
        [0L]
        >>> sa[u'aa b ']
        [0L]
        >>> sa[u'aa b c']
        [0L]
        >>> sa[u'bb']
        []
        """
        if isinstance(string, str) or isinstance(string, unicode): # In this case, string is a unicode key to be searched in the suffix array.
            return self.search_index(string)
        else:
            raise TypeError("argument must be string")

    # Input: a list of words.
    # Output: the list of words as one string.
    def glue(self, words):
        return self.text.glue(words)

    def compose_text(self, indices):
        """
        Indices is a list of positions in the text.
        >>> sa = WordSuffixArray('100 101 102 103 104 105 106 107 108 109')
        >>> sa.compose_text([])
        ''
        >>> sa.compose_text([8,3,4,1,2])
        '108 103 104 101 102'
        >>> sa.compose_text([7,6,5])
        '107 106 105'
        >>> sa.compose_text([9,0,8,1])
        '109 100 108 101'
        >>> sa.compose_text([2])
        '102'
        """
        return self.glue([ self.text[id] for id in indices ])

    def dump(self, file=sys.stdout):
        if __verbose__: print >> sys.stderr, '# Saving suffix array...'
        t1 = time.time()
        gc.disable()
#        pickle.dump(sa, open('tmp.p','wb'), protocol=-1)
        pickle.dump(self, file, protocol=-1)
        gc.enable()
        if __verbose__: print >> sys.stderr, '# Suffix array saved in %.2fs.' % (time.time() - t1)

    def load(self, file=sys.stdin):
        if __verbose__: print >> sys.stderr, '# Loading suffix array...'
        t1 = time.time()
        gc.disable()
#        sa = pickle.load(open('tmp.p','rb'))
        sa = pickle.load(file)
        gc.enable()
        if __verbose__: print >> sys.stderr, '# Suffix array loaded in %.2fs.' % (time.time() - t1)

    def __repr__(self, span=5):
        s = ''
        for i in range(self.len):
            s += 'sa[%d] = ' % i
            k = self.idsa.sa[i]
            s += self.text[k:k+span]
            if len(self.text[k:k+span]) >= span:
                s += '...'
            s += '\tlcp = %d' % self.idsa.lcp[i]
            s += '\n'
        return s

###############################################################################
# Normally, this should be the only entry point of this module.

def SuffixArray(input, unit='unicode'):
    try:
        if unit == 'int':
            return IntegerSuffixArray(input)
        elif unit == 'unicode' or unit == 'char':
            return UnicodeSuffixArray(input)
        elif unit == 'word':
            return WordSuffixArray(input)
        elif unit == 'help':
            print( """The help now provides more info on use:

Examples -- how to build a suffix array

>>> sa1 = SuffixArray('The quick brown\\nfox...')
>>> sa1 = SuffixArray('The quick brown\\nfox...', unit='char') # same as above
>>> sa1 = SuffixArray('The quick brown\\nfox...', unit='unicode') # same as above

>>> sa2 = SuffixArray('the brown\\nfox chases the brown chicken...', unit='word')

>>> sa3 = SuffixArray([24, 12, 4, 24, 7, ...], unit='int')

Examples -- how to search a suffix array:

>>> sa1['quick'] # Returns the list of all starting positions for the string 'quick'.
[4, ...]

>>> sa1.text[4:9] # Returns the text between the indices.
'quick'

>>> sa2['the brown'] # Returns the list of all starting positions for the string of words 'the brown'.
[0, 4,...]

>>> sa2.text[1:4] # Returns the sequence of words between the indices.
'brown fox chases'
""")
    except NameError:
        print('%s not a valid unit name.' % unit)

###############################################################################

def read_argv():

    from optparse import OptionParser
    this_version = 'v%s (c) %s %s' % (__version__, __date__, __author__)
    this_description = __description__
    this_usage = '''as a program:
    
    %%prog < TEXT > SUFFIX_ARRAY.gz
    
Save the suffix array of the TEXT into a zipped file.
    
As a Python library

    from %%prog import SuffixArray

and the only call should be to this function, SuffixArray, which takes a text as input,
and returns an object of the desired class, depending on the unit used (default: unicode
characters).

Examples:

    sa1 = SuffixArray('The quick brown\\nfox...')
    sa1 = SuffixArray('The quick brown\\nfox...', unit='char')    # same as above
    sa1 = SuffixArray('The quick brown\\nfox...', unit='unicode')    # same as above

    sa2 = SuffixArray('The quick brown\\nfox...', unit='word')

    sa3 = SuffixArray([24, 12, 4, 24, 7, ...], unit='int')
'''

    parser = OptionParser(version=this_version, description=this_description, usage=this_usage)
    parser.add_option('-w', '--words',
                  action='store_true', dest='words', default=False,
                  help='interpret text as list of words (default: list of Unicode characters)')
    parser.add_option('-v', '--verbose',
                  action='store_true', dest='verbose', default=False,
                  help='runs in verbose mode')
    parser.add_option('-T', '--test',
                  action='store_true', dest='test', default=False,
                  help='run all unitary tests')
                        
    (options, args) = parser.parse_args()
    return options, args

###############################################################################

def _test():
    import doctest
    doctest.testmod()
    sys.exit(0)

def main(file=sys.stdin):
    if __verbose__: print >> sys.stderr, '# Reading file...'
    t1 = time.time()
    s = file.read()

if __name__ == '__main__':
    options, args = read_argv()
    if options.test: _test()
    __verbose__ = options.verbose
    if options.words:
        if __verbose__: print >> sys.stderr, '# Reading text as a string of words.'
        unit = 'word'
    else:
        if __verbose__: print >> sys.stderr, '# Reading text as a string of characters.'
        unit = 'unicode'


    sa = SuffixArray(sys.stdin.read(),unit=unit)
    print(sa.dump())

