"""Чтение предложений из CSV-файлов корпусов.

CorpusReader — базовый класс: умеет открывать CSV (кодировка, разделитель,
лимит, очистка пробелов). Что именно считать предложением в строке файла,
решает наследник в методе extract_text.

Чтобы добавить csv парсер для csv файла из другого корпуса:
    1. написать подкласс CorpusReader с extract_text (и required_columns);
    2. добавить его в словарь READERS внизу файла.
"""

import csv


class CorpusReader:
    """Базовый класс. Работает как коллекция предложений (len, for)."""

    title = "Корпус"          # название для меню
    needs_column = False      # нужно ли спрашивать у пользователя колонку
    required_columns = ()     # колонки, без которых файл не подходит

    def __init__(self, path, limit=None):
        self.path = path
        self.sentences = self._load(limit)

    def extract_text(self, row):
        """Достаёт текст предложения из строки (словаря). Реализует наследник."""
        raise NotImplementedError("Подкласс должен реализовать extract_text")

    # --- общая часть для всех корпусов ---
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
            fields = reader.fieldnames or []
            missing = [c for c in self.required_columns if c not in fields]
            if missing:
                raise ValueError(
                    f"Для формата «{self.title}» в файле нет колонки «{missing[0]}». "
                    f"Колонки в файле: {', '.join(fields)}"
                )
            result = []
            for row in reader:
                text = " ".join((self.extract_text(row) or "").split())
                if text:
                    result.append(text)
                if limit and len(result) >= limit:
                    break
            return result

    def __len__(self):
        return len(self.sentences)

    def __iter__(self):
        return iter(self.sentences)


class RncReader(CorpusReader):
    """Выгрузка из Национального корпуса русского языка (НКРЯ)."""

    title = "НКРЯ (Национальный корпус русского языка)"
    required_columns = ("Full context",)

    def extract_text(self, row):
        return row["Full context"]


class ColumnCsvReader(CorpusReader):
    """Любой CSV: предложения лежат в колонке, которую выбирает пользователь."""

    title = "Другой корпус"
    needs_column = True

    def __init__(self, path, limit=None, column=""):
        self.column = column
        self.required_columns = (column,)
        super().__init__(path, limit)

    def extract_text(self, row):
        return row[self.column]


# Реестр форматов: ключ -> класс. Сюда добавляются новые корпуса.
READERS = {
    "rnc": RncReader,
    "csv": ColumnCsvReader,
}
