# Upstream reconnaissance

Checked: 2026-10-13

## Status and pinned revisions

- Issue [ggml-org/llama.cpp#30070](https://github.com/ggml-org/llama.cpp/issues/30070) is open. Its reproduction commit is `11fe02151f79c41d0d4af7da708755d73b9c0da6`.
- Fix PR [ggml-org/llama.cpp#30267](https://github.com/ggml-org/llama.cpp/pull/30267) is open and not a draft. Its sole commit is `a9672dd07ac5e98768f94fda11b6cb549c2eb744`; its parent is `10a60cf303566e10d6a7a2774c17d2085503d87b`.
- The PR has no review comments or approvals. The only reported check is the successful PR labeler; no build or test result is attached.
- PR #30263 is a closed earlier version of the same change. A repository search found no merged competing cgroup-thread fix.
- Upstream `master` was `fcac19079f3f2985fe74ed845f0880e7e9a8030a` when cloned.

## Code-path findings

`common_cpu_get_num_math()` in `common/common.cpp` supplies the default math-thread count. `postprocess_cpu_params()` applies it when the common CLI CPU-thread value remains negative. Therefore `llama-cli` and `llama-server`, which use common argument parsing, share this default path. Positive explicit `-t/--threads` values bypass default selection. `llama-bench` initializes its own default directly with `common_cpu_get_num_math()`.

On Linux, the existing default is primarily physical-core/topology based. CPU affinity is used specially only for hybrid x86 CPU classification; the generic path does not cap the result to the current affinity count.

PR #30267 adds one private helper and caps the existing result. It:

- reads cgroup v2 only from `/sys/fs/cgroup/cpu.max`;
- falls back to cgroup v1 only at `/sys/fs/cgroup/cpu/cpu.cfs_quota_us` and `cpu.cfs_period_us`;
- uses integer division, so positive fractional quotas are rounded down, with a minimum of one thread;
- returns zero for unlimited, unavailable, invalid, or non-positive metadata, preserving the old default;
- does not parse `/proc/self/cgroup` or `/proc/self/mountinfo`, traverse parent cgroups, combine quota with effective cpuset/affinity, or add tests;
- leaves positive explicit thread settings unchanged.

Fixed root paths work when a cgroup namespace makes the process cgroup appear as the mounted hierarchy root. They are not sufficient in every valid Linux setup, notably a host cgroup namespace where the process belongs to a descendant cgroup. Parent limits in a nested hierarchy are also not evaluated.

## Stop/go decision

**GO for measurement only.** Do not create a competing implementation. The PR addresses the issue's basic cgroup-v2-container case, but non-root/nested cgroup lookup, fractional quota behavior, affinity interaction, and failure handling have no tests or evidence. Continue only to determine whether one of those omissions produces a demonstrated user-facing defect. If not, stop.
