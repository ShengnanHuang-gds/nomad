set -e
VENV=/home/hsnnb/nomad_ros_venv/bin/pip
$VENV uninstall -y torch torchvision 2>/dev/null || true
$VENV install torch torchvision --index-url https://download.pytorch.org/whl/cu124 -q
/home/hsnnb/nomad_ros_venv/bin/python -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')"