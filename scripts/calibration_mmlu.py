#!/usr/bin/env python3
"""Ask local models to answer MMLU questions and say how sure they are.

The run behind the calibration post. Two steps:

    python3 scripts/calibration_mmlu.py sample --parquet /path/to/mmlu/all/test.parquet
    python3 scripts/calibration_mmlu.py run

`sample` draws 1,000 questions from the 14,042 in the MMLU test split (the
`all` config of cais/mmlu on Hugging Face), in proportion to the 57 subjects,
with a fixed seed, and writes them to assets/data/blog/calibration/mmlu-sample.jsonl.
That step needs pyarrow; the sample file is committed so nobody has to repeat it.

`run` sends every question to each model through a local Ollama server at
temperature 0, asking for a JSON object with the answer letter and a confidence
from 0 to 100. One line is appended per call, so a crashed run resumes where
it stopped. Standard library only.

Output files are calikit-ready: `p` is the stated confidence (0 to 100) and `y`
is whether the letter was right, so

    calikit audit assets/data/blog/calibration/llama3.1-8b.jsonl --rescale 0,100 --scheme width

reads them directly.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "data" / "blog" / "calibration"
SAMPLE = OUT / "mmlu-sample.jsonl"

MODELS = ["llama3.1:8b", "qwen2.5:14b", "aya-expanse:8b"]
OLLAMA = "http://localhost:11434/api/generate"
SEED = 0
N = 1000
LETTERS = "ABCD"

PROMPT = """Answer the multiple-choice question.

Question: {question}
A. {a}
B. {b}
C. {c}
D. {d}

Reply with JSON: the letter of your answer and your confidence, as a percentage from 0 to 100, that the answer is correct."""

SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string", "enum": list(LETTERS)},
        "confidence": {"type": "number"},
    },
    "required": ["answer", "confidence"],
}


def make_sample(parquet: Path) -> None:
    import pyarrow.parquet as pq  # only needed for this step

    table = pq.read_table(parquet).to_pylist()
    by_subject: dict[str, list[tuple[int, dict]]] = {}
    for idx, row in enumerate(table):
        by_subject.setdefault(row["subject"], []).append((idx, row))
    total = len(table)
    rng = random.Random(SEED)

    # Proportional allocation, largest remainders, at least one per subject.
    quotas = {s: N * len(rows) / total for s, rows in by_subject.items()}
    counts = {s: max(1, int(q)) for s, q in quotas.items()}
    short = N - sum(counts.values())
    for s in sorted(quotas, key=lambda s: quotas[s] - int(quotas[s]), reverse=True)[:short]:
        counts[s] += 1

    picked = []
    for subject in sorted(by_subject):
        rows = by_subject[subject]
        for idx, row in rng.sample(rows, counts[subject]):
            picked.append({
                "idx": idx,
                "subject": subject,
                "question": row["question"],
                "choices": list(row["choices"]),
                "answer": LETTERS[int(row["answer"])],
            })
    picked.sort(key=lambda r: r["idx"])

    OUT.mkdir(parents=True, exist_ok=True)
    with SAMPLE.open("w", encoding="utf-8") as fh:
        for rec in picked:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"wrote {len(picked)} questions from {len(by_subject)} subjects "
          f"(of {total}) to {SAMPLE.relative_to(ROOT)}")


def ask(model: str, item: dict) -> dict:
    prompt = PROMPT.format(question=item["question"].strip(),
                           a=item["choices"][0], b=item["choices"][1],
                           c=item["choices"][2], d=item["choices"][3])
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": SCHEMA,
        "keep_alive": "30m",
        "options": {"temperature": 0, "seed": SEED, "num_predict": 40},
    }).encode("utf-8")
    req = urllib.request.Request(OLLAMA, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.load(resp)


def parse(raw: str) -> tuple[str | None, float | None, str]:
    """Return (letter, confidence in 0..100, note)."""
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None, None, "not json"
    letter = obj.get("answer")
    if letter not in LETTERS:
        return None, None, f"bad letter {letter!r}"
    conf = obj.get("confidence")
    if isinstance(conf, bool) or not isinstance(conf, (int, float)):
        return letter, None, f"bad confidence {conf!r}"
    conf = float(conf)
    note = ""
    if 0.0 < conf < 1.0:
        # Answered as a fraction despite being asked for a percentage.
        conf, note = conf * 100.0, "fraction rescaled"
    if not 0.0 <= conf <= 100.0:
        return letter, None, f"confidence {conf} out of range"
    return letter, conf, note


def run(models: list[str]) -> None:
    items = [json.loads(line) for line in SAMPLE.read_text(encoding="utf-8").splitlines() if line.strip()]
    for model in models:
        path = OUT / (model.replace(":", "-") + ".jsonl")
        done = set()
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    done.add(json.loads(line)["idx"])
        todo = [it for it in items if it["idx"] not in done]
        print(f"{model}: {len(done)} done, {len(todo)} to go", flush=True)
        started = time.time()
        with path.open("a", encoding="utf-8") as fh:
            for k, item in enumerate(todo, start=1):
                try:
                    resp = ask(model, item)
                except Exception as exc:  # network or server hiccup: note it, move on
                    print(f"  {model} idx {item['idx']}: {exc}", file=sys.stderr, flush=True)
                    time.sleep(5)
                    continue
                raw = resp.get("response", "")
                letter, conf, note = parse(raw)
                rec = {
                    "idx": item["idx"],
                    "subject": item["subject"],
                    "gold": item["answer"],
                    "pred": letter,
                    "p": conf,
                    "y": int(letter == item["answer"]) if letter else None,
                    "note": note,
                    "raw": raw,
                    "prompt_tokens": resp.get("prompt_eval_count"),
                    "output_tokens": resp.get("eval_count"),
                    "ms": int(resp.get("total_duration", 0) / 1e6),
                }
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
                if k % 50 == 0 or k == len(todo):
                    rate = (time.time() - started) / k
                    print(f"  {model}: {k}/{len(todo)}  {rate:.2f}s per item", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample", help="draw the fixed question sample from the MMLU test parquet")
    s.add_argument("--parquet", required=True, type=Path)
    r = sub.add_parser("run", help="query the models over the sample (resumable)")
    r.add_argument("--models", nargs="*", default=MODELS)
    args = ap.parse_args()
    if args.cmd == "sample":
        make_sample(args.parquet)
    else:
        if not SAMPLE.exists():
            raise SystemExit(f"no sample at {SAMPLE}; run the sample step first")
        run(args.models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
