#!/usr/bin/env bash
set -eo pipefail
RUN="${1:-house_run_06}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
export GZ_IP="${GZ_IP:-127.0.0.1}"
export GZ_RELAY="${GZ_RELAY:-$GZ_IP}"
export TURTLEBOT3_MODEL=burger_cam
export NOMAD_SPAWN_AT_LAUNCH=1
read -r XP YP YAW <<< "$(python3 "$ROOT/gazebo_sim/read_traj_start.py" "$RUN")"
echo "launch house: spawn ($XP, $YP) from $RUN (yaw ${YAW} rad — align via reset_run_pose --align-spawn-yaw)"
exec ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py x_pose:="$XP" y_pose:="$YP"