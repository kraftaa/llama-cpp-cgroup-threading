# Critical review and public-run plan

Reviewed: 2026-10-14

## Upstream recheck

Issue [#30070](https://github.com/ggml-org/llama.cpp/issues/30070) and PR
[#30267](https://github.com/ggml-org/llama.cpp/pull/30267) remain open. The PR
head is still `a9672dd07ac5e98768f94fda11b6cb549c2eb744`; it has no reviews and its
only check is the PR labeler. No upstream change invalidates the existing
stop/go decision.

## What is strong

- The repository uses upstream `llama-bench`, not a new benchmark program.
- Revisions, image, model, checksum, raw samples, selected threads, cgroup
  counters, and CPU-only backend are recorded.
- The integral defect and the fractional 1.5-CPU gap are separated from claims
  about cpusets, hierarchy discovery, or bare-metal performance.
- The proposed patch is a small follow-up to the open PR and leaves explicit
  thread overrides alone.

## What needed correction

- Committed raw logs caused `run-one.sh` to skip a fresh run. `RESULTS_DIR` now
  isolates new evidence, and `MODEL_PATH` allows a runner-specific model path.
- A full 46-configuration matrix is expensive and too host-sensitive for CI.
  The manual workflow runs only the comparisons required for the fractional
  stop/go decision.
- Throughput should not become a permanent upstream CI invariant. The verifier
  treats a 5% gain on this one fresh Linux host as evidence for or against this
  contribution, not as a general llama.cpp regression threshold.
- GitHub-hosted runners are genuine Linux but virtualized, shared, and variable.
  They strengthen portability beyond the local Colima VM; they do not establish
  bare-metal performance.

## Remaining limitations

- cgroup v1, constrained ancestors, malformed metadata, and a correct generic
  cgroup mount/path resolver are still untested.
- The workflow downloads a 491 MB model from Hugging Face and therefore depends
  on that external service retaining the pinned revision.
- The workflow deliberately pins the upstream PR and parent commits. If the PR
  changes, the evidence must be reviewed and the pins updated rather than
  silently testing a moving branch.
- Runner CPU topology and contention can change. Raw logs and environment data
  are uploaded so a surprising result can be diagnosed rather than hidden.

## Stop/go criteria

**GO:** required thread selections match, the follow-up chooses two threads at
1.5 CPUs, explicit `-t 2` stays unchanged, and the follow-up improves at least
one of prefill or decode by 5% on the fresh Linux runner.

**STOP:** any selection assertion fails, or the new host shows less than a 5%
gain in both workloads. In that case, do not post the patch upstream as a
cross-host performance fix; inspect the uploaded logs and report the negative
result.

The host-namespace and cpuset observations remain discussion points, not part of
this patch. Building either fix now would outrun the available tests and risk
duplicating upstream work.
