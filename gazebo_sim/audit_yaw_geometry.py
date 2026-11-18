#!/usr/bin/env python3
"""Offline angular correspondence audit for the burger_cam wide-angle renderer."""

import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import xml.etree.ElementTree as ET

import cv2
import numpy as np

from capture_sensor_alignment import align_images, angle_delta
from visual_stage_data import VisualStageData, extract_verified_handoff

HERE = Path(__file__).resolve().parent
# Fixed diagnostic criteria, applied equally to all routes and both image representations.
ANGLE_INLIER_DEG = 2.0
MIN_INLIERS = 8
MIN_SUPPORT_FRACTION = 0.60
SEQUENCE_STEP_NS = 600_000_000
MAX_SEQUENCE_GAP_NS = 900_000_000


def read_projection(sdf):
    camera = ET.parse(sdf).find(".//sensor[@type='wideanglecamera']/camera")
    width, height = (int(camera.findtext(f"image/{dim}")) for dim in ("width", "height"))
    lens = camera.find("lens")
    shift = float(lens.findtext("custom_function/c3", "0"))
    if (lens.findtext("scale_to_hfov") != "true" or lens.findtext("type") != "custom"
            or lens.findtext("custom_function/fun") != "tan" or shift != 0):
        raise ValueError("Expected the burger_cam HFOV-scaled custom tan lens with c3=0")
    c2 = float(lens.findtext("custom_function/c2"))
    hfov = float(camera.findtext("horizontal_fov"))
    return width, height, c2, hfov


def pixel_bearings(pixels, projection):
    """Return horizontal and vertical scene bearings in degrees, right and down positive."""
    width, height, c2, hfov = projection
    x, y = ((pixels + 0.5 - [width / 2, height / 2]) / (width / 2)).T
    radius = np.hypot(x, y)
    theta = c2 * np.arctan(radius * np.tan(hfov / (2 * c2)))
    scale = np.divide(np.sin(theta), radius, out=np.ones_like(radius), where=radius > 0)
    return np.degrees(np.column_stack((np.arctan2(x * scale, np.cos(theta)), np.arcsin(y * scale))))


class AngularFeatures:
    def __init__(self, projection):
        self.projection = projection
        self.sift = cv2.SIFT_create(nfeatures=1000)
        # 0.5-degree sampling near the source image's angular resolution.
        azimuth, elevation = np.meshgrid(np.arange(-88, 88.5, .5), np.arange(-50, 50.5, .5))
        az, el = np.radians([azimuth, elevation])
        width, height, c2, hfov = projection
        x, y = np.sin(az) * np.cos(el), np.sin(el)
        theta = np.arctan2(np.hypot(x, y), np.cos(az) * np.cos(el))
        radius = np.tan(theta / c2) / np.tan(hfov / (2 * c2))
        scale = np.divide(radius, np.hypot(x, y), out=np.zeros_like(radius), where=theta > 0)
        self.map_x = (x * scale * width / 2 + width / 2 - .5).astype(np.float32)
        self.map_y = (y * scale * width / 2 + height / 2 - .5).astype(np.float32)
        valid = ((self.map_x >= 1) & (self.map_x < width - 2)
                 & (self.map_y >= 1) & (self.map_y < height - 2))
        self.mask = cv2.erode(valid.astype(np.uint8), np.ones((17, 17), np.uint8),
                              borderType=cv2.BORDER_CONSTANT, borderValue=0)

    def extract(self, image, angular):
        width, height, *_ = self.projection
        if image is None or image.shape != (height, width):
            raise ValueError(f"Expected decoded native {width}x{height} grayscale image")
        if angular:
            image = cv2.remap(image, self.map_x, self.map_y, cv2.INTER_LINEAR)
        keypoints, descriptors = self.sift.detectAndCompute(image, self.mask if angular else None)
        points = np.array([keypoint.pt for keypoint in keypoints]).reshape(-1, 2)
        angles = points * .5 + [-88, -50] if angular else pixel_bearings(points, self.projection)
        return angles, descriptors


def estimate_yaw(first, second):
    points_a, desc_a = first
    points_b, desc_b = second
    if len(points_a) < 2 or len(points_b) < 2:
        return {"matches": 0, "inliers": 0, "yaw_deg": None}
    matcher = cv2.BFMatcher()
    forward = {(a.queryIdx, a.trainIdx) for a, b in matcher.knnMatch(desc_a, desc_b, k=2)
               if a.distance < .7 * b.distance}
    backward = {(a.trainIdx, a.queryIdx) for a, b in matcher.knnMatch(desc_b, desc_a, k=2)
                if a.distance < .7 * b.distance}
    keep = sorted(forward & backward)
    if not keep:
        return {"matches": 0, "inliers": 0, "yaw_deg": None}
    ai, bi = np.asarray(keep).T
    differences = points_b[bi] - points_a[ai]
    yaw_steps = wrap(differences[:, 0])
    stable_elevation = np.abs(differences[:, 1]) <= ANGLE_INLIER_DEG
    agreement = ((np.abs(wrap(yaw_steps[:, None] - yaw_steps)) <= ANGLE_INLIER_DEG)
                 & stable_elevation & stable_elevation[:, None])
    best_index = np.argmax(agreement.sum(axis=1))
    best = agreement[best_index]
    inliers = int(best.sum())
    yaw = None
    if inliers >= MIN_INLIERS and inliers / len(keep) >= MIN_SUPPORT_FRACTION:
        center = yaw_steps[best_index]
        yaw = float(wrap(center + np.median(wrap(yaw_steps[best] - center))))
    return {"matches": len(keep), "inliers": inliers, "yaw_deg": yaw}


def wrap(values):
    return (values + 180) % 360 - 180


def compare(first, second):
    return {mode: estimate_yaw(first[mode], second[mode]) for mode in first}


def capture_report(root, features):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        raw = (root / entry["path"]).read_bytes()
        if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ValueError(f"Sensor capture manifest mismatch: {entry['path']}")
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    result = {}
    with tarfile.open(root / "representatives.tar.gz") as archive:
        for name, run in summary.items():
            raw = json.loads((root / name / "samples.json").read_text(encoding="utf-8"))
            aligned = align_images(raw["images"], raw["model_samples"], raw["odom_samples"])
            usable = [row for row in aligned if all(row[k]["yaw_deg"] is not None for k in ("model", "odom"))]
            aligned_by_key = {(row["file"], row["stamp_ns"]): row for row in usable}
            end = run["endpoints"]
            endpoints = [aligned_by_key[end[f"{side}_file"], end[f"{side}_stamp_ns"]]
                         for side in ("before", "after")]
            encoded = []
            for row in endpoints:
                with archive.extractfile(f"{name}/{row['file']}") as file:
                    image = cv2.imdecode(np.frombuffer(file.read(), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
                encoded.append({"native": features.extract(image, False), "angular": features.extract(image, True)})
            result[name] = {
                "image_count": len(aligned), "jointly_aligned_count": len(usable),
                "max_bracket_side_ms": max(row[k][side] for row in usable for k in ("model", "odom")
                                           for side in ("before_ms", "after_ms")),
                "pose_delta_deg": {k: angle_delta(endpoints[0][k]["yaw_deg"], endpoints[1][k]["yaw_deg"])
                                   for k in ("model", "odom")},
                **compare(*encoded),
            }
    return result


def historical_report(handoff, features):
    with tempfile.TemporaryDirectory() as tmp:
        extract_verified_handoff(handoff, tmp)
        data = VisualStageData(Path(tmp) / "dataset")
        rows = []
        for route, frames in data.routes.items():
            steps = np.linalg.norm(np.diff(frames["xy"], axis=0), axis=1)
            labels = wrap(np.degrees(np.diff(frames["yaw"])))
            cached = {}
            for start, (translation, yaw) in enumerate(zip(steps, labels)):
                if translation >= .01 or abs(yaw) <= 10:
                    continue
                for index in (start, start + 1):
                    if index not in cached:
                        image = cv2.imread(str(frames["paths"][index]), cv2.IMREAD_GRAYSCALE)
                        cached[index] = {"native": features.extract(image, False),
                                         "angular": features.extract(image, True)}
                rows.append({
                    "route": route, "current": start, "target": start + 1, "legacy_odom_yaw_deg": float(yaw),
                    "legacy_odom_translation_m": float(translation), **compare(cached[start], cached[start + 1]),
                })
    return rows


def sequence_report(folder, features):
    raw = json.loads((folder / "samples.json").read_text(encoding="utf-8"))
    if raw["errors"]:
        raise ValueError(f"Capture reported errors: {raw['errors']}")
    timeline = align_images(raw["images"], raw["model_samples"], raw["odom_samples"])
    if not timeline:
        raise ValueError("No timestamped images in sequence")
    # Leave margins for pose brackets at the edges, using image stamps only.
    start_ns = timeline[0]["stamp_ns"] + 200_000_000
    end_ns = timeline[-1]["stamp_ns"] - 200_000_000
    interior = [row for row in timeline if start_ns <= row["stamp_ns"] <= end_ns]
    if len(interior) < 2:
        raise ValueError("Capture is too short for sequence analysis")
    chosen = [interior[0]]
    for row in interior[1:]:
        if row["stamp_ns"] - chosen[-1]["stamp_ns"] >= SEQUENCE_STEP_NS:
            chosen.append(row)
    if chosen[-1] is not interior[-1]:
        chosen.append(interior[-1])

    def encode(row):
        image = cv2.imread(str(folder / row["file"]), cv2.IMREAD_GRAYSCALE)
        return features.extract(image, True)

    first = previous = encode(chosen[0])
    # Selecting test frames is based on time only. Only scoring reads the pose labels.
    reference = chosen[0]
    cumulative_yaw = 0.0
    rows = []
    for prev_row, row in zip(chosen, chosen[1:]):
        current = encode(row)
        direct = estimate_yaw(first, current)
        increment = estimate_yaw(previous, current)
        delta_t = row["stamp_ns"] - prev_row["stamp_ns"]
        if cumulative_yaw is not None:
            if increment["yaw_deg"] is None or delta_t > MAX_SEQUENCE_GAP_NS:
                cumulative_yaw = None
            else:
                cumulative_yaw = float(wrap(cumulative_yaw + increment["yaw_deg"]))
        labels = {}
        for key in ("model", "odom"):
            start_yaw = reference[key]["yaw_deg"]
            end_yaw = row[key]["yaw_deg"]
            labels[key] = angle_delta(start_yaw, end_yaw) if start_yaw is not None and end_yaw is not None else None
        rows.append({
            "file": row["file"], "stamp_ns": row["stamp_ns"], "step_seconds": delta_t / 1e9,
            "pose_delta_from_first_deg": labels,
            "direct_from_first": direct, "increment": increment, "chained_from_first_deg": cumulative_yaw,
        })
        previous = current
    return {"reference_image": reference, "rows": rows,
            "image_count": len(timeline), "selected_count": len(chosen),
            "sim_seconds": raw["sim_seconds"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, default=HERE / "visual_sensor_alignment")
    parser.add_argument("--sdf", type=Path, default=HERE / "visual_sensor_probe/config_snapshot/model.sdf")
    parser.add_argument("--handoff", type=Path, default=HERE / "training_handoff")
    parser.add_argument("--sequence", type=Path, help="audit a new full capture directory instead of the archived data")
    args = parser.parse_args()
    cv2.setNumThreads(1)
    features = AngularFeatures(read_projection(args.sdf))
    if args.sequence:
        report = sequence_report(args.sequence, features)
    else:
        report = {
            "synchronized_capture": capture_report(args.capture, features),
            "legacy_near_stationary_pairs": historical_report(args.handoff, features),
        }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
