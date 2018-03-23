from statsbot.Log import Log
from collections import defaultdict
import operator
import cProfile
import nltk
from nltk.corpus import stopwords

def descending_map(map):
    return [item for item in reversed(sorted(map.items(), key=operator.itemgetter(1)))]


def print_list(list):
    [print(item) for item in list]


class Stats:

    def __init__(self, log, bad_words_file):
        self.all_bad_words = self.load_all_bad_words(bad_words_file)

        self.text_per_nick = self.compute_text_per_nick(log)

        self.words_per_nick = self.compute_words_per_nick(log)

        self.message_count_per_nick = self.compute_message_count_per_nick(log)

        self.message_distribution_over_nicks = \
            self.compute_message_distribution_over_nicks(log, self.message_count_per_nick)

        self.bad_words_per_nick = self.compute_bad_words_per_nick(self.all_bad_words, self.words_per_nick)

        self.bad_word_percentage_per_nick = \
            self.compute_bad_word_percentage_per_nick(self.bad_words_per_nick, self.words_per_nick)

    @staticmethod
    def compute_text_per_nick(log):
        raw_text_per_nick = defaultdict(str)
        for entry in log.entries:
            raw_text_per_nick[entry["nick"]] += entry["message"] + " "

        text_per_nick = defaultdict(nltk.Text)
        for nick in raw_text_per_nick:
            tokens = nltk.word_tokenize(raw_text_per_nick[nick])
            ignored = stopwords.words("english")
            ignored.extend(["n't", "'re", "like"])
            tokens = filter(lambda w: len(w) >= 3 and w.lower() not in ignored, tokens)
            text_per_nick[nick] = nltk.Text(tokens)

        return text_per_nick

    @staticmethod
    def compute_words_per_nick(log):
        words_per_nick = defaultdict(lambda: defaultdict(int))
        for entry in log.entries:
            words = entry["message"].split()
            words = [word.strip(".") for word in words]
            words = [word.lower() for word in words]

            for word in words:
                words_per_nick[entry["nick"]][word] += 1

        return words_per_nick

    @staticmethod
    def compute_message_count_per_nick(log):
        message_count_per_nick = defaultdict(int)
        for entry in log.entries:
            message_count_per_nick[entry["nick"]] += 1

        return message_count_per_nick

    @staticmethod
    def compute_message_distribution_over_nicks(log, message_count_per_nick):
        message_distribution_over_nicks = defaultdict(float)
        for nick in message_count_per_nick.keys():
            message_distribution_over_nicks[nick] = message_count_per_nick[nick] / len(log.entries)

        return message_distribution_over_nicks

    @staticmethod
    def load_all_bad_words(bad_words_file):
        with open(bad_words_file) as file:
            all_bad_words = [word.strip() for word in file.readlines()]

        return all_bad_words

    @staticmethod
    def compute_bad_words_per_nick(all_bad_words, words_per_nick):
        bad_words_per_nick = defaultdict(lambda: defaultdict(int))

        bad_word_cache = {}

        for nick in words_per_nick.keys():
            for word in words_per_nick[nick].keys():
                if word not in bad_word_cache:
                    bad_word_cache[word] = word in all_bad_words

                if bad_word_cache[word]:
                    bad_words_per_nick[nick][word] += words_per_nick[nick][word]

        return bad_words_per_nick

    @staticmethod
    def compute_bad_word_percentage_per_nick(bad_words_per_nick, words_per_nick):
        bad_word_percentage_per_nick = defaultdict(float)
        for nick in words_per_nick.keys():
            total_word_count = sum([words_per_nick[nick][word] for word in words_per_nick[nick].keys()])
            total_bad_word_count = sum([bad_words_per_nick[nick][word] for word in bad_words_per_nick[nick].keys()])

            if total_word_count > 1000 and total_bad_word_count / total_word_count > 0:
                bad_word_percentage_per_nick[nick] = total_bad_word_count / total_word_count

        return bad_word_percentage_per_nick


def main():
    stats = Stats(Log(filename="../resources/palle_pig.txt"), "../resources/bad-words.txt")


if __name__ == "__main__":
    cProfile.run("main()", sort=1)
    #main()

