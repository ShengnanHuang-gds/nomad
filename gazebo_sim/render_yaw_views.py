#!/usr/bin/env python3
"""Render labeled image-only heading data in an isolated camera-only Gazebo world."""

from argparse import ArgumentParser
from contextlib import suppress
from functools import partial
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET

from PIL import Image

WORLD_NAME = "nomad_yaw_views"
# Verified clear in the WSL house_run_02 sensor capture. This is an offline
# training-area anchor. It is not loaded by navigation or a map exporter.
CENTER = (0.008, 3.837)
BASE_Z = 0.010


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def build_world(house, burger, destination):
    scene = ET.parse(house)
    world = scene.find("world")
    if world is None:
        raise ValueError("missing world in the installed house SDF")
    world.set("name", WORLD_NAME)
    if world.find(".//sensor") is not None:
        raise ValueError("expected a house world with no robot sensors")
    # A camera-only renderer has no controllers, pose changes or robot motion.
    for plugin in world.findall("plugin"):
        if plugin.get("name") not in {"gz::sim::systems::Physics", "gz::sim::systems::Sensors"}:
            world.remove(plugin)
    if not any(p.get("name") == "gz::sim::systems::Sensors" for p in world.findall("plugin")):
        raise ValueError("house world must have the Gazebo Sensors system")

    link = ET.parse(burger).find("./model/link[@name='camera_link']")
    if link is None:
        raise ValueError("missing burger_cam camera_link")
    sensor = link.find("./sensor[@type='wideanglecamera']")
    if sensor is None or sensor.find("camera") is None:
        raise ValueError("expected the installed burger_cam wide-angle sensor")
    pose = link.find("pose")
    offset = tuple(map(float, pose.text.split())) if pose is not None and pose.text else ()
    if (len(offset) != 6 or not all(map(math.isfinite, offset)) or pose.get("relative_to")
            or any(offset[3:]) or sensor.find("pose") is not None):
        raise ValueError("unsupported camera extrinsics; check the effective burger_cam SDF")
    camera = sensor.find("camera")
    if (camera.findtext("image/width"), camera.findtext("image/height"), camera.findtext("image/format")) != (
        "320", "240", "R8G8B8"
    ):
        raise ValueError("unsupported burger_cam image format")

    rig = ET.SubElement(world, "model", name="nomad_camera_rig")
    ET.SubElement(rig, "static").text = "true"
    views = []
    dx, dy, dz = offset[:3]
    for index, yaw_deg in enumerate(range(-90, 91, 15)):
        yaw = math.radians(yaw_deg)
        position = [CENTER[0] + dx * math.cos(yaw) - dy * math.sin(yaw),
                    CENTER[1] + dx * math.sin(yaw) + dy * math.cos(yaw), BASE_Z + dz]
        name = f"view_{index:02d}"
        topic = f"/{WORLD_NAME}/{name}/image"
        view_link = ET.SubElement(rig, "link", name=name)
        ET.SubElement(view_link, "pose").text = " ".join(map(str, [*position, 0.0, 0.0, yaw]))
        view_sensor = ET.fromstring(ET.tostring(sensor))
        view_sensor.find("topic").text = topic
        view_sensor.find("update_rate").text = "1"
        view_sensor.find("visualize").text = "false"
        view_sensor.find("gz_frame_id").text = name
        view_sensor.find("./camera/camera_info_topic").text = f"/{WORLD_NAME}/{name}/camera_info"
        view_link.append(view_sensor)
        views.append({"file": f"{name}.png", "topic": topic, "camera_position_xyz_m": position,
                      "yaw_degrees": yaw_deg})
    scene.write(destination, encoding="utf-8", xml_declaration=True)
    return views


def rgb_image(message, rgb_type):
    if (message.width, message.height, message.pixel_format_type) != (320, 240, rgb_type):
        raise ValueError("unexpected Gazebo image format")
    if message.step < 3 * message.width or len(message.data) != message.step * message.height:
        raise ValueError("invalid Gazebo row stride")
    return Image.frombytes("RGB", (message.width, message.height), message.data, "raw", "RGB",
                           message.step, 1)


def capture(world, output, resources, views, deadline_s):
    # Set these before importing the Gazebo bindings so this run has its own
    # transport discovery domain throughout startup, collection and cleanup.
    os.environ["GZ_PARTITION"] = f"{WORLD_NAME}_{uuid.uuid4().hex}"
    os.environ["GZ_IP"] = "127.0.0.1"
    os.environ.pop("GZ_RELAY", None)
    resource_path = os.environ.get("GZ_SIM_RESOURCE_PATH")
    os.environ["GZ_SIM_RESOURCE_PATH"] = str(resources) + (f":{resource_path}" if resource_path else "")

    from gz.msgs10.image_pb2 import Image as GzImage, RGB_INT8
    from gz.transport13 import Node

    samples = {}
    topics = [view["topic"] for view in views]

    def collect(topic, message):
        stamp = message.header.stamp
        stamp_ns = stamp.sec * 10**9 + stamp.nsec
        if stamp_ns > 0:
            samples.setdefault(topic, (stamp_ns, message))

    node = Node()
    for topic in topics:
        if not node.subscribe(GzImage, topic, partial(collect, topic)):
            raise RuntimeError(f"could not subscribe to {topic}")
    log = output / "gazebo.log"
    with log.open("w", encoding="utf-8") as stream:
        command = ["gz", "sim", "-s", "-r", "--headless-rendering", "-v", "3", str(world)]
        sim = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            end = time.monotonic() + deadline_s
            while len(samples) < len(topics) and sim.poll() is None and time.monotonic() < end:
                time.sleep(0.10)
            missing = [topic for topic in topics if topic not in samples]
            if missing:
                raise RuntimeError(f"Gazebo did not render {len(missing)} of {len(topics)} views; see {log}")
        finally:
            try:
                if sim.poll() is None:
                    with suppress(ProcessLookupError):
                        os.killpg(sim.pid, signal.SIGTERM)
                    try:
                        sim.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        with suppress(ProcessLookupError):
                            os.killpg(sim.pid, signal.SIGKILL)
                        sim.wait()
            finally:
                for topic in topics:
                    node.unsubscribe(topic)

    seen_pixels = set()
    for view in views:
        stamp_ns, message = samples[view["topic"]]
        image = rgb_image(message, RGB_INT8)
        if max(high - low for low, high in image.getextrema()) < 8:
            raise ValueError(f"blank or nearly uniform render for {view['topic']}")
        pixel_sha = sha256(image.tobytes()).hexdigest()
        if pixel_sha in seen_pixels:
            raise ValueError(f"duplicate rendered image for {view['topic']}")
        seen_pixels.add(pixel_sha)
        path = output / view["file"]
        image.save(path)
        view.update(image_stamp_ns=stamp_ns, png_sha256=digest(path))


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="new output directory")
    parser.add_argument("--share", type=Path, help="installed turtlebot3_gazebo package share directory")
    parser.add_argument("--prepare-only", action="store_true", help="build SDF without running Gazebo")
    parser.add_argument("--timeout", type=float, default=150, help="renderer timeout in wall seconds")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("timeout must be positive and finite")
    share = args.share
    if share is None:
        share = Path(subprocess.check_output(["ros2", "pkg", "prefix", "--share", "turtlebot3_gazebo"], text=True).strip())
    share = share.resolve()
    house = share / "worlds/turtlebot3_house.world"
    burger = share / "models/turtlebot3_burger_cam/model.sdf"
    output = args.out.resolve()
    output.mkdir(parents=True)
    world = output / "camera_only.sdf"
    views = build_world(house, burger, world)
    manifest = {
        "kind": "synthetic_heading_pilot", "world_source_sha256": digest(house),
        "camera_model_source_sha256": digest(burger), "camera_only_sdf_sha256": digest(world),
        "anchor": "house_run_02 training-area spawn", "camera_pitch_degrees": 0,
        "intended_use": "offline data generation only", "views": views,
    }
    if not args.prepare_only:
        capture(world, output, share / "models", views, args.timeout)
    name = "planned_views.json" if args.prepare_only else "manifest.json"
    (output / name).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{len(views)} views {'planned' if args.prepare_only else 'rendered'} at {output}", flush=True)


if __name__ == "__main__":
    main()
