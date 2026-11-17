#!/usr/bin/env bash
# Source before nomad_navigate / step1 rollouts (ROS Jazzy + Python with torch+rclpy).
set -eo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
set +u
source /opt/ros/jazzy/setup.bash
set -u
# Gazebo CLI (gz model -l / set_pose) must reach the same sim as ros_gz_bridge
export GZ_IP="${GZ_IP:-127.0.0.1}"
export GZ_RELAY="${GZ_RELAY:-$GZ_IP}"
export GZ_PARTITION="${GZ_PARTITION:-}"
export PYTHONPATH="$ROOT/visualnav-transformer/diffusion_policy${PYTHONPATH:+:$PYTHONPATH}"

if [[ -n "${NOMAD_PY:-}" ]]; then
  :
elif [[ -x "${NOMAD_VENV:-$HOME/nomad_ros_venv}/bin/python" ]]; then
  NOMAD_PY="${NOMAD_VENV:-$HOME/nomad_ros_venv}/bin/python"
elif python3 -c 'import torch, rclpy' 2>/dev/null; then
  NOMAD_PY=python3
elif [[ -x /home/hsnnb/miniconda3/envs/nomad_nav/bin/python ]]; then
  export PYTHONPATH="/opt/ros/jazzy/lib/python3.12/site-packages:${PYTHONPATH}"
  NOMAD_PY=/home/hsnnb/miniconda3/envs/nomad_nav/bin/python
else
  echo "Run once: bash $ROOT/gazebo_sim/setup_wsl_nomad_py.sh" >&2
  exit 1
fi
export NOMAD_PY
export PATH="$HOME/.local/bin:$PATH"