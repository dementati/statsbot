from statsbot.Stats import Stats
from statsbot.Log import Log

stats = Stats(Log(filename="resources/palle_pig.txt"), "resources/bad-words.txt")


def f(nick):
    with open(nick + ".txt", "w") as file:
        file.write(stats.text_per_nick[nick])

