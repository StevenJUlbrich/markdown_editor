# ──────────────────────────────────────────────────────────────────────────────
# File: src/utils/theme_bubble.py
# ──────────────────────────────────────────────────────────────────────────────
from collections import Counter
from typing import List

from models.document_model import ChapterPydantic
from models.document_model import PanelPydantic

ALLOWED_THEMES = ["Chaos", "Teaching", "Reflection", "Planning", "Celebration"]


def bubble_scene_themes_to_chapter(chapter: ChapterPydantic) -> None:  # noqa: ANN001 – method mutates in‑place
    """Aggregates `panel.scene_theme` strings and stores counts + percentage on the chapter.

    Adds/updates two attributes:
      * `theme_counts`: `dict[str, int]`
      * `theme_percent`: `dict[str, float]` (0‑100, rounded 2)
    """
    themes: List[str] = [getattr(p, "scene_theme", None) or "Unknown" for p in chapter.panels]
    counts = Counter(themes)
    total = sum(counts.values()) or 1
    chapter.theme_counts = {t: counts.get(t, 0) for t in ALLOWED_THEMES}
    chapter.theme_percent = {t: round(counts.get(t, 0) * 100 / total, 2) for t in ALLOWED_THEMES}


# ──────────────────────────────────────────────────────────────────────────────
# Usage examples (to be placed where OpenAI wrappers live)
# ──────────────────────────────────────────────────────────────────────────────
# from services.openai_tracing import trace_openai_call
#
# @trace_openai_call(prompt_name="scene_theme")
# def suggest_scene_theme(panel_text: str, panel_id: int):
#     ...  # existing implementation
#
# After processing a chapter:
# from utils.theme_bubble import bubble_scene_themes_to_chapter
# bubble_scene_themes_to_chapter(chapter_obj)
