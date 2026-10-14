#!/usr/bin/env bash
set -euo pipefail

root_dir=$(cd "$(dirname "$0")/.." && pwd)
run="$root_dir/scripts/run-one.sh"

# The order alternates quota settings and revisions to reduce simple warm-up,
# thermal, and revision-order bias. llama-bench records all five raw samples.
configs=(
    "llama-cgroup:issue-baseline 1 default private all"
    "llama-cgroup:pr 1 default private all"
    "llama-cgroup:pr-parent 1 default private all"
    "llama-cgroup:issue-baseline 1 1 private all"
    "llama-cgroup:pr-parent 1 1 private all"
    "llama-cgroup:pr 1 1 private all"
    "llama-cgroup:issue-baseline 1 2 private all"
    "llama-cgroup:pr 1 2 private all"
    "llama-cgroup:pr-parent 1 2 private all"
    "llama-cgroup:pr 1 4 private all"
    "llama-cgroup:pr-parent 1 4 private all"

    "llama-cgroup:pr 1.5 default private all"
    "llama-cgroup:pr-parent 1.5 default private all"
    "llama-cgroup:pr 0.5 default private all"
    "llama-cgroup:pr 2 default private all"
    "llama-cgroup:pr-parent 1.5 2 private all"
    "llama-cgroup:pr 1.5 2 private all"
    "llama-cgroup:pr 0.5 1 private all"
    "llama-cgroup:pr 2 2 private all"
    "llama-cgroup:pr-parent 1.5 1 private all"
    "llama-cgroup:pr 1.5 1 private all"
    "llama-cgroup:pr 0.5 2 private all"
    "llama-cgroup:pr 2 1 private all"
    "llama-cgroup:pr 1.5 3 private all"
    "llama-cgroup:pr 2 4 private all"
    "llama-cgroup:pr 1.5 4 private all"
    "llama-cgroup:pr 2 8 private all"

    "llama-cgroup:pr max default private all"
    "llama-cgroup:pr max 1 private all"
    "llama-cgroup:pr max 2 private all"
    "llama-cgroup:pr max 4 private all"
    "llama-cgroup:pr max 8 private all"

    "llama-cgroup:pr max default private 0"
    "llama-cgroup:pr max 1 private 0"
    "llama-cgroup:pr max 2 private 0"
    "llama-cgroup:pr max 4 private 0"

    "llama-cgroup:pr 1 default host all"
    "llama-cgroup:pr 1 1 host all"
    "llama-cgroup:pr 1 2 host all"
    "llama-cgroup:pr 1.5 default host all"
    "llama-cgroup:pr 1.5 1 host all"
    "llama-cgroup:pr 1.5 2 host all"
)

for config in "${configs[@]}"; do
    # shellcheck disable=SC2086
    "$run" $config
done
