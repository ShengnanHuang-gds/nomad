"""Teleport TurtleBot3 in Gazebo Sim (gz service set_pose + entity auto-detect)."""

from __future__ import annotations

import math
import os
import re
import subprocess
import time

DEFAULT_WORLD = os.environ.get("GZ_WORLD", "default")
DEFAULT_ENTITIES = (
    os.environ.get("GZ_ROBOT_ENTITY", "").strip(),
    "burger_cam",
    "turtlebot3_burger_cam",
    "turtlebot3",
)


def entities_from_ros_topics() -> list[str]:
    try:
        proc = subprocess.run(
            ["ros2", "topic", "list"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    names: list[str] = []
    for line in (proc.stdout or "").splitlines():
        m = re.match(r"^/model/([^/]+)/", line.strip())
        if m and m.group(1) not in names:
            names.append(m.group(1))
    return names


def list_gazebo_models(world: str = DEFAULT_WORLD) -> list[str]:
    try:
        proc = subprocess.run(
            ["gz", "model", "-l", "-w", world],
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    names: list[str] = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line or line.startswith("Available"):
            continue
        m = re.match(r"[-\s]*\d+\.\s+(\S+)", line)
        if m:
            names.append(m.group(1))
        elif re.match(r"^[\w][\w.-]*$", line):
            names.append(line)
    return names


def _unique_entities() -> tuple[str, ...]:
    out: list[str] = []
    for e in list(entities_from_ros_topics()) + list(DEFAULT_ENTITIES):
        if e and e not in out:
            out.append(e)
    for e in list_gazebo_models():
        if e not in out and ("burger" in e.lower() or "turtlebot" in e.lower()):
            out.append(e)
    return tuple(out)


def set_pose_entity_ros(
    entity: str,
    x: float,
    y: float,
    yaw: float,
    z: float = 0.01,
) -> bool:
    """Teleport via ros_gz_sim (works when gz CLI cannot reach the sim in WSL)."""
    cmd = (
        "source /opt/ros/jazzy/setup.bash 2>/dev/null; "
        f"export GZ_IP=${{GZ_IP:-127.0.0.1}}; "
        f"ros2 run ros_gz_sim set_entity_pose --name {entity} --type 2 "
        f"--pos {x:.5f} {y:.5f} {z:.5f} --euler 0 0 {yaw:.5f}"
    )
    try:
        proc = subprocess.run(
            ["bash", "-lc", cmd],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    if proc.returncode != 0 and proc.stderr:
        print(f"set_entity_pose({entity}): {proc.stderr.strip()[:300]}", flush=True)
    return proc.returncode == 0


def set_pose_entity(
    entity: str,
    x: float,
    y: float,
    yaw: float,
    world: str = DEFAULT_WORLD,
    z: float = 0.01,
) -> bool:
    zq, wq = math.sin(yaw / 2), math.cos(yaw / 2)
    req = (
        f'name: "{entity}" position: {{x: {x:.5f} y: {y:.5f} z: {z:.5f}}} '
        f"orientation: {{x: 0 y: 0 z: {zq:.6f} w: {wq:.6f}}}"
    )
    proc = subprocess.run(
        [
            "gz",
            "service",
            "-s",
            f"/world/{world}/set_pose",
            "--reqtype",
            "gz.msgs.Pose",
            "--reptype",
            "gz.msgs.Boolean",
            "--timeout",
            "8000",
            "--req",
            req,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    lo = out.lower()
    if proc.returncode != 0:
        return False
    if "data: true" in lo or "data: 1" in lo:
        return True
    if "data: false" in lo or "data: 0" in lo:
        return False
    # Do not treat unknown/empty gz CLI output as success (disconnected sim).
    return False


def set_robot_pose(x: float, y: float, yaw: float, entity: str | None = None) -> str:
    candidates = (entity,) if entity else _unique_entities()
    if not any(candidates):
        candidates = ("turtlebot3_burger_cam", "burger_cam")
    errors: list[str] = []
    for name in candidates:
        if not name:
            continue
        if set_pose_entity_ros(name, x, y, yaw) or set_pose_entity(name, x, y, yaw):
            time.sleep(2.0)
            return name
        errors.append(name)
    models = list_gazebo_models() or entities_from_ros_topics()
    hint = f" entities={models}" if models else " (gz disconnected? export GZ_IP=127.0.0.1)"
    raise RuntimeError(
        f"set_pose failed for {errors}.{hint} "
        f"Try: export GZ_IP=127.0.0.1 GZ_ROBOT_ENTITY=burger_cam; T1 must run launch."
    )