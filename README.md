# llama.cpp cgroup CPU investigation

This repository records an independent reproduction and review of [llama.cpp issue #30070](https://github.com/ggml-org/llama.cpp/issues/30070) and [PR #30267](https://github.com/ggml-org/llama.cpp/pull/30267). It deliberately uses upstream `llama-bench`; it does not introduce another benchmark tool.

Start with:

- `research/final-report.md` — conclusion and recommendation
- `research/upstream.md` — mandatory upstream stop/go review
- `results/pr-comparison.md` — numerical comparison and edge-case status
- `results/environment.md` — exact environment and limitations
- `results/runs.csv` — 460 raw samples
- `contribution/0001-common-round-fractional-cgroup-quotas-up.patch` — focused follow-up to the existing PR
- `research/critical-review.md` — risks, corrections, and public-run stop/go criteria

The recommendation is **UPSTREAM FIX**: share the fractional-quota evidence and patch on the existing PR rather than opening a duplicate implementation.

## Public Linux verification

The `Linux cgroup reproduction` GitHub Actions workflow is intentionally
manual-only. After the repository is public, open **Actions → Linux cgroup
reproduction → Run workflow**. The default five repetitions build the pinned PR
parent, PR, and fractional follow-up, download and checksum the pinned model,
run a narrow CPU-only matrix, and upload raw logs plus `ci-verdict.md`.

Making the repository public does not itself start the workflow. Do not add a
schedule or push trigger: this is a one-time independent evidence run, not a
general benchmark service or a stable performance CI suite.

The workflow uses the standard `ubuntu-24.04` runner. GitHub documents standard
hosted runners as free and unlimited for public repositories; artifact storage
still follows the account's storage policy. Only small text/CSV evidence is
uploaded—the model and Docker images are not retained as artifacts.
