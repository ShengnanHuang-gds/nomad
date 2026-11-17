set -e
source /home/hsnnb/miniconda3/etc/profile.d/conda.sh
conda create -n nomad_nav python=3.12 pip -y
conda run -n nomad_nav python -m pip install -q torch --index-url https://download.pytorch.org/whl/cpu
conda run -n nomad_nav python -m pip install -q diffusers transformers efficientnet-pytorch opencv-python-headless pyyaml pillow numpy
source /opt/ros/jazzy/setup.bash
PY=/home/hsnnb/miniconda3/envs/nomad_nav/bin/python
export PYTHONPATH="/opt/ros/jazzy/lib/python3.12/site-packages:${PYTHONPATH:-}"
$PY -c "import torch, rclpy; print('OK', torch.__version__)"