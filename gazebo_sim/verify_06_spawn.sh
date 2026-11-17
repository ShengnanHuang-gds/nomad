#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/gazebo_sim/nomad_wsl_env.sh"
echo "Need terminal 1 (WSL): bash gazebo_sim/launch_tb3_house_at_run.sh house_run_06"
exec "$NOMAD_PY" "$ROOT/gazebo_sim/reset_run_pose.py" \
  --run house_run_06 --skip-teleport --verify --max-err-m 0.8 --settle-s 8