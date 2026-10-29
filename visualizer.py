"""Визуализации: дерево зависимостей со стрелками и диаграмма частей речи.

Картинки сохраняются в data/visuals под именем вида
    <номер>_<начало_предложения>_tree.png
    <номер>_<начало_предложения>_pos.png
Номер совпадает с sent_id в results.csv.
"""

import os
import re
from collections import Counter

from matplotlib.figure import Figure
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.ticker import MaxNLocator


class Visualizer:
    def __init__(self, out_dir="data/visuals", fmt="png"):
        self.out_dir = out_dir
        self.fmt = fmt  # можно поставить "svg"
        os.makedirs(out_dir, exist_ok=True)

    # --- имена файлов ---
    @staticmethod
    def make_slug(text, max_len=40):
        """Безопасная для имени файла версия начала предложения."""
        slug = re.sub(r"[\W_]+", "_", text).strip("_")[:max_len].strip("_")
        return slug or "sentence"

    def _path(self, sent_id, sentence, kind):
        name = f"{sent_id}_{self.make_slug(sentence.text)}_{kind}.{self.fmt}"
        return os.path.join(self.out_dir, name)

    # --- дерево зависимостей ---
    def save_tree(self, sentence, sent_id):
        tokens = list(sentence)

        # Центры слов по оси x (1 единица = 1 дюйм)
        centers, x = [], 0.2
        for t in tokens:
            w = max(0.7, 0.115 * len(t.form) + 0.35)
            centers.append(x + w / 2)
            x += w
        width = max(x + 0.2, 3.0)

        spans = [abs(t.head - t.tok_id) for t in tokens if t.head]
        max_h = max(0.5 + 0.32 * max(spans, default=0), 0.9)
        top = 0.75 * max_h + 0.6  # самая высокая точка дуги = 0.75 * h

        fig = Figure(figsize=(width, top + 1.0))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, width)
        ax.set_ylim(-1.0, top)
        ax.axis("off")

        arrow = dict(arrowstyle="-|>", lw=1, color="black",
                     shrinkA=0, shrinkB=0, mutation_scale=9)

        for t, xd in zip(tokens, centers):
            # слово и часть речи под ним
            ax.text(xd, -0.12, t.form, ha="center", va="top", fontsize=11)
            ax.text(xd, -0.52, t.pos, ha="center", va="top",
                    fontsize=8, color="gray")

            if t.head == 0:
                # корень предложения: стрелка сверху
                ax.annotate("", xy=(xd, 0), xytext=(xd, 0.75), arrowprops=arrow)
                ax.text(xd, 0.8, t.deprel, ha="center", va="bottom", fontsize=8)
                continue

            xh = centers[t.head - 1]
            sign = 1 if xd > xh else -1
            xs = xh + 0.12 * sign   # начало дуги у родителя
            xe = xd - 0.08 * sign   # конец дуги у зависимого слова
            h = 0.5 + 0.32 * abs(t.head - t.tok_id)

            curve = Path(
                [(xs, 0), (xs, h), (xe, h), (xe, 0)],
                [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4],
            )
            ax.add_patch(PathPatch(curve, fc="none", ec="black", lw=1))
            ax.annotate("", xy=(xe, 0), xytext=(xe, 0.12), arrowprops=arrow)
            ax.text((xs + xe) / 2, 0.75 * h, t.deprel, ha="center", va="center",
                    fontsize=8, zorder=3,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))

        path = self._path(sent_id, sentence, "tree")
        fig.savefig(path, dpi=130)
        return path

    # --- диаграмма частей речи ---
    def save_pos_chart(self, sentence, sent_id):
        counts = Counter(t.pos for t in sentence)
        labels, values = zip(*counts.most_common())

        fig = Figure(figsize=(max(4.0, 0.8 * len(labels) + 1.5), 3.6))
        ax = fig.add_subplot(111)
        bars = ax.bar(labels, values, color="#4C72B0")
        ax.bar_label(bars)
        ax.set_ylabel("Число токенов")
        ax.set_ylim(0, max(values) + 1)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        short = sentence.text if len(sentence.text) <= 50 else sentence.text[:50] + "…"
        ax.set_title(f"Части речи: {short}", fontsize=10)
        fig.tight_layout()

        path = self._path(sent_id, sentence, "pos")
        fig.savefig(path, dpi=130)
        return path

    def save_all(self, sentence, sent_id):
        """Сохраняет обе картинки, возвращает список путей."""
        return [self.save_tree(sentence, sent_id),
                self.save_pos_chart(sentence, sent_id)]
