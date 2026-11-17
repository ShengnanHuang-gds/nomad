#!/usr/bin/env bash
set -eo pipefail
ROOT=/mnt/c/Users/61078/Desktop/nomad
cd "$ROOT"
source "$ROOT/gazebo_sim/nomad_wsl_env.sh"
PY="$NOMAD_PY"
OUT="$ROOT/gazebo_sim/episodes_eval_gpu"
mkdir -p "$OUT"
MAX_TICKS="${MAX_TICKS:-1200}"
export OUT

run_one() {
  local id="$1"
  local model="$2"
  local topomap="house_${id}"
  local run="house_run_${id}"
  local tag="${topomap}_${model}"
  local out="$OUT/${tag}.json"
  echo "===== $tag max_ticks=$MAX_TICKS ====="
  "$PY" "$ROOT/gazebo_sim/reset_run_pose.py" --run "$run" --verify --max-err-m 0.5
  "$PY" "$ROOT/gazebo_sim/pd_controller_ros2.py" &
  local PD=$!
  trap "kill $PD 2>/dev/null || true" RETURN
  "$PY" "$ROOT/gazebo_sim/nomad_navigate_ros2.py" \
    --topomap "$topomap" \
    --model "$model" \
    --traj-name "$run" \
    --episode-out "$out" \
    --max-ticks "$MAX_TICKS" \
    --auto-log-csv
  kill "$PD" 2>/dev/null || true
  wait "$PD" 2>/dev/null || true
  trap - RETURN
}

for model in nomad_b40 nomad_gazebo_task; do
  for id in 06 07; do
    run_one "$id" "$model"
  done
done

echo
echo "=== hold-out summary (GPU) ==="
"$PY" "$ROOT/gazebo_sim/summarize_holdout_eval.py" "$OUT"