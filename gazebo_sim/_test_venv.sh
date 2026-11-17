#!/usr/bin/env bash
set +u
source /opt/ros/jazzy/setup.bash
/home/hsnnb/nomad_ros_venv/bin/python -c 'import torch, rclpy; print("OK", torch.__version__)'
