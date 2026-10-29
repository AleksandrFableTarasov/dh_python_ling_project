"""Анализатор на spaCy: текст -> Sentence.

Чтобы добавить другой вид анализа, напишите новый класс с таким же
методом analyze(text) и подключите его в main.py.
"""

import spacy

from models import Sentence, Token


class SpacyAnalyzer:
    def __init__(self, model_name="ru_core_news_sm"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            raise SystemExit(
                f"Не найдена модель {model_name}. Установите её командой:\n"
                f"  python -m spacy download {model_name}"
            )

    def analyze(self, text):
        doc = self.nlp(text)
        tokens = []
        for t in doc:
            is_root = t.head.i == t.i
            tokens.append(
                Token(
                    tok_id=t.i + 1,
                    form=t.text,
                    lemma=t.lemma_,
                    pos=t.pos_,
                    feats=str(t.morph),
                    head=0 if is_root else t.head.i + 1,
                    deprel=t.dep_,
                )
            )
        return Sentence(text, tokens)
