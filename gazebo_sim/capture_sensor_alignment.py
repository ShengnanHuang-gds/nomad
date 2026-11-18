#!/usr/bin/env python3
"""Read-only, timestamped camera/odom/Gazebo capture for a short Jazzy sim run."""

import argparse
from bisect import bisect_left
import json
import math
from pathlib import Path
import time

NS_PER_SECOND = 1_000_000_000
MAX_SIDE_NS = 50_000_000
IMAGE_TOPIC = "/camera/image_raw"
ODOM_TOPIC = "/odom"


def stamped(stamp, nsec):
    return int(stamp.sec) * NS_PER_SECOND + int(nsec)


def xyz(point):
    return [point.x, point.y, point.z]


def xyzw(rotation):
    return xyz(rotation) + [rotation.w]


def yaw_deg(quaternion):
    x, y, z, w = quaternion
    norm = x*x + y*y + z*z + w*w
    if not math.isclose(norm, 1.0, abs_tol=0.01):
        raise ValueError("invalid orientation quaternion")
    return math.degrees(math.atan2(2 * (w*z + x*y), norm - 2 * (y*y + z*z)))


def angle_delta(start, end):
    return (end - start + 180) % 360 - 180


def align_images(images, poses, odom):
    """Interpolate short-interval ZYX yaw at the image header stamp."""
    def prepare(samples):
        stamps = [sample["stamp_ns"] for sample in samples]
        if any(stamp <= 0 for stamp in stamps):
            raise ValueError("zero or negative pose stamp")
        if any(b <= a for a, b in zip(stamps, stamps[1:])):
            raise ValueError("pose stamps must be strictly increasing within one capture")
        return stamps, [yaw_deg(sample["orientation_xyzw"]) for sample in samples]

    def at(stamp, stream):
        stamps, yaws = stream
        i = bisect_left(stamps, stamp)
        if i < len(stamps) and stamps[i] == stamp:
            return {"yaw_deg": yaws[i], "before_ms": 0.0, "after_ms": 0.0}
        before = stamp - stamps[i - 1] if i else None
        after = stamps[i] - stamp if i < len(stamps) else None
        yaw = None
        if before is not None and after is not None and max(before, after) <= MAX_SIDE_NS:
            turn = angle_delta(yaws[i - 1], yaws[i])
            yaw = angle_delta(0.0, yaws[i - 1] + before / (before + after) * turn)
        return {"yaw_deg": yaw,
                "before_ms": None if before is None else before / 1e6,
                "after_ms": None if after is None else after / 1e6}

    pose_stream, odom_stream = prepare(poses), prepare(odom)
    return [
        {"file": image["file"], "stamp_ns": image["stamp_ns"],
         "model": at(image["stamp_ns"], pose_stream), "odom": at(image["stamp_ns"], odom_stream)}
        for image in images
    ]


def append_sample(samples, sample, errors, zero_stamps, source):
    stamp = sample["stamp_ns"]
    if stamp <= 0:
        zero_stamps[source] += 1
        return
    if samples:
        previous = samples[-1]["stamp_ns"]
        if stamp < previous:
            errors.add(f"{source} timestamp went backwards")
            return
        if stamp == previous:
            return
    samples.append(sample)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="new output directory")
    parser.add_argument("--world", default="default")
    parser.add_argument("--model", default="burger_cam")
    parser.add_argument("--entity-id", type=int, required=True, help="Gazebo model ID from gz model")
    parser.add_argument("--sim-seconds", type=float, default=4.0)
    parser.add_argument("--wall-seconds", type=float, default=45.0)
    args = parser.parse_args()
    if not (args.entity_id > 0 and 0 < args.sim_seconds <= 10 and 0 < args.wall_seconds <= 90):
        parser.error("use a positive entity ID, 0 < sim seconds <= 10 and 0 < wall seconds <= 90")
    if args.out.exists():
        parser.error(f"output directory already exists: {args.out}")

    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from nav_msgs.msg import Odometry
    from rosgraph_msgs.msg import Clock
    from sensor_msgs.msg import Image
    from gz.msgs10.pose_v_pb2 import Pose_V
    from gz.transport13 import Node
    from PIL import Image as PilImage

    pose_topic = f"/world/{args.world}/dynamic_pose/info"
    poses, odom, images, image_data, clocks = [], [], [], [], []
    errors = set()
    zero_stamps = dict.fromkeys(("Gazebo model", "odom", "image", "/clock"), 0)

    def collect_pose(message):
        stamp = message.header.stamp
        for pose in message.pose:
            if pose.id == args.entity_id and pose.name == args.model:
                append_sample(poses, {
                    "stamp_ns": stamped(stamp, stamp.nsec), "entity_id": pose.id,
                    "name": pose.name, "position_xyz": xyz(pose.position),
                    "orientation_xyzw": xyzw(pose.orientation),
                }, errors, zero_stamps, "Gazebo model")

    def collect_odom(message):
        stamp = message.header.stamp
        pose = message.pose.pose
        append_sample(odom, {
            "stamp_ns": stamped(stamp, stamp.nanosec), "frame_id": message.header.frame_id,
            "child_frame_id": message.child_frame_id, "position_xyz": xyz(pose.position),
            "orientation_xyzw": xyzw(pose.orientation),
        }, errors, zero_stamps, "odom")

    def collect_image(message):
        stamp = message.header.stamp
        if (message.width, message.height) != (320, 240):
            errors.add("unexpected image size; expected native burger_cam 320x240")
            return
        if (message.encoding not in ("rgb8", "bgr8") or message.step < 3 * message.width
                or len(message.data) != message.height * message.step):
            errors.add("unsupported image buffer")
            return
        if len(images) >= 320:
            errors.add("image count exceeded capture limit")
            return
        append_sample(images, {
            "stamp_ns": stamped(stamp, stamp.nanosec), "frame_id": message.header.frame_id,
            "file": f"images/{len(images):04d}.png", "width": message.width,
            "height": message.height, "encoding": message.encoding, "step": message.step,
        }, errors, zero_stamps, "image")
        if len(image_data) < len(images):
            image_data.append(bytes(message.data))

    def collect_clock(message):
        clock = message.clock
        append_sample(clocks, {"stamp_ns": stamped(clock, clock.nanosec)}, errors, zero_stamps, "/clock")

    gz_node = Node()
    rclpy.init()
    node = rclpy.create_node("nomad_sensor_alignment")
    started = time.monotonic()
    try:
        if not gz_node.subscribe(Pose_V, pose_topic, collect_pose):
            raise RuntimeError(f"could not subscribe to {pose_topic}")
        node.create_subscription(Image, IMAGE_TOPIC, collect_image, qos_profile_sensor_data)
        node.create_subscription(Odometry, ODOM_TOPIC, collect_odom, qos_profile_sensor_data)
        node.create_subscription(Clock, "/clock", collect_clock, qos_profile_sensor_data)
        while rclpy.ok() and not errors and time.monotonic() - started < args.wall_seconds:
            rclpy.spin_once(node, timeout_sec=0.05)
            if clocks and clocks[-1]["stamp_ns"] - clocks[0]["stamp_ns"] >= args.sim_seconds * NS_PER_SECOND:
                break
    finally:
        elapsed = time.monotonic() - started
        gz_node.unsubscribe(pose_topic)
        node.destroy_node()
        rclpy.try_shutdown()

    if len({image["frame_id"] for image in images}) > 1:
        errors.add("image frame changed during capture")
    if len({(sample["frame_id"], sample["child_frame_id"]) for sample in odom}) > 1:
        errors.add("odom frames changed during capture")
    if len(clocks) < 2:
        errors.add("no advancing /clock")
    for name, samples in (("image", images), ("odom", odom), ("Gazebo model", poses)):
        if not samples:
            errors.add(f"no stamped {name} samples")

    aligned = []
    if not errors:
        try:
            aligned = align_images(images, poses, odom)
        except ValueError as exc:
            errors.add(str(exc))

    args.out.mkdir(parents=True)
    (args.out / "images").mkdir()
    for meta, raw in zip(images, image_data, strict=True):
        mode = "RGB" if meta["encoding"] == "rgb8" else "BGR"
        PilImage.frombytes("RGB", (meta["width"], meta["height"]), raw,
                           "raw", mode, meta["step"], 1).save(args.out / meta["file"])
    matched = [row for row in aligned if all(row[key]["yaw_deg"] is not None for key in ("model", "odom"))]
    sim_s = (clocks[-1]["stamp_ns"] - clocks[0]["stamp_ns"]) / NS_PER_SECOND if clocks else None
    result = {
        "pose_topic": pose_topic, "image_topic": IMAGE_TOPIC, "odom_topic": ODOM_TOPIC,
        "model_name": args.model, "entity_id": args.entity_id, "max_bracket_side_ms": MAX_SIDE_NS / 1e6,
        "wall_seconds": elapsed, "sim_seconds": sim_s,
        "errors": sorted(errors), "zero_stamp_count": zero_stamps,
        "jointly_aligned_image_count": len(matched),
        "clock": clocks, "images": images, "model_samples": poses, "odom_samples": odom,
        "alignment": aligned,
    }
    (args.out / "samples.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{args.out}: {len(matched)}/{len(images)} images aligned with both pose streams")
    if errors or not matched:
        raise SystemExit("; ".join(sorted(errors)) or "no images bracketed by both pose streams")


if __name__ == "__main__":
    main()
