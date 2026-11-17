#!/usr/bin/env bash
set -eo pipefail
ROOT=/mnt/c/Users/61078/Desktop/nomad
source "$ROOT/gazebo_sim/nomad_wsl_env.sh"
PY="$NOMAD_PY"
OUT="$ROOT/gazebo_sim/episodes_eval_gpu/house_06_nomad_b40.json"
"$PY" "$ROOT/gazebo_sim/reset_run_pose.py" --run house_run_06 --verify --max-err-m 0.5
"$PY" "$ROOT/gazebo_sim/pd_controller_ros2.py" &
PD=$!
sleep 1
"$PY" "$ROOT/gazebo_sim/nomad_navigate_ros2.py" --topomap house_06 --model nomad_b40 --traj-name house_run_06 --episode-out "$OUT" --max-ticks 600 --auto-log-csv
kill $PD 2>/dev/null || true