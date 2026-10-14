# llama.cpp cgroup CPU investigation

This repository records an independent reproduction and review of [llama.cpp issue #30070](https://github.com/ggml-org/llama.cpp/issues/30070) and [PR #30267](https://github.com/ggml-org/llama.cpp/pull/30267). It deliberately uses upstream `llama-bench`; it does not introduce another benchmark tool.

Start with:

- `research/final-report.md` — conclusion and recommendation
- `research/upstream.md` — mandatory upstream stop/go review
- `results/pr-comparison.md` — numerical comparison and edge-case status
- `results/environment.md` — exact environment and limitations
- `results/runs.csv` — 460 raw samples
- `contribution/0001-common-round-fractional-cgroup-quotas-up.patch` — focused follow-up to the existing PR

The recommendation is **UPSTREAM FIX**: share the fractional-quota evidence and patch on the existing PR rather than opening a duplicate implementation.
