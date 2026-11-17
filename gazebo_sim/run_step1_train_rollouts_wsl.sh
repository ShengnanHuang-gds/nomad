#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck source=/dev/null
source "$ROOT/gazebo_sim/nomad_wsl_env.sh"
PY="$NOMAD_PY"
MODEL="${1:-nomad_b40}"
EPDIR="$ROOT/gazebo_sim/episodes"
mkdir -p "$EPDIR"
run_one() {
  local id="$1"
  local topomap="house_${id}"
  local run="house_run_${id}"
  local out="$EPDIR/${topomap}.json"
  if [[ -f "$out" ]]; then
    echo "skip $topomap (already $out)"
    return 0
  fi
  echo "===== $topomap ($MODEL) -> $out ====="
  "$PY" "$ROOT/gazebo_sim/reset_run_pose.py" --run "$run"
  "$PY" "$ROOT/gazebo_sim/pd_controller_ros2.py" &
  local PD=$!
  trap "kill $PD 2>/dev/null || true" RETURN
  "$PY" "$ROOT/gazebo_sim/nomad_navigate_ros2.py" \
    --topomap "$topomap" \
    --model "$MODEL" \
    --traj-name "$run" \
    --episode-out "$out" \
    --max-ticks 800 || test -f "$out"
  kill "$PD" 2>/dev/null || true
  wait "$PD" 2>/dev/null || true
  trap - RETURN
}
for id in 00 01 02 03 04 05; do run_one "$id"; done
echo "episodes in $EPDIR"