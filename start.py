from statsbot.Stats import Stats
from statsbot.Log import Log

stats = Stats(Log(filename="resources/log.txt"), "resources/bad-words.txt")


def f(nick):
    with open(nick + ".txt", "w") as file:
        file.write(stats.text_per_nick[nick])


def channel(filename, encoding="latin-1", limit=0):
    long_raw_texts = [text for text in stats.raw_text_per_nick.values() if len(text) > limit]
    shortened_texts = [text[0:10000] for text in long_raw_texts]
    text = "\n".join(shortened_texts)
    with open(filename, "w", encoding=encoding) as f:
        f.write(text)
