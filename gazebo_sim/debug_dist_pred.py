#!/usr/bin/env python3
"""Sanity-check dist_pred: teach frames vs topomap vs optional live /camera/image_raw."""

from __future__ import annotations

import argparse
import math
import pickle
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch
import yaml
from PIL import Image as PILImage

REPO = Path(__file__).resolve().parents[1]
VT = REPO / "visualnav-transformer"
DEPLOY = VT / "deployment"
TRAIN = VT / "train"
sys.path.insert(0, str(TRAIN))
sys.path.insert(0, str(DEPLOY / "src"))

from utils import load_model, to_numpy, transform_images  # noqa: E402

GZ = Path(__file__).resolve().parent


def resolve_ckpt(rel: str) -> Path:
    p = (DEPLOY / rel).resolve()
    if not p.is_file():
        raise FileNotFoundError(p)
    return p


def load_train_config(rel_cfg: str) -> dict:
    with open(TRAIN / "config" / "defaults.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    with open((DEPLOY / "config" / rel_cfg).resolve(), encoding="utf-8") as f:
        cfg.update(yaml.safe_load(f))
    return cfg


def load_topomap(name: str) -> list[PILImage.Image]:
    d = DEPLOY / "topomaps" / "images" / name
    paths = sorted(d.iterdir(), key=lambda p: int(p.stem))
    return [PILImage.open(p).convert("RGB") for p in paths if p.suffix.lower() in (".png", ".jpg")]


def dist_matrix(
    model: torch.nn.Module,
    mp: dict,
    device: torch.device,
    obs_stack: list[PILImage.Image],
    goals: list[PILImage.Image],
) -> np.ndarray:
    ctx = mp["context_size"]
    need = ctx + 1
    stack = obs_stack[-need:] if len(obs_stack) >= need else obs_stack * need
    stack = stack[-need:]
    obs = transform_images(stack, mp["image_size"], center_crop=False)
    obs = torch.cat(torch.split(obs, 3, dim=1), dim=1).to(device)
    mask = torch.zeros(1, dtype=torch.long, device=device)
    goal_batch = torch.concat(
        [
            transform_images(g, mp["image_size"], center_crop=False).to(device)
            for g in goals
        ],
        dim=0,
    )
    n = goal_batch.shape[0]
    cond = model(
        "vision_encoder",
        obs_img=obs.repeat(n, 1, 1, 1),
        goal_img=goal_batch,
        input_goal_mask=mask.repeat(n),
    )
    return to_numpy(model("dist_pred_net", obsgoal_cond=cond).flatten())


def pil_mse(a: PILImage.Image, b: PILImage.Image) -> float:
    aa = np.asarray(a.resize((96, 96)), dtype=np.float32)
    bb = np.asarray(b.resize((96, 96)), dtype=np.float32)
    return float(np.mean((aa - bb) ** 2))


def grab_live_camera(
    wait_s: float = 10.0,
    *,
    skip_frames: int = 25,
    save_path: Path | None = None,
) -> tuple[PILImage.Image | None, str]:
    """Return latest camera frame after warmup; include short /odom summary."""
    import math
    import time

    import rclpy
    from nav_msgs.msg import Odometry
    from rclpy.node import Node
    from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
    from sensor_msgs.msg import Image

    cam_qos = QoSProfile(
        depth=4,
        reliability=ReliabilityPolicy.BEST_EFFORT,
        history=HistoryPolicy.KEEP_LAST,
    )
    odom_qos = QoSProfile(
        depth=5,
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.VOLATILE,
        history=HistoryPolicy.KEEP_LAST,
    )

    class _Grab(Node):
        def __init__(self) -> None:
            super().__init__("debug_dist_grab")
            self.pil: PILImage.Image | None = None
            self.n_img = 0
            self.odom_xy: tuple[float, float] | None = None
            self.odom_yaw: float | None = None
            self.create_subscription(Image, "/camera/image_raw", self._cb_img, cam_qos)
            self.create_subscription(Odometry, "/odom", self._cb_odom, odom_qos)

        def _cb_img(self, msg: Image) -> None:
            self.n_img += 1
            if self.n_img <= skip_frames:
                return
            enc = msg.encoding.lower()
            ch = 3 if enc in ("rgb8", "bgr8") else 4
            img = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, ch)
            if enc.startswith("bgr"):
                img = img[:, :, :3][:, :, ::-1]
            elif ch == 4:
                img = img[:, :, :3]
            self.pil = PILImage.fromarray(img, "RGB")

        def _cb_odom(self, msg: Odometry) -> None:
            p = msg.pose.pose.position
            q = msg.pose.pose.orientation
            self.odom_xy = (float(p.x), float(p.y))
            self.odom_yaw = math.atan2(
                2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)
            )

    if rclpy.ok():
        rclpy.shutdown()
    rclpy.init()
    node = _Grab()
    t0 = time.time()
    pil: PILImage.Image | None = None
    odom_note = "odom=?"
    try:
        while time.time() - t0 < wait_s:
            rclpy.spin_once(node, timeout_sec=0.05)
            if node.pil is not None:
                pil = node.pil.copy()
        if pil is not None and save_path is not None:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            pil.save(save_path, quality=92)
        if node.odom_xy is not None and node.odom_yaw is not None:
            odom_note = (
                f"odom=({node.odom_xy[0]:.3f},{node.odom_xy[1]:.3f}) "
                f"yaw={math.degrees(node.odom_yaw):.1f}° frames={node.n_img}"
            )
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    return pil, odom_note


def run_model(
    model_key: str,
    topomap: str,
    run: str,
    radius: int,
    live: bool,
    *,
    wait_s: float,
    save_live: Path | None,
) -> None:
    with open(DEPLOY / "config" / "models.yaml", encoding="utf-8") as f:
        models = yaml.safe_load(f)
    mp = load_train_config(models[model_key]["config_path"])
    ckpt = resolve_ckpt(models[model_key]["ckpt_path"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(str(ckpt), mp, device).eval()

    topo = load_topomap(topomap)
    teach0 = PILImage.open(GZ / run / "0.jpg").convert("RGB")
    topo0 = topo[0]
    print(f"\n=== model={model_key} topomap={topomap} ({len(topo)} nodes) device={device} ===")
    print(f"pixel MSE teach0.jpg vs topomap/0: {pil_mse(teach0, topo0):.2f} (0=same file)")

    ctx_stack = [teach0] * (mp["context_size"] + 1)
    self_goals = topo[0 : min(radius + 1, len(topo))]
    d_self = dist_matrix(model, mp, device, ctx_stack, self_goals)
    for i, v in enumerate(d_self):
        mark = "  <-- self" if i == 0 else ""
        print(f"  dist_pred(obs=teach0 x{mp['context_size']+1}, goal=node {i}): {v:.3f}{mark}")

    live_pil: PILImage.Image | None = None
    if live:
        assert_at_teach_start(run)
        live_pil, odom_note = grab_live_camera(
            min(wait_s, 6.0), skip_frames=15, save_path=save_live
        )
        print(f"live snapshot at teach t=0: {odom_note}")
        if save_live and live_pil is not None:
            print(f"saved {save_live}")
    if live_pil is not None:
        print(f"pixel MSE live /camera vs topomap/0: {pil_mse(live_pil, topo0):.2f}")
        print(f"pixel MSE live /camera vs teach0.jpg: {pil_mse(live_pil, teach0):.2f}")
        if pil_mse(live_pil, teach0) > 2000:
            print(
                "WARN: MSE still huge — teach was likely recorded in another sim look/pose "
                "(not fixed by yaw only). Open teach0.jpg vs saved live JPG side-by-side; "
                "if different, re-record house_run_06 + export_topomap under current Gazebo."
            )
        live_stack = [live_pil] * (mp["context_size"] + 1)
        d_live = dist_matrix(model, mp, device, live_stack, self_goals)
        for i, v in enumerate(d_live):
            print(f"  dist_pred(obs=live x{mp['context_size']+1}, goal=node {i}): {v:.3f}")
    elif live:
        print("WARN: no /camera/image_raw (start Gazebo in terminal 1)")

    close = 5
    best_self = float(np.min(d_self))
    print(f"min dist (teach0 self-match): {best_self:.3f}  close_threshold={close}  ok={best_self < close}")


DESK_COMPARE = Path("/mnt/c/Users/61078/Desktop/nomad_house06_compare")


def gate_live_check(
    model_key: str,
    topomap: str,
    run: str,
    wait_s: float,
    max_mse: float,
    max_dist: float,
) -> tuple[bool, str]:
    assert_at_teach_start(run)
    with open(DEPLOY / "config" / "models.yaml", encoding="utf-8") as f:
        models = yaml.safe_load(f)
    mp = load_train_config(models[model_key]["config_path"])
    ckpt = resolve_ckpt(models[model_key]["ckpt_path"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(str(ckpt), mp, device).eval()
    topo = load_topomap(topomap)
    teach0 = PILImage.open(GZ / run / "0.jpg").convert("RGB")
    live_pil, note = grab_live_camera(min(wait_s, 6.0), skip_frames=15, save_path=None)
    if live_pil is None:
        return False, "gate: no live frame"
    mse = pil_mse(live_pil, teach0)
    ctx = [live_pil] * (mp["context_size"] + 1)
    d0 = float(
        dist_matrix(model, mp, device, ctx, [topo[0]])[0]
    )
    ok = mse <= max_mse and d0 <= max_dist
    msg = f"gate mse={mse:.1f} (max {max_mse}) dist0={d0:.3f} (max {max_dist}) {note}"
    return ok, msg


def teach_start_yaw(run: str) -> float:
    pkl = GZ / run / "traj_data.pkl"
    with open(pkl, "rb") as f:
        d = pickle.load(f)
    return float(d["yaw"][0])


def read_odom_snapshot(timeout_s: float = 5.0) -> tuple[float, float, float] | None:
    """Current /odom (x, y, yaw)."""
    import time

    import rclpy
    from nav_msgs.msg import Odometry
    from rclpy.node import Node
    from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

    qos = QoSProfile(
        depth=5,
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.VOLATILE,
        history=HistoryPolicy.KEEP_LAST,
    )

    class _O(Node):
        def __init__(self) -> None:
            super().__init__("debug_odom_snap")
            self.pose: tuple[float, float, float] | None = None
            self.create_subscription(Odometry, "/odom", self._cb, qos)

        def _cb(self, msg: Odometry) -> None:
            p = msg.pose.pose.position
            q = msg.pose.pose.orientation
            yaw = math.atan2(
                2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)
            )
            self.pose = (float(p.x), float(p.y), yaw)

    if rclpy.ok():
        rclpy.shutdown()
    rclpy.init()
    node = _O()
    t0 = time.time()
    try:
        while time.time() - t0 < timeout_s:
            rclpy.spin_once(node, timeout_sec=0.1)
            if node.pose is not None:
                return node.pose
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return None


def assert_at_teach_start(run: str, *, max_xy_m: float = 0.25, max_yaw_deg: float = 8.0) -> None:
    """live vs teach0 only valid at episode t=0 (after verify, before any nav)."""
    target_yaw = teach_start_yaw(run)
    odom = read_odom_snapshot()
    if odom is None:
        raise SystemExit("no /odom — start Gazebo + verify_06_spawn first")
    x, y, yaw = odom
    yaw_err = abs((yaw - target_yaw + math.pi) % (2 * math.pi) - math.pi)
    xy_err = math.hypot(x, y)
    print(
        f"odom check: xy=({x:.3f},{y:.3f}) err={xy_err:.3f}m "
        f"yaw={math.degrees(yaw):.1f}° teach={math.degrees(target_yaw):.1f}° "
        f"yaw_err={math.degrees(yaw_err):.1f}°",
        flush=True,
    )
    if xy_err > max_xy_m or math.degrees(yaw_err) > max_yaw_deg:
        raise SystemExit(
            "refusing live grab: robot not at teach START (t=0). "
            "Do NOT run holdout/eval first. T1 relaunch → verify_06_spawn → "
            "then debug_dist_pred --pull-desktop or --live immediately. "
            f"(need |xy|<{max_xy_m}m, yaw_err<{max_yaw_deg}°)"
        )


def pull_desktop_compare(topomap: str, run: str, *, wait_s: float, model: str) -> None:
    """Copy teach/top (+ optional live) to Windows Desktop and write compare.html."""
    desk = DESK_COMPARE
    desk.mkdir(parents=True, exist_ok=True)
    teach = GZ / run / "0.jpg"
    top = DEPLOY / "topomaps" / "images" / topomap / "0.png"
    shutil.copy2(teach, desk / "teach0_house06.jpg")
    if top.is_file():
        shutil.copy2(top, desk / "topomap0_house06.png")

    live_path = desk / "live_house06.jpg"
    grabbed = False
    proc = subprocess.run(
        ["bash", "-lc", "source /opt/ros/jazzy/setup.bash 2>/dev/null; timeout 6 ros2 topic list"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if "/camera/image_raw" in (proc.stdout or ""):
        print(
            "--wait-s is camera warmup only (skip bad first frames), NOT drive time.",
            flush=True,
        )
        assert_at_teach_start(run)
        grab_dest = GZ / f"debug_live_{topomap}.jpg"
        live_pil, note = grab_live_camera(
            min(wait_s, 6.0), skip_frames=15, save_path=grab_dest
        )
        print(f"live grab at t=0: {note}")
        if live_pil is not None and grab_dest.is_file():
            shutil.copy2(grab_dest, live_path)
            grabbed = True
    else:
        print("WARN: no /camera/image_raw — teach/top only (start Gazebo + verify first)")

    live_block = (
        '<img src="live_house06.jpg" alt="live">'
        if grabbed
        else "<p>no live yet — Gazebo + verify then re-run --pull-desktop</p>"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset=utf-8><title>house_06</title>"
        "<style>body{background:#111;color:#eee;padding:16px}"
        ".row{display:flex;gap:12px;flex-wrap:wrap}img{max-width:420px}</style>"
        "</head><body><h1>house_06</h1><div class=\"row\">"
        "<div><h2>teach0</h2><img src=\"teach0_house06.jpg\"></div>"
        "<div><h2>topomap0</h2><img src=\"topomap0_house06.png\"></div>"
        f"<div><h2>live</h2>{live_block}</div></div>"
        "<p>C:\\Users\\61078\\Desktop\\nomad_house06_compare</p></body></html>"
    )
    (desk / "compare.html").write_text(html, encoding="utf-8")
    print(f"Desktop folder: {desk}")
    subprocess.run(["explorer.exe", r"C:\Users\61078\Desktop\nomad_house06_compare"], check=False)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--pull-desktop",
        action="store_true",
        help="copy teach/top/live to Desktop/nomad_house06_compare",
    )
    p.add_argument("--model", default="nomad_b40")
    p.add_argument("--topomap", default="house_06")
    p.add_argument("--run", default="house_run_06")
    p.add_argument("--radius", type=int, default=4)
    p.add_argument("--live", action="store_true")
    p.add_argument(
        "--wait-s",
        type=float,
        default=4.0,
        help="max seconds to skip first camera frames (robot must stay still at verify pose)",
    )
    p.add_argument(
        "--save-live",
        default="",
        help="write live RGB frame (default under gazebo_sim/ if --live and empty)",
    )
    p.add_argument("--compare-models", default="", help="comma list e.g. nomad_b40,nomad_gazebo")
    p.add_argument(
        "--gate",
        action="store_true",
        help="exit 0 if live MSE/dist node0 pass thresholds (needs verify pose)",
    )
    p.add_argument("--max-mse", type=float, default=2500.0)
    p.add_argument("--max-dist", type=float, default=5.0)
    args = p.parse_args()
    if args.gate:
        ok, msg = gate_live_check(
            args.model,
            args.topomap,
            args.run,
            args.wait_s,
            args.max_mse,
            args.max_dist,
        )
        print(msg)
        raise SystemExit(0 if ok else 1)
    if args.pull_desktop:
        pull_desktop_compare(
            args.topomap, args.run, wait_s=args.wait_s, model=args.model
        )
        return
    save_live: Path | None = None
    if args.live:
        save_live = (
            Path(args.save_live)
            if args.save_live
            else GZ / f"debug_live_{args.topomap}.jpg"
        )
    keys = [args.model]
    if args.compare_models:
        keys = [k.strip() for k in args.compare_models.split(",") if k.strip()]
    for k in keys:
        run_model(
            k,
            args.topomap,
            args.run,
            args.radius,
            args.live,
            wait_s=args.wait_s,
            save_live=save_live,
        )


if __name__ == "__main__":
    main()