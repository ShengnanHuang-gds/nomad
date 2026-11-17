#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
export GZ_IP="${GZ_IP:-127.0.0.1}"
export GZ_RELAY="${GZ_RELAY:-$GZ_IP}"
export TURTLEBOT3_MODEL=burger_cam
exec ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py
