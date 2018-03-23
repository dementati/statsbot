from Log import Log
from collections import defaultdict
import operator

bad_words_file = "../resources/bad-words.txt"


def descending_map(map):
    return [item for item in reversed(sorted(map.items(), key=operator.itemgetter(1)))]


def print_list(list):
    [print(item) for item in list]


class Stats:

    def __init__(self, log):
        self.all_bad_words = self.load_all_bad_words()
        self.words_per_nick = self.compute_words_per_nick(log)
        self.message_count_per_nick = self.compute_message_count_per_nick(log)
        self.message_distribution_over_nicks = \
            self.compute_message_distribution_over_nicks(log, self.message_count_per_nick)
        self.bad_words_per_nick = self.compute_bad_words_per_nick(self.all_bad_words, self.words_per_nick)
        self.bad_word_percentage_per_nick = \
            self.compute_bad_word_percentage_per_nick(self.all_bad_words, self.words_per_nick)


    @staticmethod
    def compute_words_per_nick(log):
        words_per_nick = defaultdict(list)
        for entry in log.entries:
            words = entry["message"].split()
            words = [word.strip(".") for word in words]
            words = [word.lower() for word in words]
            words_per_nick[entry["nick"]].extend(words)

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
    def load_all_bad_words():
        with open(bad_words_file) as file:
            all_bad_words = [word.strip() for word in file.readlines()]

        return all_bad_words

    @staticmethod
    def compute_bad_words_per_nick(all_bad_words, words_per_nick):
        bad_words_per_nick = defaultdict(lambda: defaultdict(int))

        for nick in words_per_nick.keys():
            bad_words = [word for word in words_per_nick[nick] if word in all_bad_words]

            for word in bad_words:
                bad_words_per_nick[nick][word] += 1

        return bad_words_per_nick

    @staticmethod
    def compute_bad_word_percentage_per_nick(all_bad_words, words_per_nick):
        bad_word_percentage_per_nick = defaultdict(float)
        for nick in words_per_nick.keys():
            bad_words = [word for word in words_per_nick[nick] if word in all_bad_words]
            bad_word_count = len(bad_words)

            if len(words_per_nick[nick]) > 1000 and bad_word_count / len(words_per_nick[nick]) > 0:
                bad_word_percentage_per_nick[nick] = bad_word_count / len(words_per_nick[nick])

        return bad_word_percentage_per_nick


def main():
    stats = Stats(Log(filename="../resources/palle_pig.txt"))

    bad_word_count = descending_map(stats.bad_word_percentage_per_nick)

    for i in range(10):
        nick, percentage = bad_word_count[i]

        print("Foulmouth #%d: %s, percentage: %f%%" % (i + 1, nick, percentage * 100))

        print_list(descending_map(stats.bad_words_per_nick[nick])[0:10])


if __name__ == "__main__":
    main()
