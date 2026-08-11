import json
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases.json"
RESP_DIR = ROOT / "evals" / "responses"


def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a or "", b or "").ratio()


def main():
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    total = len(cases)
    category_matches = 0

    for i, case in enumerate(cases):
        expected = case["expected"]
        resp_path = RESP_DIR / f"response_{i}.json"
        if not resp_path.exists():
            print(f"[{i}] missing response file: {resp_path}")
            continue
        try:
            actual = json.loads(resp_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[{i}] failed to parse response JSON: {exc}")
            continue

        exp_cat = expected.get("category")
        act_cat = actual.get("category")
        cat_ok = exp_cat == act_cat
        if cat_ok:
            category_matches += 1

        exp_sum = expected.get("summary") or ""
        act_sum = actual.get("summary") or ""
        sim = similar(exp_sum, act_sum)

        exp_flags = set(expected.get("quality_flags", []))
        act_flags = set(actual.get("quality_flags", []))

        print(f"[{i}] Category expected: {exp_cat!r} actual: {act_cat!r} -> {'OK' if cat_ok else 'MISMATCH'}")
        print(f"    Summary similarity: {sim:.2f}")
        print(f"    Expected summary: {exp_sum}")
        print(f"    Actual summary:   {act_sum}")
        print(f"    Expected flags: {sorted(exp_flags)}")
        print(f"    Actual flags:   {sorted(act_flags)}")
        print("")

    print(f"Summary: {category_matches}/{total} categories matched exactly.")


if __name__ == "__main__":
    main()
