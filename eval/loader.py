"""Loads the corpus ground-truth files.

Deliberately schema-agnostic for now: the files are returned as plain dicts.
Typed models get written on Day 2, once we have looked at the actual shapes
via `make gt-inspect`. Guessing a schema here would just be inventing one.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from eval.config import eval_settings

# Stem -> the extensions it might have been written with.
EXPECTED = [
    "benchmark_questions",
    "benchmark_answers",
    "intentional_conflicts",
    "version_relationships",
    "dependency_map",
    "module_data",
    "abbreviations",
    "document_manifest",
]

SUFFIXES = (".yaml", ".yml", ".json")


def gt_dir() -> Path:
    d = eval_settings.ground_truth_dir
    if not d.exists():
        raise FileNotFoundError(
            f"Ground truth directory not found: {d.resolve()}\n"
            "Set GROUND_TRUTH_DIR in .env to the folder holding benchmark_questions.yaml.\n"
            "It must live OUTSIDE this repository."
        )
    return d


def find(stem: str) -> Path | None:
    for suffix in SUFFIXES:
        candidate = gt_dir() / f"{stem}{suffix}"
        if candidate.exists():
            return candidate
    return None


@lru_cache(maxsize=None)
def load(stem: str) -> Any:
    """Load one ground-truth file by stem, e.g. load('benchmark_questions')."""
    path = find(stem)
    if path is None:
        raise FileNotFoundError(f"No {stem}.(yaml|yml|json) in {gt_dir().resolve()}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def questions() -> Any:
    return load("benchmark_questions")


def answers() -> Any:
    return load("benchmark_answers")
