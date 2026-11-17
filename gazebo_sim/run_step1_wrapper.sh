#!/usr/bin/env bash
set -eo pipefail
ROOT=/mnt/c/Users/61078/Desktop/nomad
cd "$ROOT"
source "$ROOT/gazebo_sim/nomad_wsl_env.sh"
bash "$ROOT/gazebo_sim/run_step1_train_rollouts_wsl.sh" "${1:-nomad_b40}"
source "$ROOT/gazebo_sim/nomad_wsl_env.sh"
"$NOMAD_PY" "$ROOT/gazebo_sim/collect_task_metrics.py" --episode-dir "$ROOT/gazebo_sim/episodes"