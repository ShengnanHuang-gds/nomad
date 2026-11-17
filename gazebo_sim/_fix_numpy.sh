#!/usr/bin/env bash
/home/hsnnb/nomad_ros_venv/bin/pip install 'numpy<2' -q
/home/hsnnb/nomad_ros_venv/bin/python -c 'import numpy; print(numpy.__version__)'
