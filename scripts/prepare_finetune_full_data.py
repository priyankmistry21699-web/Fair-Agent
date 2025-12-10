import json
import random
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FINETUNE_DIR = PROJECT_ROOT / "data" / "finetune"
FINETUNE_DIR.mkdir(parents=True, exist_ok=True)

SEED_PATH = FINETUNE_DIR / "qa_med_fin_seed.jsonl"
FULL_PATH = FINETUNE_DIR / "qa_med_fin_full.jsonl"
TRAIN_PATH = FINETUNE_DIR / "qa_med_fin_train.jsonl"
VAL_PATH = FINETUNE_DIR / "qa_med_fin_val.jsonl"


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_full_dataset() -> list[dict]:
    """Build the full med/fin/cross-domain dataset.

    For now this simply mirrors the seed file so you have a
    single place to grow the dataset. Later you can append
    additional curated examples here or edit qa_med_fin_full.jsonl
    directly.
    """

    seed_rows = _read_jsonl(SEED_PATH)

    # If a manual full file already exists with extra examples,
    # prefer that file so you can grow it over time.
    manual_full = _read_jsonl(FULL_PATH)
    if manual_full:
        return manual_full

    return seed_rows


def split_train_val(rows: list[dict], val_ratio: float = 0.2) -> tuple[list[dict], list[dict]]:
    if not rows:
        return [], []

    rows = list(rows)
    random.shuffle(rows)
    n_total = len(rows)
    n_val = max(1, int(n_total * val_ratio)) if n_total > 1 else 0

    if n_val == 0:
        return rows, []

    val_rows = rows[:n_val]
    train_rows = rows[n_val:]
    if not train_rows:
        train_rows, val_rows = val_rows, []
    return train_rows, val_rows


def main() -> None:
    rows = build_full_dataset()
    if not rows:
        print("No examples found in seed or full dataset; nothing to do.")
        return

    _write_jsonl(FULL_PATH, rows)

    train_rows, val_rows = split_train_val(rows, val_ratio=0.2)

    _write_jsonl(TRAIN_PATH, train_rows)
    _write_jsonl(VAL_PATH, val_rows)

    print(f"Total examples: {len(rows)}")
    print(f"Train examples: {len(train_rows)} -> {TRAIN_PATH}")
    print(f"Val examples:   {len(val_rows)} -> {VAL_PATH}")


if __name__ == "__main__":
    main()
