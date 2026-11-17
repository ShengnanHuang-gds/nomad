#!/usr/bin/env bash
set -eo pipefail
ROOT=/mnt/c/Users/61078/Desktop/nomad
cd "$ROOT"
source "$ROOT/gazebo_sim/nomad_wsl_env.sh"
export GZ_ROBOT_ENTITY="${GZ_ROBOT_ENTITY:-burger_cam}"
exec "$NOMAD_PY" "$ROOT/gazebo_sim/reset_run_pose.py" \
  --run house_run_06 \
  --entity "$GZ_ROBOT_ENTITY" \
  --verify --max-err-m 0.5 --settle-s 6