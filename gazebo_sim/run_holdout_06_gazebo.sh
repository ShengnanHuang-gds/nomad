#!/usr/bin/env bash
set -eo pipefail
ROOT=/mnt/c/Users/61078/Desktop/nomad
cd "$ROOT"
source "$ROOT/gazebo_sim/nomad_wsl_env.sh"
PY="$NOMAD_PY"
OUT="$ROOT/gazebo_sim/episodes_eval_gpu/house_06_nomad_gazebo.json"
MAX_TICKS="${MAX_TICKS:-600}"
export GZ_ROBOT_ENTITY="${GZ_ROBOT_ENTITY:-burger_cam}"

"$PY" "$ROOT/gazebo_sim/check_sim_prereq.py" --need-gpu
"$PY" "$ROOT/gazebo_sim/reset_run_pose.py" --list-models 2>/dev/null || true
if [[ "${SKIP_SPAWN_VERIFY:-0}" == 1 ]]; then
  echo "SKIP_SPAWN_VERIFY=1 (fresh spawn required if prior holdout drove the robot)"
else
  "$PY" "$ROOT/gazebo_sim/reset_run_pose.py" --run house_run_06 --skip-teleport --verify --max-err-m 0.8 --settle-s 5
fi

"$PY" "$ROOT/gazebo_sim/pd_controller_ros2.py" &
PD=$!
sleep 1
trap "kill -TERM $PD 2>/dev/null || true; sleep 0.5; kill -KILL $PD 2>/dev/null || true" EXIT

"$PY" "$ROOT/gazebo_sim/nomad_navigate_ros2.py" \
  --topomap house_06 \
  --model nomad_gazebo \
  --traj-name house_run_06 \
  --spawn-at-launch \
  --episode-out "$OUT" \
  --max-ticks "$MAX_TICKS" \
  --auto-log-csv

kill -TERM "$PD" 2>/dev/null || true
sleep 0.5
kill -KILL "$PD" 2>/dev/null || true
wait "$PD" 2>/dev/null || true

"$PY" "$ROOT/gazebo_sim/diagnose_episode.py" "$OUT"
"$PY" "$ROOT/gazebo_sim/plot_eval_routes.py" --episode-dir "$(dirname "$OUT")"
echo "done: $OUT"