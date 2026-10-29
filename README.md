# Разбор русских предложений

Морфологический и синтаксический разбор русского текста (spaCy, модель `ru_core_news_sm`).
Предложение можно ввести вручную или загрузить CSV (например, выгрузку из НКРЯ).

## Установка

```
pip install spacy matplotlib streamlit
python -m spacy download ru_core_news_sm
```

## Запуск

- Консоль: `python main.py`
- Веб-интерфейс: `python -m streamlit run app.py`

## Результаты

Всё сохраняется в папке `data/` рядом со скриптами:
- `results.csv` — одна строка на токен (лемма, часть речи, признаки, связь, голова);
- `visuals/` — дерево зависимостей и диаграмма частей речи (PNG).

Предложения, которые уже есть в `results.csv`, повторно не разбираются.

## Структура

| Файл | Что делает |
|---|---|
| `models.py` | `Token`, `Sentence` |
| `analyzer.py` | `SpacyAnalyzer`: текст → `Sentence` |
| `reader.py` | `CorpusReader` и его наследники (`RncReader` для НКРЯ, `ColumnCsvReader`) |
| `storage.py` | `CsvStorage`: запись в CSV и проверка дубликатов |
| `visualizer.py` | `Visualizer`: картинки |
| `main.py`, `app.py` | консольный и веб-интерфейс |

Новый корпус добавляется подклассом `CorpusReader` (метод `extract_text`) и записью в словаре `READERS`.
