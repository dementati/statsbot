from statsbot.Stats import Stats
from statsbot.Log import Log

stats = Stats(Log(filename="resources/palle_pig.txt"), "resources/bad-words.txt")


def f(nick):
    with open(nick + ".txt", "w") as file:
        file.write(stats.nicks[nick].raw_text)


def channel(filename, encoding="latin-1", limit=0):
    long_raw_texts = [stats.nicks[nick].raw_text
                      for nick in stats.nicks.values()
                      if len(stats.nicks[nick].raw_text) > limit]
    shortened_texts = [text[0:10000] for text in long_raw_texts]
    text = "\n".join(shortened_texts)
    with open(filename, "w", encoding=encoding) as f:
        f.write(text)
