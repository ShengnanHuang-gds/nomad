"""Validate labeled offline renders and produce same-location heading pairs."""

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import cv2
import numpy as np
from PIL import Image

from audit_yaw_geometry import AngularFeatures, estimate_yaw, read_projection, wrap

PILOT = Path(__file__).resolve().parent / "visual_yaw_render_pilot"
# Candidate camera centers are archive frame indices in the existing training
# split. They select scene locations only; generated SDF angles supply labels.
TRAINING_ANCHORS = {
    "house_run_00": (5, 17, 29),
    "house_run_01": (4, 14, 22),
    "house_run_02": (0, 9, 22, 33),
    "house_run_03": (4, 15),
    "house_run_04": (3, 16),
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read_rendered_views(folder):
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("kind") not in {"synthetic_heading_pilot", "synthetic_heading_training_v1"}:
        raise ValueError(f"unrecognized render manifest: {manifest_path}")
    sdf = folder / "camera_only.sdf"
    if digest(sdf) != manifest["camera_only_sdf_sha256"]:
        raise ValueError(f"render world SHA256 mismatch: {sdf}")
    rig = ET.parse(sdf).find("./world/model[@name='nomad_camera_rig']")
    if rig is None or rig.findtext("static") != "true":
        raise ValueError(f"expected a static render rig: {sdf}")
    links = rig.findall("link")
    views = manifest["views"]
    if len(links) != 13 or len(views) != 13:
        raise ValueError(f"expected a full 13-view group: {folder}")
    files, yaws, pixels = [], [], set()
    for index, (view, link) in enumerate(zip(views, links, strict=True)):
        name = f"view_{index:02d}"
        path = folder / f"{name}.png"
        if (view["file"] != path.name or link.get("name") != name or digest(path) != view["png_sha256"]
                or view["image_stamp_ns"] <= 0):
            raise ValueError(f"invalid image identity or timestamp: {path}")
        pose = [float(item) for item in link.findtext("pose").split()]
        if (len(pose) != 6 or not np.allclose(pose[:3], view["camera_position_xyz_m"], atol=1e-8, rtol=0)
                or not math.isclose(pose[5], math.radians(view["yaw_degrees"]), abs_tol=1e-8)
                or link.findtext("sensor/topic") != view["topic"]):
            raise ValueError(f"render labels disagree with SDF: {path}")
        with Image.open(path) as image:
            if image.mode != "RGB" or image.size != (320, 240):
                raise ValueError(f"invalid image type or size: {path}")
            if max(high - low for low, high in image.getextrema()) < 8:
                raise ValueError(f"blank render: {path}")
            image_digest = sha256(image.tobytes()).hexdigest()
            if image_digest in pixels:
                raise ValueError(f"duplicate pixels in render group: {path}")
            pixels.add(image_digest)
        files.append(path)
        yaws.append(float(view["yaw_degrees"]))
    if not np.allclose(np.diff(yaws), 15.0, atol=1e-8, rtol=0):
        raise ValueError(f"expected ordered views spaced 15 degrees apart: {folder}")
    return manifest, files, yaws


def render_geometry(folder, files, yaws):
    feature = AngularFeatures(read_projection(folder / "camera_only.sdf"))
    images = [feature.extract(cv2.imread(str(file), cv2.IMREAD_GRAYSCALE), True) for file in files]
    rows = []
    for gap in range(1, len(images)):
        for start in range(len(images) - gap):
            goal = start + gap
            expected = yaws[goal] - yaws[start]
            estimate = estimate_yaw(images[start], images[goal])
            yaw = estimate["yaw_deg"]
            rows.append({"from": start, "to": goal, "expected_deg": expected, **estimate,
                         "error_deg": None if yaw is None else abs(float(wrap(yaw - expected)))})
    return rows


def load_rendered_training(root):
    cv2.setNumThreads(1)
    groups, report, pairs = {}, [], []
    accepted_centers, seen_groups = [], set()
    source = json.loads((PILOT / "manifest.json").read_text(encoding="utf-8"))
    for manifest_file in sorted(root.glob("*/manifest.json")):
        folder = manifest_file.parent
        manifest, files, yaws = read_rendered_views(folder)
        route, frame = manifest.get("source_route"), manifest.get("source_frame")
        if (manifest["kind"] != "synthetic_heading_training_v1" or frame not in TRAINING_ANCHORS.get(route, ())
                or folder.name != f"{route}_{frame:02d}"):
            raise ValueError(f"not a planned training anchor: {folder}")
        if any(manifest[k] != source[k] for k in ("world_source_sha256", "camera_model_source_sha256")):
            raise ValueError(f"scene or camera differs from the verified pilot: {folder}")
        center = np.asarray(manifest["anchor_xy_m"], dtype=float)
        endpoints = [manifest["views"][i]["camera_position_xyz_m"][:2] for i in (0, -1)]
        if (center.shape != (2,) or not np.isfinite(center).all()
                or not np.allclose(center, np.mean(endpoints, axis=0), atol=1e-8, rtol=0)):
            raise ValueError(f"invalid camera center: {folder}")
        audited = render_geometry(folder, files, yaws)
        adjacent = [r for r in audited if r["to"] == r["from"] + 1]
        consistent = sum(r["error_deg"] is not None and r["error_deg"] <= 3 for r in adjacent)
        # Avoid counting nearby duplicates as new scenes. This uses only the
        # offline anchors and never participates in training predictions.
        separated = all(np.linalg.norm(center - other) >= 0.4 for other in accepted_centers)
        signatures = frozenset(view["png_sha256"] for view in manifest["views"])
        duplicate = signatures in seen_groups
        accepted = consistent >= 8 and separated and not duplicate
        report.append({"anchor": folder.name, "route": route, "frame": frame,
                       "manifest_sha256": digest(manifest_file), "consistent_adjacent": consistent,
                       "separated": separated, "duplicate_group": duplicate, "accepted": accepted})
        if not accepted:
            continue
        accepted_centers.append(center)
        seen_groups.add(signatures)
        key = f"rendered:{folder.name}"
        groups[key] = files
        pairs.extend((key, i, j, math.radians(b - a))
                     for i, a in enumerate(yaws) for j, b in enumerate(yaws)
                     if i != j and abs(b - a) <= 90.000001)
    return groups, pairs, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="one pilot group or a training batch")
    parser.add_argument("--training-batch", action="store_true")
    args = parser.parse_args()
    cv2.setNumThreads(1)
    if args.training_batch:
        groups, pairs, report = load_rendered_training(args.folder)
        result = {"accepted_groups": len(groups), "pairs": len(pairs), "groups": report}
    else:
        _, files, yaws = read_rendered_views(args.folder)
        result = {"image_count": len(files), "pairs": render_geometry(args.folder, files, yaws)}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
