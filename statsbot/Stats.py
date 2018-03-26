from statsbot.Log import Log
from collections import defaultdict
import operator
import cProfile
import nltk
from nltk.corpus import stopwords
from nltk.metrics import *
import numpy
import time


def descending_map(map, key=operator.itemgetter(1)):
    return [item for item in reversed(sorted(map.items(), key=key))]


def print_list(list):
    [print(item) for item in list]


ignored_words = stopwords.words("english")
ignored_words.extend(["n't", "'re", "like"])

word_filter_cache = {}


def word_filter(word):
    if word not in word_filter_cache:
        word_filter_cache[word] = len(word) >= 3 and word.lower() not in ignored_words

    return word_filter_cache[word]


class Distance:

    def __init__(self):
        self.masi = None
        self.jaccard = None
        self.nick_distance = None
        self.masi_index = None
        self.jaccard_index = None
        self.nick_distance_index = None

    def set_masi(self, masi):
        self.masi = masi

    def set_jaccard(self, jaccard):
        self.jaccard = jaccard

    def set_nick_distance(self, nick_distance):
        self.nick_distance = nick_distance

    def set_masi_index(self, masi_index):
        self.masi_index = masi_index

    def set_jaccard_index(self, jaccard_index):
        self.jaccard_index = jaccard_index

    def set_nick_distance_index(self, nick_distance_index):
        self.nick_distance_index = nick_distance_index

    def distance(self):
        return numpy.mean([self.masi / self.masi_index,
                           self.jaccard / self.jaccard_index,
                           self.nick_distance / self.nick_distance_index])

    def __str__(self):
        return "Distance: (distance=%f, masi(rel)=%f, jaccard(rel)=%f, nick_distance(rel)=%f)" \
               % (float(self.distance()),
                  self.masi / self.masi_index,
                  self.jaccard / self.jaccard_index,
                  self.nick_distance / self.nick_distance_index)

    def __repr__(self):
        return self.__str__()


def process(items, f, name):
    print("Computing %s..." % name)

    last_time = time.time()

    items = list(items)

    for i in range(len(items)):
        if time.time() > last_time + 1:
            print("%f%%" % (100 * i / len(items)))
            last_time = time.time()

        item = items[i]
        f(item)

    print("Done.")


class Nick:
    def __init__(self):
        self.raw_text = ""
        self.text = None
        self.messages = []
        self.message_frequency = None
        self.bad_word_count = defaultdict(int)
        self.bad_word_frequency = None

class Stats:

    def __init__(self, log, bad_words_file):
        self.bad_words_file = None
        self.nicks = defaultdict(lambda: Nick())
        self.distance = defaultdict(Distance)

        self.load_all_bad_words(bad_words_file)

        self.compute_raw_text_per_nick(log)
        self.compute_text_per_nick()
        self.compute_messages_per_nick(log)
        self.compute_message_frequency_per_nicks(log)
        self.compute_bad_word_count_per_nick()
        self.compute_bad_word_frequency_per_nick()

        self.compute_distance()

    def load_all_bad_words(self, bad_words_file):
        print("Loading bad words...")
        with open(bad_words_file) as file:
            self.all_bad_words = [word.strip() for word in file.readlines()]

        print("Done.")

    def compute_raw_text_per_nick(self, log):
        def f(entry):
            self.nicks[entry["nick"]].raw_text += entry["message"] + " "

        process(log.entries, f, "raw text per nick")

    def compute_text_per_nick(self):
        def f(nick):
            tokens = nltk.word_tokenize(self.nicks[nick].raw_text)
            tokens = filter(word_filter, tokens)
            self.nicks[nick].text = nltk.Text(tokens)

        process(self.nicks.keys(), f, "NLTK Text per nick")

    def compute_messages_per_nick(self, log):
        def f(entry):
            self.nicks[entry["nick"]].messages.append(entry["message"])

        process(log.entries, f, "messages per nick")

    def compute_message_frequency_per_nicks(self, log):
        def f(nick):
            self.nicks[nick].message_frequency = len(self.nicks[nick].messages) / len(log.entries)

        process(self.nicks.keys(), f, "message frequency over nicks")

    def compute_bad_word_count_per_nick(self):
        bad_word_cache = {}

        def f(nick):
            for word, count in self.nicks[nick].text.vocab().items():
                if word not in bad_word_cache:
                    bad_word_cache[word] = word in self.all_bad_words

                if bad_word_cache[word]:
                    self.nicks[nick].bad_word_count[word] += count

        process(self.nicks.keys(), f, "bad words per nick")

    def compute_bad_word_frequency_per_nick(self):
        def f(nick):
            total_word_count = sum(self.nicks[nick].text.vocab().values())
            total_bad_word_count = sum(self.nicks[nick].bad_word_count.values())

            if total_word_count > 1000 and total_bad_word_count / total_word_count > 0:
                self.nicks[nick].bad_word_frequency = total_bad_word_count / total_word_count

        process(self.nicks.keys(), f, "bad word percentage per nick")

    def compute_distance(self):
        print("Computing distance...")

        for nick in self.nicks.keys():
            if len(self.nicks[nick].text.vocab()) < 1000:
                continue

            for nick2 in self.nicks.keys():
                if len(self.nicks[nick2].text.vocab()) < 1000:
                    continue

                if nick == nick2:
                    continue

                def most_common_words(nick):
                    return {x for x, y in self.nicks[nick].text.vocab().most_common(50)}

                mcw_a = most_common_words(nick)
                mcw_b = most_common_words(nick2)

                self.distance[frozenset((nick, nick2))] \
                    .set_masi(masi_distance(mcw_a, mcw_b))

                self.distance[frozenset((nick, nick2))] \
                    .set_jaccard(jaccard_distance(mcw_a, mcw_b))

                self.distance[frozenset((nick, nick2))] \
                    .set_nick_distance(edit_distance(nick, nick2))

        masi_index = numpy.mean([sim.masi for sim in self.distance.values()])
        jaccard_index = numpy.mean([sim.jaccard for sim in self.distance.values()])
        nick_distance_index = numpy.mean([sim.nick_distance for sim in self.distance.values()])

        for sim in self.distance.values():
            sim.set_masi_index(masi_index)
            sim.set_jaccard_index(jaccard_index)
            sim.set_nick_distance_index(nick_distance_index)

        print("Done.")


def main():
    Stats(Log(filename="../resources/palle_pig.txt"), "../resources/bad-words.txt")


if __name__ == "__main__":
    #cProfile.run("main()", sort=1)
    main()

