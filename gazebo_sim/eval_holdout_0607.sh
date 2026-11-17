#!/usr/bin/env bash
set -eo pipefail
ROOT=/mnt/c/Users/61078/Desktop/nomad
cd "$ROOT"
source "$ROOT/gazebo_sim/nomad_wsl_env.sh"
PY="$NOMAD_PY"
OUT="$ROOT/gazebo_sim/episodes_eval"
mkdir -p "$OUT"
MAX_TICKS="${MAX_TICKS:-1200}"

run_one() {
  local id="$1"
  local model="$2"
  local topomap="house_${id}"
  local run="house_run_${id}"
  local tag="${topomap}_${model}"
  local out="$OUT/${tag}.json"
  echo "===== $tag max_ticks=$MAX_TICKS ====="
  "$PY" "$ROOT/gazebo_sim/reset_run_pose.py" --run "$run"
  "$PY" "$ROOT/gazebo_sim/pd_controller_ros2.py" &
  local PD=$!
  trap "kill $PD 2>/dev/null || true" RETURN
  "$PY" "$ROOT/gazebo_sim/nomad_navigate_ros2.py" \
    --topomap "$topomap" \
    --model "$model" \
    --traj-name "$run" \
    --episode-out "$out" \
    --max-ticks "$MAX_TICKS"
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
echo "=== hold-out summary ==="
"$PY" -c "import json,glob,os; root=r'''$OUT'''; rows=[]; 
[rows.append((os.path.basename(p).replace('.json',''), *(lambda d:(d.get('success'),d.get('path_odom_m'),d.get('collision_count'),d.get('closest_node'),d.get('goal_node')))(json.load(open(p,encoding='utf-8')))) for p in sorted(glob.glob(os.path.join(root,'house_*.json')))]; 
print(f\"{'run':28} {'succ':>5} {'path_m':>8} {'coll':>5} {'node':>10}\");
[print(f\"{r[0]:28} {str(r[1]):>5} {r[2]:8.2f} {r[3]:5d} {r[4]}/{r[5]:>10}\") for r in rows]"