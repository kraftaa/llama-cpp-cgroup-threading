#!/usr/bin/env python3
"""Apply the investigation's narrow stop/go criteria to a fresh Linux run."""

import csv
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESULTS = Path(os.environ.get("RESULTS_DIR", ROOT / "results"))
SUMMARY = RESULTS / "summary.csv"
VERDICT = RESULTS / "ci-verdict.md"


with SUMMARY.open(newline="") as handle:
    rows = list(csv.DictReader(handle))


def find(image, cpus, requested, test):
    matches = [
        row
        for row in rows
        if row["image"] == image
        and row["cpus"] == cpus
        and row["threads_requested"] == requested
        and row["test"] == test
        and row["cgroup_namespace"] == "private"
        and row["cpuset"] == "all"
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected one row for {image}, CPUs={cpus}, threads={requested}, "
            f"test={test}; found {len(matches)}"
        )
    return matches[0]


selection_cases = [
    ("PR parent at 1 CPU", "llama-cgroup:pr-parent", "1", "default", None),
    ("PR at 1 CPU", "llama-cgroup:pr", "1", "default", 1),
    ("PR at 1.5 CPUs", "llama-cgroup:pr", "1.5", "default", 1),
    ("explicit override", "llama-cgroup:pr", "1.5", "2", 2),
    ("follow-up at 0.5 CPU", "llama-cgroup:pr-fractional", "0.5", "default", 1),
    ("follow-up at 1 CPU", "llama-cgroup:pr-fractional", "1", "default", 1),
    ("follow-up at 1.5 CPUs", "llama-cgroup:pr-fractional", "1.5", "default", 2),
    ("follow-up at 2 CPUs", "llama-cgroup:pr-fractional", "2", "default", 2),
]

failures = []
selection_lines = []
for label, image, cpus, requested, expected in selection_cases:
    row = find(image, cpus, requested, "tg64")
    used = int(row["threads_used"])
    if expected is None:
        passed = used > 1
        expectation = ">1 (reproduces the old oversubscription default)"
    else:
        passed = used == expected
        expectation = str(expected)
    selection_lines.append(
        f"| {label} | {requested} | {used} | {expectation} | "
        f"{'PASS' if passed else 'FAIL'} |"
    )
    if not passed:
        failures.append(f"{label}: used {used}, expected {expectation}")


def median(image, cpus, requested, test):
    return float(find(image, cpus, requested, test)["median_tps"])


performance_lines = []
gains = {}
for test in ("pp128", "tg64"):
    floor = median("llama-cgroup:pr", "1.5", "default", test)
    explicit = median("llama-cgroup:pr", "1.5", "2", test)
    fixed = median("llama-cgroup:pr-fractional", "1.5", "default", test)
    gain = 100.0 * (fixed / floor - 1.0)
    delta_from_explicit = 100.0 * (fixed / explicit - 1.0)
    gains[test] = gain
    performance_lines.append(
        f"| {test} | {floor:.2f} | {explicit:.2f} | {fixed:.2f} | "
        f"{gain:+.1f}% | {delta_from_explicit:+.1f}% |"
    )

# A new Linux host supports the contribution only if the ceil selection is
# correct and produces a meaningful gain in at least one workload. This is a
# research stop/go threshold, not a stable performance assertion for upstream CI.
meaningful_gain = max(gains.values()) >= 5.0
if not meaningful_gain:
    failures.append(
        "the 1.5-CPU follow-up improved neither workload by at least 5%; "
        "do not make a cross-host performance claim"
    )

verdict = "GO — independent Linux evidence supports the focused follow-up" if not failures else "STOP — the public-run evidence does not support contribution yet"
report = f"""# GitHub-hosted Linux verification

## Verdict

**{verdict}.**

## Thread selection

| Case | Requested | Used | Expected | Result |
|---|---:|---:|---:|---|
{chr(10).join(selection_lines)}

## Fractional-quota performance

All values are median tokens/second. “Patched vs explicit” is a consistency
check, not an assertion that the two independent runs must be identical.

| Workload | PR floor default | PR explicit 2 | Follow-up default | Follow-up gain | Patched vs explicit |
|---|---:|---:|---:|---:|---:|
{chr(10).join(performance_lines)}

## Gate

- Required selections must match the pinned code behavior.
- The follow-up must improve at least one 1.5-CPU workload by 5% or more.
- This gate is intentionally host-specific research evidence. It is not suitable
  as a general llama.cpp performance test.
"""

if failures:
    report += "\n## Failures\n\n" + "\n".join(f"- {failure}" for failure in failures) + "\n"

RESULTS.mkdir(parents=True, exist_ok=True)
VERDICT.write_text(report)
print(report)
sys.exit(1 if failures else 0)
