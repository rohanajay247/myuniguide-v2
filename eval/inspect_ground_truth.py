"""Prints the shape of every ground-truth file so we can write typed models against
the real structure instead of a guessed one.

Usage:
    uv run python -m eval.inspect_ground_truth
"""

from typing import Any

from eval.loader import EXPECTED, find, gt_dir, load


def describe(name: str, obj: Any, indent: int = 2) -> None:
    pad = " " * indent
    if isinstance(obj, dict):
        print(f"{pad}{name}: dict with {len(obj)} keys")
        for k in list(obj)[:12]:
            v = obj[k]
            kind = type(v).__name__
            extra = f" (len {len(v)})" if isinstance(v, (list, dict)) else ""
            print(f"{pad}  - {k}: {kind}{extra}")
        if len(obj) > 12:
            print(f"{pad}  ... {len(obj) - 12} more")
    elif isinstance(obj, list):
        print(f"{pad}{name}: list of {len(obj)}")
        if obj and isinstance(obj[0], dict):
            print(f"{pad}  first item keys: {list(obj[0])}")
            print(f"{pad}  first item: {obj[0]}")
    else:
        print(f"{pad}{name}: {type(obj).__name__}")


def main() -> None:
    print(f"Ground truth: {gt_dir().resolve()}\n")

    missing = []
    for stem in EXPECTED:
        path = find(stem)
        if path is None:
            missing.append(stem)
            print(f"[MISSING] {stem}")
            continue
        print(f"[ok] {path.name}")
        try:
            describe(stem, load(stem))
        except Exception as exc:  # noqa: BLE001
            print(f"  could not parse: {exc}")
        print()

    if missing:
        print(f"Missing files: {', '.join(missing)}")

    try:
        q = load("benchmark_questions")
        items = q if isinstance(q, list) else next(
            (v for v in q.values() if isinstance(v, list)), []
        )
        print(f"\nQuestion count: {len(items)}  (expected 72)")
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    main()
