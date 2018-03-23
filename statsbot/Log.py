import re

encodings = ["utf8", "latin_1"]

class Log:

    def __init__(self, **kwargs):
        self.clear()

        if "filename" in kwargs:
            if not self.parse_file(kwargs["filename"]):
                success = False
                for encoding in encodings:
                    if self.parse_file(kwargs["filename"], encoding):
                        success = True
                        break

                if not success:
                    raise Exception("Couldn't parse file: " + kwargs["filename"])

        elif "line" in kwargs:
            self.entries = [self.parse(kwargs["line"])]

        self.entries = [entry for entry in self.entries if entry]

    def parse_file(self, filename, encoding=None):
        try:
            self.clear()

            if encoding:
                file = open(filename, encoding=encoding)
            else:
                file = open(filename)

            self.entries = [self.parse(line) for line in file.readlines()]
            return True
        except UnicodeDecodeError:
            return False

    def clear(self):
        self.unparsed = []
        self.entries = []

    def parse(self, line):
        m = re.match("^(\S*)\s<([^>]*)> (.*)$", line)

        if not m:
            self.unparsed.append(line)
            return None

        if len(m.groups()) != 3:
            self.unparsed.append(line)
            return None

        return {"timestamp" : m.groups()[0], "nick" : m.groups()[1].strip(), "message" : m.groups()[2]}

    def __str__(self):
        return str(self.entries)


if __name__ == "__main__":
    log = Log(line="[00:04] <rosvi> I have a linux box I'm gonna install arch a windows box. Not bootable media. Would it be possible to installa distro on those circumstances? Just wondering about it")
    log = Log(filename="../resources/#ubuntu.txt")
    log = Log(filename="../resources/log.txt")
    log = Log(filename="../resources/palle_pig.txt")