"""Сохранение результатов в CSV: одна строка = один токен."""

import csv
import os

FIELDS = ["sent_id", "sentence", "tok_id", "form", "lemma",
          "pos", "feats", "head", "deprel"]


class CsvStorage:
    def __init__(self, path="data/results.csv"):
        self.path = path
        self._next_id = None  # номер считаем по файлу один раз, дальше увеличиваем
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)

    def _next_sent_id(self):
        if self._next_id is None:
            if not os.path.exists(self.path):
                self._next_id = 1
            else:
                with open(self.path, encoding="utf-8-sig", newline="") as f:
                    ids = [int(row["sent_id"]) for row in csv.DictReader(f)]
                self._next_id = max(ids, default=0) + 1
        return self._next_id

    def save(self, sentence):
        """Дописывает разбор предложения в файл, возвращает его sent_id."""
        sent_id = self._next_sent_id()
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
        self._next_id = sent_id + 1
        return sent_id
