import csv
import os


class IncompatibleColumnNamesError(ValueError):
    pass


class CSVWriter:
    def __init__(self, filename: str, columns: list[str], buffer_size: int = 10_000):
        self.buffer_size = buffer_size
        self.filename = filename
        self.rows: list[dict[str, str]] = []
        self.columns = columns

        # if the file already exists, confirm that it has the same columns
        if os.path.isfile(self.filename):
            with open(self.filename, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != self.columns:
                    raise IncompatibleColumnNamesError(f"File {self.filename!r} has different columns than expected.")

    def dict_write_row(self, row: dict[str, str]):
        if set(self.columns) - set(row.keys()):
            raise ValueError(f"Row must contain all columns: {self.columns}")
        row = {k: v for k, v in row.items() if k in self.columns}
        self.rows.append(row)
        if len(self.rows) >= self.buffer_size:
            self.flush()

    def flush(self):
        if not self.rows:
            return
        if not os.path.isfile(self.filename):
            file_dirname = os.path.dirname(self.filename)
            if file_dirname:
                os.makedirs(file_dirname, exist_ok=True)
            with open(self.filename, "w") as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)
                writer.writeheader()

        with open(self.filename, "a") as f:
            csv.DictWriter(f, fieldnames=self.columns).writerows(self.rows)
        self.rows = []
