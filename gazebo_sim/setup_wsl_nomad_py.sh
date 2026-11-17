#!/usr/bin/env bash
# One-time: system Python 3.12 (ROS Jazzy) + venv with torch (keeps rclpy from ROS).
set -euo pipefail
VENV="${NOMAD_VENV:-$HOME/nomad_ros_venv}"
if ! dpkg -s python3.12-venv >/dev/null 2>&1; then
  echo "Install deps (password once):"
  echo "  sudo apt-get update && sudo apt-get install -y python3.12-venv python3-pip curl"
  exit 1
fi
python3 -m venv --system-site-packages "$VENV"
source "$VENV/bin/activate"
python -m pip install -U pip wheel
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
python -m pip install 'numpy<2' diffusers transformers efficientnet-pytorch opencv-python-headless pyyaml pillow einops vit-pytorch prettytable timm lmdb
set +u
source /opt/ros/jazzy/setup.bash
set -u
python -c 'import torch, rclpy; print("OK", torch.__version__)'
echo
echo "Next:"
echo "  source $(dirname "$0")/nomad_wsl_env.sh"
echo "  bash $(dirname "$0")/run_step1_train_rollouts_wsl.sh nomad_b40"