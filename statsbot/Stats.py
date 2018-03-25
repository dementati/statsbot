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


class Stats:

    def __init__(self, log, bad_words_file):
        self.all_bad_words = self.load_all_bad_words(bad_words_file)

        self.raw_text_per_nick = self.compute_raw_text_per_nick(log)

        self.text_per_nick = self.compute_text_per_nick(self.raw_text_per_nick)

        self.words_per_nick = self.compute_words_per_nick(log)

        self.distance = self.compute_distance(self.words_per_nick)

        self.message_count_per_nick = self.compute_message_count_per_nick(log)

        self.message_distribution_over_nicks = \
            self.compute_message_distribution_over_nicks(log, self.message_count_per_nick)

        self.bad_words_per_nick = self.compute_bad_words_per_nick(self.all_bad_words, self.words_per_nick)

        self.bad_word_percentage_per_nick = \
            self.compute_bad_word_percentage_per_nick(self.bad_words_per_nick, self.words_per_nick)

    @staticmethod
    def compute_raw_text_per_nick(log):
        raw_text_per_nick = defaultdict(str)

        def f(entry):
            raw_text_per_nick[entry["nick"]] += entry["message"] + " "

        process(log.entries, f, "raw text per nick")

        return raw_text_per_nick

    @staticmethod
    def compute_text_per_nick(raw_text_per_nick):
        text_per_nick = defaultdict(nltk.Text)

        def f(nick):
            tokens = nltk.word_tokenize(raw_text_per_nick[nick])
            tokens = filter(word_filter, tokens)
            text_per_nick[nick] = nltk.Text(tokens)

        process(raw_text_per_nick.keys(), f, "NLTK Text per nick")
        return text_per_nick

    @staticmethod
    def compute_words_per_nick(log):
        words_per_nick = defaultdict(lambda: defaultdict(int))

        def f(entry):
            words = entry["message"].split()
            words = [word.strip(".") for word in words]
            words = [word.lower() for word in words]
            words = filter(word_filter, words)

            for word in words:
                words_per_nick[entry["nick"]][word] += 1

        process(log.entries, f, "words per nick")
        return words_per_nick

    @staticmethod
    def compute_distance(words_per_nick):
        print("Computing distance...")
        words_per_nick = {nick : words for nick, words in words_per_nick.items() if len(words) > 1000}

        most_common_words = {}
        for nick in words_per_nick.keys():
            if len(words_per_nick[nick]) > 1000:
                most_common_words[nick] = set(pair[0] for pair in descending_map(words_per_nick[nick])[0:50])

        distance = defaultdict(Distance)
        for nick in most_common_words.keys():
            for nick2 in most_common_words.keys():
                if nick != nick2:
                    distance[frozenset((nick, nick2))]\
                        .set_masi(masi_distance(most_common_words[nick], most_common_words[nick2]))

                    distance[frozenset((nick, nick2))] \
                        .set_jaccard(jaccard_distance(most_common_words[nick], most_common_words[nick2]))

                    distance[frozenset((nick, nick2))] \
                        .set_nick_distance(edit_distance(nick, nick2))

        masi_index = numpy.mean([sim.masi for sim in distance.values()])
        jaccard_index = numpy.mean([sim.jaccard for sim in distance.values()])
        nick_distance_index = numpy.mean([sim.nick_distance for sim in distance.values()])

        for sim in distance.values():
            sim.set_masi_index(masi_index)
            sim.set_jaccard_index(jaccard_index)
            sim.set_nick_distance_index(nick_distance_index)

        print("Done.")
        return distance

    @staticmethod
    def compute_message_count_per_nick(log):
        message_count_per_nick = defaultdict(int)

        def f(entry):
            message_count_per_nick[entry["nick"]] += 1

        process(log.entries, f, "message count per nick")

        return message_count_per_nick

    @staticmethod
    def compute_message_distribution_over_nicks(log, message_count_per_nick):
        message_distribution_over_nicks = defaultdict(float)

        def f(nick):
            message_distribution_over_nicks[nick] = message_count_per_nick[nick] / len(log.entries)

        process(message_count_per_nick.keys(), f, "message distribution over nicks")

        return message_distribution_over_nicks

    @staticmethod
    def load_all_bad_words(bad_words_file):
        print("Loading bad words...")
        with open(bad_words_file) as file:
            all_bad_words = [word.strip() for word in file.readlines()]

        print("Done.")
        return all_bad_words

    @staticmethod
    def compute_bad_words_per_nick(all_bad_words, words_per_nick):
        bad_words_per_nick = defaultdict(lambda: defaultdict(int))

        bad_word_cache = {}

        def f(nick):
            for word in words_per_nick[nick].keys():
                if word not in bad_word_cache:
                    bad_word_cache[word] = word in all_bad_words

                if bad_word_cache[word]:
                    bad_words_per_nick[nick][word] += words_per_nick[nick][word]

        process(words_per_nick.keys(), f, "bad words per nick")

        return bad_words_per_nick

    @staticmethod
    def compute_bad_word_percentage_per_nick(bad_words_per_nick, words_per_nick):
        bad_word_percentage_per_nick = defaultdict(float)

        def f(nick):
            total_word_count = sum([words_per_nick[nick][word] for word in words_per_nick[nick].keys()])
            total_bad_word_count = sum([bad_words_per_nick[nick][word] for word in bad_words_per_nick[nick].keys()])

            if total_word_count > 1000 and total_bad_word_count / total_word_count > 0:
                bad_word_percentage_per_nick[nick] = total_bad_word_count / total_word_count

        process(words_per_nick.keys(), f, "bad word percentage per nick")

        return bad_word_percentage_per_nick


def main():
    Stats(Log(filename="../resources/palle_pig.txt"), "../resources/bad-words.txt")


if __name__ == "__main__":
    #cProfile.run("main()", sort=1)
    main()

