"""Консольный анализатор русских предложений.

Запуск:  python main.py
Режимы: ввод с клавиатуры или разбор CSV-файла (например, выгрузки НКРЯ).
"""

import os

from analyzer import SpacyAnalyzer
from reader import CorpusReader
from storage import CsvStorage
from visualizer import Visualizer

MENU = """
Выберите режим:
  1 — ввести предложение с клавиатуры
  2 — разобрать CSV-файл (например, выгрузку из НКРЯ)
  0 — выход"""


def analyze_and_save(text, analyzer, storage, visualizer, with_visuals):
    """Разбирает текст, пишет в CSV, при необходимости рисует картинки."""
    sentence = analyzer.analyze(text)
    sent_id = storage.save(sentence)
    paths = visualizer.save_all(sentence, sent_id) if with_visuals else []
    return sentence, sent_id, paths


def keyboard_mode(analyzer, storage, visualizer):
    print("\nВведите предложение (пустая строка или «выход» — назад в меню).")
    while True:
        text = input("\n> ").strip()
        if not text or text.lower() in ("выход", "exit", "quit"):
            return

        sentence, sent_id, paths = analyze_and_save(
            text, analyzer, storage, visualizer, with_visuals=True
        )
        print()
        print(sentence.to_table())
        print()
        print(sentence.to_tree())
        print(f"\nСохранено: {os.path.abspath(storage.path)} (предложение №{sent_id})")
        for p in paths:
            print(f"Картинка: {os.path.abspath(p)}")


def file_mode(analyzer, storage, visualizer):
    path = input("\nПуть к CSV-файлу (Enter — назад): ").strip().strip("\"'")
    if not path:
        return
    column = input("Колонка с предложениями [Full context]: ").strip() or "Full context"
    limit_raw = input("Сколько предложений разобрать? [Enter — все]: ").strip()
    limit = int(limit_raw) if limit_raw.isdigit() and int(limit_raw) > 0 else None
    answer = input("Сохранять картинки для каждого предложения? (д/н) [н]: ")
    with_visuals = answer.strip().lower() in ("д", "да", "y", "yes")

    try:
        reader = CorpusReader(path, column, limit)
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}")
        return

    total = len(reader)
    if total == 0:
        print("В файле не нашлось предложений.")
        return

    for i, text in enumerate(reader, 1):
        _, sent_id, _ = analyze_and_save(text, analyzer, storage, visualizer, with_visuals)
        short = text if len(text) <= 60 else text[:60] + "…"
        print(f"[{i}/{total}] №{sent_id}: {short}")

    print(f"\nГотово: разобрано {total} предложений.")
    print(f"Результаты: {os.path.abspath(storage.path)}")
    if with_visuals:
        print(f"Картинки: {os.path.abspath(visualizer.out_dir)}")


def main():
    print("Загрузка модели...")
    analyzer = SpacyAnalyzer()
    storage = CsvStorage("data/results.csv")
    visualizer = Visualizer("data/visuals")

    while True:
        print(MENU)
        choice = input("> ").strip().lower()
        try:
            if choice == "1":
                keyboard_mode(analyzer, storage, visualizer)
            elif choice == "2":
                file_mode(analyzer, storage, visualizer)
            elif choice in ("0", "выход", "exit", "quit"):
                break
            else:
                print("Введите 1, 2 или 0.")
        except PermissionError:
            print("Не удалось записать файл. Закройте results.csv (например, в Excel) и повторите.")


if __name__ == "__main__":
    main()
