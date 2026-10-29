"""Сохранение результатов в CSV: одна строка = один токен."""

import csv
import os

FIELDS = ["sent_id", "sentence", "tok_id", "form", "lemma",
          "pos", "feats", "head", "deprel"]


class CsvStorage:
    def __init__(self, path="data/results.csv"):
        self.path = path
        self._known = None   # текст предложения -> sent_id (читается из файла один раз)
        self._next_id = 1
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)

    @staticmethod
    def _key(text):
        """Ключ для сравнения: текст без лишних пробелов."""
        return " ".join(text.split())

    def _load(self):
        """Один раз читает файл: запоминает уже разобранные предложения."""
        if self._known is not None:
            return
        self._known = {}
        last_id = 0
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    if not row.get("sent_id"):
                        continue
                    sent_id = int(row["sent_id"])
                    last_id = max(last_id, sent_id)
                    self._known.setdefault(self._key(row["sentence"]), sent_id)
        self._next_id = last_id + 1

    def find(self, text):
        """Возвращает sent_id, если такое предложение уже есть в файле, иначе None."""
        self._load()
        return self._known.get(self._key(text))

    def save(self, sentence):
        """Дописывает разбор предложения в файл, возвращает его sent_id."""
        self._load()
        sent_id = self._next_id
        new_file = not os.path.exists(self.path)
        # utf-8-sig, чтобы Excel правильно открывал кириллицу
        with open(self.path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(FIELDS)
            for t in sentence:
                writer.writerow([sent_id, sentence.text, t.tok_id, t.form,
                                 t.lemma, t.pos, t.feats, t.head, t.deprel])
            writer.writerow([])  # пустая строка-разделитель между предложениями
        self._known.setdefault(self._key(sentence.text), sent_id)
        self._next_id = sent_id + 1
        return sent_id
