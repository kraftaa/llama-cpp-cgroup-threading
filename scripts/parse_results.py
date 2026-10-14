#!/usr/bin/env python3
"""Convert preserved llama-bench JSONL/log metadata into tidy CSV files."""

import csv
import json
import os
import shlex
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESULTS = Path(os.environ.get("RESULTS_DIR", ROOT / "results"))
RAW = RESULTS / "raw"
RUNS = RESULTS / "runs.csv"
SUMMARY = RESULTS / "summary.csv"

COMMITS = {
    "llama-cgroup:issue-baseline": "11fe02151f79c41d0d4af7da708755d73b9c0da6",
    "llama-cgroup:pr-parent": "10a60cf303566e10d6a7a2774c17d2085503d87b",
    "llama-cgroup:pr": "a9672dd07ac5e98768f94fda11b6cb549c2eb744",
    "llama-cgroup:pr-fractional": "d9ae21d39ad086270c399dbe7d386cb6be87b228",
}


def parse_log(path):
    meta = {}
    before = {}
    after = {}
    results = []

    for raw in path.read_text(errors="replace").splitlines():
        if raw.startswith("META "):
            content = raw[5:]
            if ":" in content and "=" not in content.split(":", 1)[0]:
                key, value = content.split(":", 1)
                meta[key.strip()] = value.strip()
                continue
            for token in shlex.split(content):
                if "=" in token:
                    key, value = token.split("=", 1)
                    meta[key] = value
        elif raw.startswith("STAT_BEFORE "):
            key, value = raw[12:].split(None, 1)
            before[key] = int(value)
        elif raw.startswith("STAT_AFTER "):
            key, value = raw[11:].split(None, 1)
            after[key] = int(value)
        elif raw.startswith("{"):
            results.append(json.loads(raw))

    if meta.get("exit_status") != "0" or len(results) != 2:
        return []

    deltas = {
        key: after.get(key, 0) - before.get(key, 0)
        for key in set(before) | set(after)
    }
    periods = deltas.get("nr_periods", 0)
    throttled = deltas.get("nr_throttled", 0)

    rows = []
    for result in results:
        test = "pp128" if result["n_prompt"] else "tg64"
        for index, (sample_ns, sample_tps) in enumerate(
            zip(result["samples_ns"], result["samples_ts"]), start=1
        ):
            rows.append(
                {
                    "run_id": path.stem,
                    "image": meta["image"],
                    "commit": COMMITS[meta["image"]],
                    "cpus": meta["cpus"],
                    "cgroup_namespace": meta["cgroupns"],
                    "cpuset": meta["cpuset"],
                    "threads_requested": meta["threads_requested"],
                    "threads_used": result["n_threads"],
                    "test": test,
                    "sample": index,
                    "sample_ns": sample_ns,
                    "tokens_per_second": sample_tps,
                    "backend": result["backends"],
                    "gpu_info": result["gpu_info"],
                    "n_gpu_layers": result["n_gpu_layers"],
                    "cpu_max_root": meta.get("root_cpu_max", ""),
                    "cpu_max_effective": meta.get("effective_cpu_max", ""),
                    "cpus_allowed_list": meta.get("Cpus_allowed_list", ""),
                    "effective_cpuset": meta.get("effective_cpuset", ""),
                    "nr_periods_delta": periods,
                    "nr_throttled_delta": throttled,
                    "throttled_usec_delta": deltas.get("throttled_usec", 0),
                    "throttled_period_pct": round(100 * throttled / periods, 3) if periods else 0,
                    "wall_ns": meta["wall_ns"],
                    "exit_status": meta["exit_status"],
                }
            )
    return rows


rows = []
for path in sorted(RAW.glob("*.log")):
    rows.extend(parse_log(path))

if not rows:
    raise SystemExit("no completed measurements found")

RUNS.parent.mkdir(parents=True, exist_ok=True)
with RUNS.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

groups = defaultdict(list)
group_meta = {}
for row in rows:
    key = tuple(
        row[name]
        for name in (
            "image",
            "commit",
            "cpus",
            "cgroup_namespace",
            "cpuset",
            "threads_requested",
            "threads_used",
            "test",
        )
    )
    groups[key].append(float(row["tokens_per_second"]))
    group_meta[key] = row

summary_rows = []
for key, values in groups.items():
    run = group_meta[key]
    summary_rows.append(
        dict(
            zip(
                (
                    "image",
                    "commit",
                    "cpus",
                    "cgroup_namespace",
                    "cpuset",
                    "threads_requested",
                    "threads_used",
                    "test",
                ),
                key,
            ),
            samples=len(values),
            median_tps=round(statistics.median(values), 4),
            min_tps=round(min(values), 4),
            max_tps=round(max(values), 4),
            nr_periods_delta=run["nr_periods_delta"],
            nr_throttled_delta=run["nr_throttled_delta"],
            throttled_period_pct=run["throttled_period_pct"],
            throttled_usec_delta=run["throttled_usec_delta"],
            wall_ns=run["wall_ns"],
        )
    )

summary_rows.sort(
    key=lambda row: (
        row["image"],
        row["cgroup_namespace"],
        row["cpuset"],
        row["cpus"],
        row["threads_requested"],
        row["test"],
    )
)
with SUMMARY.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0]))
    writer.writeheader()
    writer.writerows(summary_rows)

print(f"wrote {len(rows)} raw samples to {RUNS}")
print(f"wrote {len(summary_rows)} summaries to {SUMMARY}")
