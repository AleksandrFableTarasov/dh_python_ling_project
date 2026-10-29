"""Веб-интерфейс на Streamlit.

Запуск (из папки проекта):  streamlit run app.py
Использует те же классы, что и консольная версия, и ту же папку data.
"""

import base64
import io
import os
import tempfile

import streamlit as st

from analyzer import SpacyAnalyzer
from reader import READERS
from storage import CsvStorage
from visualizer import Visualizer

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_PATH = os.path.join(DATA_DIR, "results.csv")
VISUALS_DIR = os.path.join(DATA_DIR, "visuals")

st.set_page_config(page_title="Разбор русских предложений", layout="wide")


@st.cache_resource(show_spinner="Загрузка модели spaCy...")
def get_analyzer():
    return SpacyAnalyzer()


def show_figure(fig):
    """Показывает картинку в натуральном размере с горизонтальной прокруткой
    (длинные деревья иначе стали бы слишком мелкими)."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=110)
    encoded = base64.b64encode(buffer.getvalue()).decode()
    st.markdown(
        f'<div style="overflow-x:auto"><img src="data:image/png;base64,{encoded}"></div>',
        unsafe_allow_html=True,
    )


def show_sentence(sentence, visualizer):
    """Таблица разбора и три вкладки с визуализациями."""
    st.dataframe(sentence.to_rows(), hide_index=True)
    tab_tree, tab_pos, tab_text = st.tabs(
        ["Дерево зависимостей", "Части речи", "Текстовое дерево"]
    )
    with tab_tree:
        show_figure(visualizer.draw_tree(sentence))
    with tab_pos:
        show_figure(visualizer.draw_pos_chart(sentence))
    with tab_text:
        st.code(sentence.to_tree(), language=None)


# --- режим 1: одно предложение ---
def single_mode(analyzer, visualizer):
    with st.form("single"):
        text = st.text_area("Предложение", placeholder="Например: Я хочу пиццу", height=100)
        save = st.checkbox("Сохранять результат в data (CSV и картинки)", value=True)
        submitted = st.form_submit_button("Разобрать")

    if not submitted:
        return
    text = text.strip()
    if not text:
        st.warning("Введите предложение.")
        return

    storage = CsvStorage(CSV_PATH)
    if save:
        existing_id = storage.find(text)
        if existing_id is not None:
            st.info(f"Предложение уже есть в файле. id = {existing_id}")
            return

    sentence = analyzer.analyze(text)
    if save:
        try:
            sent_id = storage.save(sentence)
            visualizer.save_all(sentence, sent_id)
            st.success(f"Сохранено как предложение №{sent_id}: {CSV_PATH}")
        except PermissionError:
            st.error("Не удалось записать results.csv. Закройте его (например, в Excel) и повторите.")
    show_sentence(sentence, visualizer)


# --- режим 2: CSV-файл ---
def process_file(analyzer, visualizer, reader_class, uploaded, column, limit, save_visuals):
    """Разбирает загруженный файл.

    Возвращает (results, skipped): results — список (sent_id, Sentence) новых
    предложений, skipped — список (id, текст) тех, что уже были в файле.
    При ошибке возвращает (None, [])."""
    # reader работает с путём к файлу, поэтому сохраняем загрузку во временный файл
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = tmp.name
    try:
        options = {"column": column.strip()} if reader_class.needs_column else {}
        reader = reader_class(tmp_path, limit=limit or None, **options)
    except (OSError, ValueError) as error:
        st.error(str(error))
        return None, []
    finally:
        os.remove(tmp_path)

    if len(reader) == 0:
        st.warning("В файле не нашлось предложений.")
        return None, []

    storage = CsvStorage(CSV_PATH)
    progress = st.progress(0.0)
    results, skipped = [], []
    for i, text in enumerate(reader, 1):
        existing_id = storage.find(text)
        if existing_id is not None:
            skipped.append((existing_id, text))
        else:
            sentence = analyzer.analyze(text)
            sent_id = storage.save(sentence)
            if save_visuals:
                visualizer.save_all(sentence, sent_id)
            results.append((sent_id, sentence))
        progress.progress(i / len(reader))
    return results, skipped


def file_mode(analyzer, visualizer):
    key = st.selectbox("Формат файла", list(READERS), format_func=lambda k: READERS[k].title)
    reader_class = READERS[key]
    column = st.text_input("Название колонки с предложениями") if reader_class.needs_column else ""
    uploaded = st.file_uploader("CSV-файл", type=["csv", "txt"])
    limit = int(st.number_input("Сколько предложений разобрать (0 — все)",
                                min_value=0, value=20, step=10))
    save_visuals = st.checkbox("Сохранять картинки для каждого предложения в data/visuals",
                               value=False)

    if st.button("Разобрать файл"):
        if uploaded is None:
            st.warning("Сначала выберите файл.")
        elif reader_class.needs_column and not column.strip():
            st.warning("Укажите название колонки.")
        else:
            try:
                results, skipped = process_file(analyzer, visualizer, reader_class, uploaded,
                                                column, limit, save_visuals)
            except PermissionError:
                st.error("Не удалось записать results.csv. Закройте его (например, в Excel) и повторите.")
                results, skipped = None, []
            if skipped:
                st.info(f"Предложение уже есть в файле: пропущено {len(skipped)}")
                with st.expander("Какие именно"):
                    st.dataframe([{"id": sid, "Предложение": t} for sid, t in skipped],
                                 hide_index=True)
            if results:
                st.session_state["file_results"] = results
                st.success(f"Разобрано новых предложений: {len(results)}. Результаты: {CSV_PATH}")
            elif results is not None:
                st.warning("Новых предложений нет: все уже есть в файле.")

    # результаты хранятся в session_state, чтобы не пропадать при выборе предложения
    results = st.session_state.get("file_results")
    if not results:
        return

    st.subheader("Разобранные предложения")
    st.dataframe(
        [{"№": sid, "Предложение": s.text, "Токенов": len(s)} for sid, s in results],
        hide_index=True,
    )
    index = st.selectbox(
        "Показать разбор предложения",
        range(len(results)),
        format_func=lambda i: f"№{results[i][0]}: {results[i][1].text[:70]}",
    )
    show_sentence(results[index][1], visualizer)

    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "rb") as f:
            st.download_button("Скачать results.csv", f.read(),
                               file_name="results.csv", mime="text/csv")


def main():
    st.title("Морфологический и синтаксический разбор русских предложений")
    try:
        analyzer = get_analyzer()
    except SystemExit as error:  # модель spaCy не установлена
        st.error(str(error))
        st.stop()
    visualizer = Visualizer(VISUALS_DIR)

    mode = st.sidebar.radio("Режим", ["Одно предложение", "CSV-файл"])
    if mode == "Одно предложение":
        single_mode(analyzer, visualizer)
    else:
        file_mode(analyzer, visualizer)


main()
