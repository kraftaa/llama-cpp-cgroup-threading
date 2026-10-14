# CPU inference under Linux cgroup limits — final report

## 1. Upstream status

[Issue #30070](https://github.com/ggml-org/llama.cpp/issues/30070) and [PR #30267](https://github.com/ggml-org/llama.cpp/pull/30267) were both open when checked on 2026-10-13. The PR head was `a9672dd07ac5e98768f94fda11b6cb549c2eb744`, with no reviews and no build/test checks beyond the labeler. Its direct parent was used for the controlled code-change comparison. See `research/upstream.md` for the code-path review.

## 2. What was executed

Three pinned upstream revisions and one local follow-up were built CPU-only in Docker. `llama-bench` ran 46 completed configurations, two workload types per configuration, and five samples per workload: 460 raw measurements total. The matrix covered private and host cgroup namespaces, 0.5/1/1.5/2/unlimited CPU quotas, explicit 1/2/3/4/8 threads, and a one-CPU cpuset. One-token `llama-cli` inference and `llama-server` initialization verified the shared default path.

Reproduction commands are in `scripts/`; raw logs are in `results/raw/`; normalized samples and summaries are `results/runs.csv` and `results/summary.csv`. Environment, model checksum, build flags, image IDs, and limitations are in `results/environment.md`.

## 3. Results

The original defect was independently reproduced in direction and mechanism. At a one-CPU quota, the issue commit's two-thread default decoded at 25.66 tok/s versus 31.07 tok/s with one explicit thread (+21.1%), while throttled-period incidence fell from 92.1% to 15.0%.

The existing PR fixes that integral case: against its immediate parent, the one-CPU default improves from 39.05 to 42.51 tok/s for prefill and from 23.86 to 30.71 tok/s for decode.

The PR has a measured fractional regression. At 1.5 CPUs it floors to one thread. Two threads improve median prefill from 42.91 to 60.50 tok/s (+41.0%) and decode from 31.25 to 38.59 tok/s (+23.5%). The local ceiling fix chooses two threads and measures 62.16/37.78 tok/s, within the explicit two-thread sample spread. It leaves 0.5, 1, and 2 CPU selections unchanged.

Two further selection gaps were demonstrated: fixed root cgroup paths miss a one-CPU quota under Docker's host cgroup namespace, and an unlimited container restricted to cpuset `0` still defaults to two threads. These are not included in the fractional patch.

## 4. Explanation

The integral-quota slowdown is best explained by CFS bandwidth throttling amplified by synchronization and scheduling overhead from excess runnable threads. The fractional result shows why quota equivalence is not itself the best thread count: a 1.5-CPU time budget needs two runnable threads to use the fractional capacity on this workload. Conversely, at 0.5 CPU, two threads collapse performance, so the correct rule for the tested fractional range is `ceil(quota / period)`, capped by the existing topology result—not an unrestricted increase.

## 5. Recommendation

**UPSTREAM FIX.** Do not open a competing PR. Post the 1.5-CPU evidence and attach the focused follow-up commit/patch to PR #30267, asking the author/maintainers to incorporate it. Also report the host-cgroup-namespace and cpuset failures as scoped follow-up cases. A broader cgroup resolver should wait for maintainer direction and dedicated tests.

## 6. Publication check

A truthful short post can say: “I reproduced llama.cpp's cgroup default-thread slowdown in Linux Docker, found that the open fix leaves significant 1.5-CPU performance unused by flooring fractional quotas, and prepared a measured follow-up patch.” It must also say the measurements used a two-vCPU Colima Linux VM, the existing PR already owns the main fix, and no upstream acceptance has occurred. This is contribution-ready evidence, not a claim of merged impact or a new benchmark product.
