"""Чтение предложений из CSV-файла (по умолчанию формат выгрузки НКРЯ)."""

import csv


class CorpusReader:
    """Список предложений из колонки CSV. Работает как обычная коллекция."""

    def __init__(self, path, column="Full context", limit=None):
        self.path = path
        self.column = column
        self.sentences = self._load(limit)

    def _load(self, limit):
        for encoding in ("utf-8-sig", "cp1251"):
            try:
                return self._read(encoding, limit)
            except UnicodeDecodeError:
                continue
        raise ValueError("Не удалось прочитать файл: ожидается UTF-8 или Windows-1251")

    def _read(self, encoding, limit):
        with open(self.path, encoding=encoding, newline="") as f:
            header = f.readline()
            # разделитель определяем по строке заголовка (у НКРЯ это «;»)
            delimiter = max(";\t,", key=header.count)
            f.seek(0)
            reader = csv.DictReader(f, delimiter=delimiter)
            if not reader.fieldnames or self.column not in reader.fieldnames:
                cols = ", ".join(reader.fieldnames or [])
                raise ValueError(
                    f"В файле нет колонки «{self.column}». Колонки: {cols}"
                )
            result = []
            for row in reader:
                text = " ".join((row.get(self.column) or "").split())
                if text:
                    result.append(text)
                if limit and len(result) >= limit:
                    break
            return result

    def __len__(self):
        return len(self.sentences)

    def __iter__(self):
        return iter(self.sentences)
