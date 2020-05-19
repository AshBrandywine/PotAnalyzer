

class BatchWriter:
    filename = ""
    written_hashes = set()
    batch = []
    batch_size = 1000000

    def __init__(self, filename):
        file = open(filename, 'w')
        file.close()
        self.filename = filename

    def add_line(self, line):
        line_hash = hash(line)
        if line_hash not in self.written_hashes:
            self.written_hashes.add(line_hash)
            self.batch.append(line)
            if len(self.batch) >= self.batch_size:
                self.commit()

    def add_many_lines(self, many_lines):
        for line in many_lines:
            self.add_line(line)

    def commit(self):
        with open(self.filename, 'a') as outfile:
            for line in self.batch:
                outfile.write(line + '\n')
        self.batch.clear()

    def unique_line_count(self):
        return len(self.written_hashes)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.commit()

