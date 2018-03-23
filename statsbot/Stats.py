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
        self.word_count_per_nick = defaultdict(int)
        self.message_distribution_over_nicks = defaultdict(float)
        self.bad_word_percentage_per_nick = defaultdict(float)
        self.bad_words_per_nick = defaultdict(lambda: defaultdict(int))

        self.calculate_word_count_per_nick(log)
        self.calculate_message_distribution_over_nicks(log)
        self.calculate_on_bad_words(log, self.word_count_per_nick)

    def calculate_word_count_per_nick(self, log):
        for entry in log.entries:
            words = entry["message"].split()
            words = [word.strip(".") for word in words]
            words = [word.lower() for word in words]
            self.word_count_per_nick[entry["nick"]] += len(words)

    def calculate_message_distribution_over_nicks(self, log):
        messages_per_user = defaultdict(int)
        for entry in log.entries:
            messages_per_user[entry["nick"]] += 1

        for nick in messages_per_user.keys():
            self.message_distribution_over_nicks[nick] = messages_per_user[nick] / len(log.entries)

    def calculate_on_bad_words(self, log, word_count_per_nick):
        with open(bad_words_file) as file:
            all_bad_words = [word.strip() for word in file.readlines()]

        bad_word_count_per_nick = defaultdict(int)

        for entry in log.entries:
            # Words
            words = entry["message"].split()
            words = [word.strip(".") for word in words]
            words = [word.lower() for word in words]
            bad_words = [word for word in words if word in all_bad_words]

            for word in bad_words:
                self.bad_words_per_nick[entry["nick"]][word] += 1

            bad_word_count_per_nick[entry["nick"]] += len(bad_words)

        for nick in bad_word_count_per_nick.keys():
            if word_count_per_nick[nick] > 1000 and bad_word_count_per_nick[nick] / word_count_per_nick[nick] > 0:
                self.bad_word_percentage_per_nick[nick] = bad_word_count_per_nick[nick] / word_count_per_nick[nick]


if __name__ == "__main__":
    stats = Stats(Log(filename="../resources/palle_pig.txt"))

    bad_word_count = descending_map(stats.bad_word_percentage_per_nick)

    for i in range(10):
        nick, percentage = bad_word_count[i]

        print("Foulmouth #%d: %s, percentage: %f%%" % (i+1, nick, percentage*100))

        print_list(descending_map(stats.bad_words_per_nick[nick])[0:10])
