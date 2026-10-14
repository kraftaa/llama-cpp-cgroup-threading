# PR #30267 comparison

The open PR fixes integral cgroup-v2 quotas in the default Docker cgroup namespace, but fails fractional quota selection and does not resolve the current process cgroup when the mount root is not the process cgroup. A focused local follow-up fixes the demonstrated fractional regression without duplicating the PR.

All values below are medians of five raw samples in tokens/second. `pp128` is prompt processing; `tg64` is token generation. The throttling percentage is the configuration-wide delta `nr_throttled / nr_periods`, so it covers warmup plus both tests.

| Case | Revision / threads used | pp128 | tg64 | Throttled periods | Result |
|---|---:|---:|---:|---:|---|
| 1 CPU, old default | issue commit / 2 | 40.25 | 25.66 | 92.1% | Reproduces slowdown |
| 1 CPU, explicit | issue commit / 1 | 42.08 | 31.07 | 15.0% | Decode +21.1% |
| 1 CPU, PR parent default | parent / 2 | 39.05 | 23.86 | 89.2% | Failing baseline |
| 1 CPU, PR default | PR / 1 | 42.51 | 30.71 | 7.4% | Pass; +8.9% pp, +28.7% tg vs parent default |
| 1.5 CPUs, PR default | PR / 1 | 42.91 | 31.25 | 0.0% | **Fail: floors quota** |
| 1.5 CPUs, explicit | PR / 2 | 60.50 | 38.59 | 89.1% | +41.0% pp, +23.5% tg vs PR default |
| 1.5 CPUs, fixed default | local follow-up / 2 | 62.16 | 37.78 | 88.4% | Pass; overlaps explicit-run spread |
| 0.5 CPU, PR default | PR / 1 | 20.64 | 15.25 | 96.4% | Pass; minimum one thread |
| 0.5 CPU, explicit 2 | PR / 2 | 5.89 | 4.07 | 99.0% | Confirms one thread is correct |
| 2 CPUs, PR default | PR / 2 | 82.91 | 51.97 | 3.9% | Pass |
| Unlimited, PR default | PR / 2 | 82.64 | 52.00 | 0.0% | Pass/no regression seen |
| Host cgroup ns, 1 CPU, PR default | PR / 2 | 39.46 | 26.45 | 92.9% | **Fail: root path missing** |
| Host cgroup ns, 1 CPU, explicit 1 | PR / 1 | 42.94 | 31.40 | 20.7% | Effective quota is usable via process path |
| Cpuset `0`, unlimited, PR default | PR / 2 | 42.15 | 29.88 | n/a | **Selection fail**; expected cap to one available CPU |
| Cpuset `0`, explicit 1 | PR / 1 | 42.55 | 30.56 | n/a | Similar throughput on this ARM host |

The one-CPU issue reproduction is smaller than the reporter's 3.1x result because this host exposes only two Linux CPUs, so its bad default is two rather than ten threads. It still reproduces the mechanism: default decode is 17.4% lower than explicit one-thread performance, with 92.1% versus 15.0% of periods throttled.

## Edge-case classification

| Case | Status | Evidence |
|---|---|---|
| cgroup v2, private namespace, integral quota | PASS | PR selects 1 and 2 threads at 1 and 2 CPUs |
| Fractional 0.5 CPU | PASS | PR selects one; two threads are much slower |
| Fractional 1.5 CPU | FAIL in PR; PASS locally | PR selects one; measured optimum among tested decode settings is two; local ceil fix selects two |
| Fractional 2.5 CPU | UNTESTED | VM has two CPUs |
| Unlimited quota | PASS | Old two-core default retained |
| Positive explicit override | PASS | bench and CLI retain requested thread count |
| Affinity/cpuset narrower than topology | FAIL selection | `nproc=1`, effective cpuset `0`, PR default remains two |
| Host cgroup namespace / non-root process cgroup | FAIL | `/sys/fs/cgroup/cpu.max` is missing while `/sys/fs/cgroup/docker/<id>/cpu.max` contains the quota |
| Nested constrained ancestor | UNTESTED | No safe parent-cgroup control in this VM |
| Malformed metadata | UNTESTED | PR's hard-coded sysfs path offers no injection seam |
| cgroup v1 | UNTESTED | Environment is cgroup v2 only |
| llama-cli shared path | PASS | Verbose one-token inference reports `n_threads = 1`, CPU-only; explicit `-t 2` remains two |
| llama-server shared path | PASS | Server initializes one-thread CPU pool and listens successfully under a one-CPU quota |

## Root-cause assessment

At one CPU, excess runnable math threads correlate with near-every-period CFS bandwidth throttling and lower decode throughput. Reducing two threads to one sharply reduces throttled periods and improves generation speed, supporting quota-driven throttling plus synchronization/scheduling overhead as the main cause in this experiment.

Throttling percentage alone is not a performance verdict: at 1.5 CPUs, two threads are throttled in most periods but outperform one thread because they can consume the extra half-CPU budget. That observation is the direct reason floor rounding is wrong here. Memory bandwidth and cache contention were not independently instrumented and cannot be ruled out as secondary effects.

## Focused contribution

Local commit `d9ae21d39ad086270c399dbe7d386cb6be87b228` is based directly on PR #30267. It changes quota conversion from floor to overflow-safe ceiling for both v1 and v2 parsing. It does not create a second detector, benchmark, or public project. The generated follow-up patch is in `contribution/`.

The host-cgroup-namespace and affinity gaps are documented evidence for review discussion, but intentionally excluded from this small patch. Correct mount/path discovery requires parsing `/proc/self/cgroup` and `/proc/self/mountinfo`; combining affinity, topology, and ancestor limits deserves separate review rather than an untested expansion.
