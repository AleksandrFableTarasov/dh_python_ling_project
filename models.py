"""Модели данных: Token (одно слово/знак) и Sentence (предложение из токенов)."""


class Token:
    """Один токен с морфологическим и синтаксическим разбором."""

    def __init__(self, tok_id, form, lemma, pos, feats, head, deprel):
        self.tok_id = tok_id    # номер в предложении, с 1
        self.form = form        # слово как в тексте
        self.lemma = lemma      # начальная форма
        self.pos = pos          # часть речи (UPOS)
        self.feats = feats      # признаки: Case=Nom|Number=Sing|...
        self.head = head        # номер родителя, 0 для корня
        self.deprel = deprel    # тип синтаксической связи

    def __eq__(self, other):
        if not isinstance(other, Token):
            return NotImplemented
        return (self.form, self.lemma, self.pos, self.feats, self.deprel) == (
            other.form, other.lemma, other.pos, other.feats, other.deprel
        )

    def __repr__(self):
        return f"Token({self.form!r}, {self.pos}, {self.deprel})"


class Sentence:
    """Предложение: исходный текст и список токенов (композиция)."""

    def __init__(self, text, tokens):
        self.text = text
        self.tokens = list(tokens)

    # --- переопределённые методы ---
    def __len__(self):
        return len(self.tokens)

    def __iter__(self):
        return iter(self.tokens)

    def __getitem__(self, index):
        return self.tokens[index]

    def __eq__(self, other):
        if not isinstance(other, Sentence):
            return NotImplemented
        return self.tokens == other.tokens

    def __repr__(self):
        return f"Sentence({self.text!r}, {len(self)} токенов)"

    # --- вывод ---
    def _head_form(self, token):
        return "—" if token.head == 0 else self.tokens[token.head - 1].form

    def to_table(self):
        """Текстовая таблица разбора."""
        header = ("№", "Форма", "Лемма", "Часть речи", "Признаки", "Связь", "Голова")
        rows = [
            (str(t.tok_id), t.form, t.lemma, t.pos, t.feats or "—",
             t.deprel, self._head_form(t))
            for t in self.tokens
        ]
        widths = [max(len(r[i]) for r in [header] + rows) for i in range(len(header))]

        def line(row):
            return "  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip()

        return "\n".join([line(header)] + [line(r) for r in rows])

    def to_tree(self):
        """Дерево зависимостей, нарисованное символами."""
        children = {}
        for t in self.tokens:
            children.setdefault(t.head, []).append(t)

        lines = []

        def walk(token, prefix, is_last, is_root):
            label = f"{token.form} ({token.deprel})"
            if is_root:
                lines.append(label)
                child_prefix = ""
            else:
                lines.append(prefix + ("└── " if is_last else "├── ") + label)
                child_prefix = prefix + ("    " if is_last else "│   ")
            kids = children.get(token.tok_id, [])
            for i, kid in enumerate(kids):
                walk(kid, child_prefix, i == len(kids) - 1, False)

        for root in children.get(0, []):
            walk(root, "", True, True)
        return "\n".join(lines)
