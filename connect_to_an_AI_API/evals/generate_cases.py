import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOKS = ROOT / "books.json"
CASES = ROOT / "evals" / "cases.json"

random.seed(42)

KEYWORD_MAP = [
    ("poem", "Poetry"),
    ("poetry", "Poetry"),
    ("child", "Children's literature"),
    ("aladdin", "Children's literature"),
    ("picture", "Picture books"),
    ("fairy", "Fairy tales and folklore"),
    ("fantasy", "Fantasy"),
    ("science fiction", "Science fiction"),
    ("mystery", "Mystery"),
    ("history", "History"),
    ("cook", "Food"),
    ("music", "Music"),
    ("romance", "Romance"),
]


def pick_category(text: str) -> str:
    t = text.lower()
    for k, cat in KEYWORD_MAP:
        if k in t:
            return cat
    return "other"


def one_sentence(desc: str) -> str:
    if not desc:
        return ""
    # naive first-sentence extraction
    for sep in (".\n", "\n", ". "):
        if sep in desc:
            return desc.split(sep)[0].strip()[:500]
    return desc.strip().split(".")[0][:500]


def detect_flags(desc: str) -> list:
    flags = []
    if not desc or desc.strip() == "":
        flags.append("missing_description")
    if any(x in desc for x in ["Â", "â", "Ã"]):
        flags.append("encoding_error")
    if len(desc) < 50:
        flags.append("insufficient_information")
    return flags


def main():
    data = json.loads(BOOKS.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("books.json must contain a list of records")

    chosen = random.sample(data, min(8, len(data)))
    cases = []
    for rec in chosen:
        desc = rec.get("description", "")
        expected = {
            "category": pick_category(rec.get("title", "") + " " + desc),
            "summary": one_sentence(desc),
            "quality_flags": detect_flags(desc),
        }
        cases.append({"record": rec, "expected": expected})

    out_path = ROOT / "evals" / "cases.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(cases)} cases to {out_path}")


if __name__ == "__main__":
    main()
