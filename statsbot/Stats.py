from Log import Log
from collections import defaultdict
import operator

class Stats:

    def __init__(self, log):
        self.message_distribution_over_nicks = self.message_distribution_over_nicks(log)

    @staticmethod
    def message_distribution_over_nicks(log):
        messages_per_user = defaultdict(int)
        for entry in log.entries:
            messages_per_user[entry["nick"]] += 1

        message_distribution_over_nicks = defaultdict(float)
        for nick in messages_per_user.keys():
            message_distribution_over_nicks[nick] = messages_per_user[nick] / len(log.entries)

        return message_distribution_over_nicks


if __name__ == "__main__":
    log = Log(filename="../resources/palle_pig.txt")
    stats = Stats(log)

    [print(item) for item
        in reversed(sorted(stats.message_distribution_over_nicks.items(), key=operator.itemgetter(1)))]
