#!/usr/bin/env python3
from pathlib import Path

content = r"""#!/usr/bin/env bash
set -eo pipefail
RUN="${1:-house_run_06}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
export GZ_IP="${GZ_IP:-127.0.0.1}"
export GZ_RELAY="${GZ_RELAY:-$GZ_IP}"
export TURTLEBOT3_MODEL=burger_cam
read -r XP YP _YAW <<< "$(python3 "$ROOT/gazebo_sim/read_traj_start.py" "$RUN")"
echo "launch house: spawn ($XP, $YP) from $RUN"
exec ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py x_pose:="$XP" y_pose:="$YP"
"""

Path(__file__).resolve().parent.joinpath("launch_tb3_house_at_run.sh").write_text(
    content, encoding="utf-8", newline="\n"
)
print("ok")