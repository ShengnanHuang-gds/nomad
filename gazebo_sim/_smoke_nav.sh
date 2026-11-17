#!/usr/bin/env bash
set -eo pipefail
ROOT=/mnt/c/Users/61078/Desktop/nomad
cd "$ROOT"
set +u
source /opt/ros/jazzy/setup.bash
set -u
export PYTHONPATH="$ROOT/visualnav-transformer/diffusion_policy:$ROOT/visualnav-transformer/train:$ROOT/visualnav-transformer/deployment/src"
/home/hsnnb/nomad_ros_venv/bin/python "$ROOT/gazebo_sim/nomad_navigate_ros2.py" --help 2>&1 | head -3