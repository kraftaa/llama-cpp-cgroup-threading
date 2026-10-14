# Measurement environment

Measured: 2026-10-13 and 2026-10-14 UTC (2026-10-13 America/New_York)

## Host and Linux runtime

- Physical host: Apple M1 Pro MacBook Pro (`MacBookPro18,1`), 10 host cores (8 performance, 2 efficiency), 32 GB RAM, macOS 26.7.1.
- Docker daemon: Docker 27.4.0 using Colima, Ubuntu 24.04.1 LTS, Linux 6.8.0-50-generic, cgroup v2, `aarch64`, overlayfs.
- Linux VM allocation: 2 vCPUs, 3,999,444 KiB RAM. The Linux container reported two online CPUs, one thread per core, and effective cpuset `0-1` when unrestricted.
- Ubuntu image: `ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55`.
- Post-run Linux VM load snapshot: `0.26 0.75 1.00`; load was not sampled for every individual run.

This is a real Linux kernel and cgroup-v2 Docker environment, but it is a Linux VM on macOS, not a bare-metal Linux host. The results are valid for the tested environment and reproduce the cgroup mechanism, but they must not be generalized as bare-host CPU performance results.

## Source and images

| Name | Commit | Local image ID |
|---|---|---|
| Issue reproduction | `11fe02151f79c41d0d4af7da708755d73b9c0da6` | `sha256:e6e69044560c1803d8b4677ed04ca47a4e1f38063b250788cb9510fbcf26e2e4` |
| PR parent | `10a60cf303566e10d6a7a2774c17d2085503d87b` | `sha256:84fb7115e0e0d5829256cdd9ad0f5a1d4615ae2ac084660462d8d8e80abb437c` |
| PR #30267 | `a9672dd07ac5e98768f94fda11b6cb549c2eb744` | `sha256:cbd8d13c210194b738e5176e5c7aacc57002e202dbf5585205c1a39d5754e405` |
| Local fractional follow-up | `d9ae21d39ad086270c399dbe7d386cb6be87b228` | `sha256:1d5a23128dd05c856cd7f3330d2347c0f1bddba0b6131ea3d1d9d4e4826feda8` |

All builds used GCC 13.3, CMake Release mode, static libraries, `GGML_NATIVE=OFF`, and disabled CUDA, Metal, Vulkan, OpenCL, BLAS, and curl. Runtime commands also set `-ngl 0`. Every `llama-bench` JSON row reports `backends: CPU`, empty `gpu_info`, and `n_gpu_layers: 0`.

## Model and workload

- Model: official `Qwen/Qwen2.5-0.5B-Instruct-GGUF`, revision `2ed9be962c95f7625f4963ff51ed472e4538187a`, file `qwen2.5-0.5b-instruct-q4_k_m.gguf`.
- Size: 491,400,032 bytes.
- SHA-256: `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`.
- This is a close public substitute for the reporter's unnamed Qwen 0.5B Q4_K_M file; it is not claimed to be byte-identical.
- Per configuration: `llama-bench -p 128 -n 64 -r 5 -o jsonl -ngl 0`, with llama-bench's normal warmup.
- The run order alternated revisions, quotas, and thread counts. Each result preserves all five sample times/rates plus before/after `cpu.stat` counters.

## Scope limitations

- Quotas 0.5, 1, 1.5, and 2 CPUs, unlimited quota, explicit 1/2/3/4/8 threads, a one-CPU cpuset, and host/private cgroup namespaces were tested.
- Docker rejected `--cpus=4` because the VM has only two CPUs. Quota-greater-than-affinity was approximated with unlimited quota plus a one-CPU cpuset.
- cgroup v1, a separately constrained ancestor, malformed synthetic cgroup files, and 2.5 CPUs were not testable here.
- Host load was not recorded for every run, and the VM is shared with macOS. Five-sample min/max ranges are reported to expose noise.
