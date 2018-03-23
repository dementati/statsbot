from statsbot.Stats import Stats
from statsbot.Log import Log
from nltk import FreqDist

stats = Stats(Log(filename="resources/palle_pig.txt"), "resources/bad-words.txt")