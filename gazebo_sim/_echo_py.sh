#!/usr/bin/env bash
cd /mnt/c/Users/61078/Desktop/nomad
source gazebo_sim/nomad_wsl_env.sh
echo PY=$NOMAD_PY
$NOMAD_PY -c 'import torch; print(torch.__version__)'