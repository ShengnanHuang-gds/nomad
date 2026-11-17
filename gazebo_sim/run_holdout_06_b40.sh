#!/usr/bin/env bash
set -eo pipefail
ROOT=/mnt/c/Users/61078/Desktop/nomad
cd "$ROOT"
source "$ROOT/gazebo_sim/nomad_wsl_env.sh"
PY="$NOMAD_PY"
MODEL="${MODEL:-nomad_b40}"
OUT="${EPISODE_OUT:-$ROOT/gazebo_sim/episodes_eval_gpu/house_06_nomad_b40_lead4.json}"
LEAD="${SUBGOAL_LEAD:-1}"
WP="${WAYPOINT:-2}"
RAD="${RADIUS:-4}"
MAX_TICKS="${MAX_TICKS:-0}"
MAX_SIM_SECONDS="${MAX_SIM_SECONDS:-60}"
MAX_WALL_SECONDS="${MAX_WALL_SECONDS:-900}"
TEACH_YAW_DEG="${TEACH_YAW_DEG:-3}"
TEACH_EXIT_M="${TEACH_EXIT_M:-0.35}"
TEACH_ARGS=()
if [[ "${TEACH_ROUTE:-0}" == 1 ]]; then
  TEACH_ARGS=(--teach-route --teach-yaw-deg "$TEACH_YAW_DEG" --stop-on-collision)
elif [[ "${TEACH_YAW_SPIN:-0}" == 1 ]]; then
  TEACH_ARGS=(--teach-yaw-spin --teach-yaw-deg "$TEACH_YAW_DEG" --teach-exit-m "$TEACH_EXIT_M")
fi
export GZ_ROBOT_ENTITY="${GZ_ROBOT_ENTITY:-burger_cam}"

"$PY" "$ROOT/gazebo_sim/check_sim_prereq.py" --need-gpu
# list models (optional); skip if gz CLI cannot see the running sim
"$PY" "$ROOT/gazebo_sim/reset_run_pose.py" --list-models 2>/dev/null || true
if [[ "${SKIP_SPAWN_VERIFY:-0}" == 1 ]]; then
  echo "SKIP_SPAWN_VERIFY=1 (you already ran verify_06_spawn.sh; sim must still be fresh spawn)"
else
  "$PY" "$ROOT/gazebo_sim/reset_run_pose.py" --run house_run_06 --skip-teleport --verify --max-err-m 0.8 --settle-s 5
fi

"$PY" "$ROOT/gazebo_sim/pd_controller_ros2.py" --log-csv "${OUT%.*}.control.csv" &
PD=$!
sleep 1
trap "kill $PD 2>/dev/null || true" EXIT

"$PY" "$ROOT/gazebo_sim/nomad_navigate_ros2.py" \
  --topomap house_06 \
  --model "$MODEL" \
  --traj-name house_run_06 \
  --spawn-at-launch \
  --episode-out "$OUT" \
  --max-ticks "$MAX_TICKS" \
  --max-sim-seconds "$MAX_SIM_SECONDS" \
  --max-wall-seconds "$MAX_WALL_SECONDS" \
  --subgoal-lead "$LEAD" \
  --waypoint "$WP" \
  --radius "$RAD" \
  "${TEACH_ARGS[@]}" \
  --auto-log-csv

kill -TERM "$PD" 2>/dev/null || true
sleep 0.5
kill -KILL "$PD" 2>/dev/null || true
wait "$PD" 2>/dev/null || true

"$PY" "$ROOT/gazebo_sim/diagnose_episode.py" "$OUT"
"$PY" "$ROOT/gazebo_sim/plot_eval_routes.py" --episode-dir "$(dirname "$OUT")"
echo "done: $OUT"
