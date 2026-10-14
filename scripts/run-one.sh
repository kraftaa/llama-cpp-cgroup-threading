#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 || $# -gt 5 ]]; then
    echo "usage: $0 IMAGE CPUS THREADS CGROUP_NAMESPACE [CPUSET]" >&2
    echo "  CPUS: max or Docker --cpus value; THREADS: default or integer" >&2
    exit 2
fi

image=$1
cpus=$2
threads=$3
cgroupns=$4
cpuset=${5:-all}
reps=${REPS:-5}

root_dir=$(cd "$(dirname "$0")/.." && pwd)
model="$root_dir/models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
raw_dir="$root_dir/results/raw"
mkdir -p "$raw_dir"

if [[ ! -f "$model" ]]; then
    echo "missing model: $model" >&2
    exit 1
fi

safe_image=${image//[:\/]/-}
run_id="${safe_image}__cpu-${cpus}__threads-${threads}__ns-${cgroupns}__set-${cpuset}"
log="$raw_dir/$run_id.log"

if [[ ${FORCE:-0} != 1 ]] && [[ -f "$log" ]] && grep -q 'exit_status=0' "$log"; then
    echo "skipping completed $run_id"
    exit 0
fi

docker_args=(docker run --rm --cgroupns="$cgroupns")
if [[ "$cpus" != max ]]; then
    docker_args+=(--cpus="$cpus")
fi
if [[ "$cpuset" != all ]]; then
    docker_args+=(--cpuset-cpus="$cpuset")
fi
docker_args+=(-v "$root_dir/models:/models:ro" --entrypoint /bin/sh "$image" -c)

bench_args=""
if [[ "$threads" != default ]]; then
    bench_args="-t $threads"
fi

container_script='set -u
rel=$(awk -F: '\''$1 == "0" { print $3 }'\'' /proc/self/cgroup)
cg="/sys/fs/cgroup${rel}"
if [ ! -f "$cg/cpu.stat" ]; then cg=/sys/fs/cgroup; fi
echo "META image=$1 cpus=$2 threads_requested=$3 cgroupns=$4 cpuset=$5 reps=$6"
echo "META kernel=$(uname -r) arch=$(uname -m) nproc=$(nproc) cgroup_rel=$rel resolved_cgroup=$cg"
grep -E "Cpus_allowed_list|Mems_allowed_list" /proc/self/status | sed "s/^/META /"
if [ -f /sys/fs/cgroup/cpu.max ]; then echo "META root_cpu_max=$(cat /sys/fs/cgroup/cpu.max)"; else echo "META root_cpu_max=MISSING"; fi
if [ -f "$cg/cpu.max" ]; then echo "META effective_cpu_max=$(cat "$cg/cpu.max")"; else echo "META effective_cpu_max=MISSING"; fi
if [ -f "$cg/cpuset.cpus.effective" ]; then echo "META effective_cpuset=$(cat "$cg/cpuset.cpus.effective")"; fi
cat "$cg/cpu.stat" | sed "s/^/STAT_BEFORE /"
start=$(date +%s%N)
/src/build/bin/llama-bench -m /models/qwen2.5-0.5b-instruct-q4_k_m.gguf -p 128 -n 64 -r "$6" -o jsonl -ngl 0 $7
rc=$?
end=$(date +%s%N)
echo "META wall_ns=$((end-start)) exit_status=$rc"
cat "$cg/cpu.stat" | sed "s/^/STAT_AFTER /"
exit "$rc"'

echo "running $run_id"
"${docker_args[@]}" "$container_script" sh "$image" "$cpus" "$threads" "$cgroupns" "$cpuset" "$reps" "$bench_args" >"$log" 2>&1
echo "wrote $log"
