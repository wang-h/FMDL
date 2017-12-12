import sys


def add_padding(sentence, padding=1, segmented=False):
    sentence = sentence.rstrip("\n")
    if not segmented:
        words = [w for w in sentence]
    else:
        words = sentence.split()
    words = ["<s>"] * padding + words + ["</s>"] * padding
    return words


def remove_blank(line):
    return line.rstrip("\n").replace(" ", "$$")


class Data:
    def __init__(self, segmented=False, padding=0, file=None):
        self.sentences = []
        self.segmented = segmented
        self.padding = padding
        self.len = 0
        if file:
            self.read(file=file)

    # def add_padding(self, sentence):
    #     sentence = sentence.rstrip("\n")
    #     if self.segmented:
    #         sentence = sentence.split()
    #     words = ["<s>"] * self.padding + [w for w in sentence] + ["</s>"] * self.padding
    #     return words

    def __setitem__(self, idx, item):
        self.sentences[idx] = item

    def __getitem__(self, idx):
        return self.sentences[idx]

    # def read(self, file=None):
    #     pool = Pool(core_number)
    #     self.sentences= pool.map(remove_blank, file, core_number)
    #     self.len = len(self.sentences)

    def read(self, file=None):
        for line in file:
            self.sentences.append(remove_blank(line))
        self.len = len(self.sentences)

    def __iter__(self, format="str"):
        for sentence in self.sentences:
            if format == "list":
                if self.segmented:
                    yield sentence.split()
                else:
                    yield [w for w in sentence]
            elif format == "str":
                yield sentence
            elif format == "unsegmented":
                yield "".join(sentence.split())

    def padded(self, padding=0, format="list"):
        self.padding = padding
        for sentence in self.sentences:
            if format == "list":
                yield add_padding(sentence, padding=self.padding, segmented=self.segmented)
            elif format == "str":
                yield " ".join(add_padding(sentence, padding=self.padding, segmented=self.segmented))

    def append(self, line):
        self.sentences.append(line)
        self.len += 1

    def write(self, file=sys.stdout):
        for sentence in self.sentences:
            print(sentence, file=file)

    @property
    def rawtext(self):
        return " \n ".join(self.padded(format="str"))
