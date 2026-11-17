#!/usr/bin/env bash
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
for py in python3 /home/hsnnb/miniconda3/bin/python /home/hsnnb/miniconda3/envs/habitat/bin/python /mnt/c/Users/61078/anaconda3/python.exe /mnt/c/Users/61078/anaconda3/envs/nomad_train/python.exe; do
  if ! command -v "$py" >/dev/null 2>&1 && ! test -x "$py"; then continue; fi
  t=$("$py" -c 'import torch; print(torch.__version__)' 2>/dev/null || echo no)
  if "$py" -c 'import rclpy' 2>/dev/null; then r=ok; else r=no; fi
  echo "$py torch=$t rclpy=$r"
done