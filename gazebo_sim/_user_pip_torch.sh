set -e
cd /tmp
curl -fsSL https://mirrors.aliyun.com/pypi/get-pip.py -o get-pip.py || curl -fsSL http://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py --use
export PATH="$HOME/.local/bin:$PATH"
python3 -m pip install --user -i https://mirrors.aliyun.com/pypi/simple/ torch torchvision --index-url https://mirrors.aliyun.com/pytorch-wheels/cpu 2>/dev/null || python3 -m pip install --user -i https://pypi.tuna.tsinghua.edu.cn/simple torch
python3 -m pip install --user -i https://pypi.tuna.tsinghua.edu.cn/simple diffusers pyyaml pillow numpy opencv-python-headless
source /opt/ros/jazzy/setup.bash
python3 -c 'import torch, rclpy; print("OK", torch.__version__)'