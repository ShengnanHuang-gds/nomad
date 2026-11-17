"""Small CSV sink: flush each row so interrupted runs retain diagnostics."""

import csv
from pathlib import Path


class CsvLog:
    def __init__(self, path):
        self.path = path
        self.file = None
        self.writer = None

    def write(self, row):
        if not self.path:
            return
        if self.file is None:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            self.file = open(self.path, "w", newline="", encoding="utf-8")
            self.writer = csv.DictWriter(self.file, fieldnames=list(row))
            self.writer.writeheader()
        self.writer.writerow(row)
        self.file.flush()

    def close(self):
        if self.file is not None:
            self.file.close()
