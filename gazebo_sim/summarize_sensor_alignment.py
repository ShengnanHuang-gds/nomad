#!/usr/bin/env python3
"""Summarize the three alignment captures. Does not command the robot."""

import json
import math
from pathlib import Path

import cv2
import numpy as np

ROOT = Path("/mnt/c/Users/61078/Desktop/nomad/gazebo_sim/visual_sensor_alignment")


def wrap(delta):
    return (delta + 180) % 360 - 180


def rpy(q):
    x, y, z, w = q
    yaw = math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))
    pitch = math.degrees(math.asin(max(-1, min(1, 2 * (w * y - z * x)))))
    roll = math.degrees(math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)))
    return roll, pitch, yaw


def bracket(samples, stamp):
    stamps = [s["stamp_ns"] for s in samples]
    lo, hi = 0, len(stamps) - 1
    if stamp < stamps[0] or stamp > stamps[-1]:
        return None
    while lo < hi:
        mid = (lo + hi) // 2
        if stamps[mid] < stamp:
            lo = mid + 1
        else:
            hi = mid
    if stamps[lo] == stamp:
        return samples[lo], samples[lo], 0
    if lo == 0:
        return None
    before, after = samples[lo - 1], samples[lo]
    if max(stamp - before["stamp_ns"], after["stamp_ns"] - stamp) > 50_000_000:
        return None
    return before, after, (stamp - before["stamp_ns"]) / (after["stamp_ns"] - before["stamp_ns"])


def blend_position(before, after, t):
    return [a + (b - a) * t for a, b in zip(before["position_xyz"], after["position_xyz"])]


def sift_pair(first, second):
    images = []
    for path in (first, second):
        gray = cv2.cvtColor(cv2.imread(str(path), cv2.IMREAD_COLOR), cv2.COLOR_BGR2GRAY)
        images.append(gray)
    sift = cv2.SIFT_create(nfeatures=1000)
    keys, desc = [], []
    for gray in images:
        k, d = sift.detectAndCompute(gray, None)
        keys.append(k)
        desc.append(d)
    if desc[0] is None or desc[1] is None or len(keys[0]) < 2 or len(keys[1]) < 2:
        return {"matches": 0, "reason": "too few features"}
    matcher = cv2.BFMatcher()
    def ratio(d_from, d_to):
        pairs = matcher.knnMatch(d_from, d_to, k=2)
        return [(m.queryIdx, m.trainIdx) for m, n in pairs if m.distance < 0.7 * n.distance]
    forward = {(a, b) for a, b in ratio(desc[0], desc[1])}
    backward = {(b, a) for a, b in ratio(desc[1], desc[0])}
    mutual = sorted(forward & backward)
    points = []
    for a, b in mutual:
        x1, y1 = keys[0][a].pt
        x2, y2 = keys[1][b].pt
        points.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "dx": x2 - x1, "dy": y2 - y1})
    if not points:
        return {"matches": 0, "reason": "no mutual matches"}
    dx = float(np.median([p["dx"] for p in points]))
    dy = float(np.median([p["dy"] for p in points]))
    return {"matches": len(points), "median_dx_px": dx, "median_dy_px": dy, "points": points}


def segment(aligned):
    usable = [row for row in aligned if row["model"]["yaw_deg"] is not None and row["odom"]["yaw_deg"] is not None]
    if len(usable) < 3:
        return usable, [], []
    yaw = [row["model"]["yaw_deg"] for row in usable]
    stamps = [row["stamp_ns"] for row in usable]
    pre = next((i for i in range(len(usable) - 1, -1, -1)
                if max(yaw[:i + 1]) - min(yaw[:i + 1]) < 0.35 and stamps[i] - stamps[0] >= 400_000_000), None)
    post = next((i for i in range(len(usable))
                 if max(yaw[i:]) - min(yaw[i:]) < 0.35 and stamps[-1] - stamps[i] >= 400_000_000), None)
    if pre is None or post is None or post <= pre:
        return usable, [], []
    return usable[:pre + 1], usable[pre + 1:post], usable[post:]


def endpoints(data, before, after):
    if not before or not after:
        return {"complete": False, "reason": "missing a still period"}
    a, b = before[-1], after[0]
    model_delta = wrap(b["model"]["yaw_deg"] - a["model"]["yaw_deg"])
    odom_delta = wrap(b["odom"]["yaw_deg"] - a["odom"]["yaw_deg"])
    model_pose = bracket(data["model_samples"], a["stamp_ns"]), bracket(data["model_samples"], b["stamp_ns"])
    odom_pose = bracket(data["odom_samples"], a["stamp_ns"]), bracket(data["odom_samples"], b["stamp_ns"])
    result = {
        "complete": abs(model_delta) >= 8,
        "before_file": a["file"], "after_file": b["file"],
        "before_stamp_ns": a["stamp_ns"], "after_stamp_ns": b["stamp_ns"],
        "model_yaw_delta_deg": model_delta, "odom_yaw_delta_deg": odom_delta,
        "delta_difference_deg": model_delta - odom_delta,
        "before_bracket_ms": {"model": [a["model"]["before_ms"], a["model"]["after_ms"]],
                              "odom": [a["odom"]["before_ms"], a["odom"]["after_ms"]]},
        "after_bracket_ms": {"model": [b["model"]["before_ms"], b["model"]["after_ms"]],
                             "odom": [b["odom"]["before_ms"], b["odom"]["after_ms"]]},
    }
    if all(model_pose) and all(odom_pose):
        ma, mb = blend_position(*model_pose[0][:2], model_pose[0][2]), blend_position(*model_pose[1][:2], model_pose[1][2])
        oa, ob = blend_position(*odom_pose[0][:2], odom_pose[0][2]), blend_position(*odom_pose[1][:2], odom_pose[1][2])
        result["model_displacement_m"] = [p - q for p, q in zip(mb, ma)]
        result["odom_displacement_m"] = [p - q for p, q in zip(ob, oa)]
        result["model_rpy_deg_before"] = list(rpy(model_pose[0][0]["orientation_xyzw"]))
        result["model_rpy_deg_after"] = list(rpy(model_pose[1][0]["orientation_xyzw"]))
        result["odom_rpy_deg_before"] = list(rpy(odom_pose[0][0]["orientation_xyzw"]))
        result["odom_rpy_deg_after"] = list(rpy(odom_pose[1][0]["orientation_xyzw"]))
    if abs(model_delta) < 8:
        result["mark"] = "small_or_incomplete"
    return result


summary = {}
for name in ("stationary", "left", "right"):
    data = json.loads((ROOT / name / "samples.json").read_text(encoding="utf-8"))
    images = data["images"]
    stamps = [row["stamp_ns"] for row in images]
    files = [row["file"] for row in images]
    aligned = data["alignment"]
    both = [row for row in aligned if row["model"]["yaw_deg"] is not None and row["odom"]["yaw_deg"] is not None]
    sides = []
    for row in both:
        for source in ("model", "odom"):
            sides.extend(abs(v) for v in (row[source]["before_ms"], row[source]["after_ms"]) if v is not None)
    before, during, after = segment(both)
    ends = endpoints(data, before if before else both[:1], after if after else both[-1:])
    if name == "stationary":
        ends = endpoints(data, both[:1], both[-1:])
        ends["complete"] = abs(ends["model_yaw_delta_deg"]) < 1
        ends.pop("mark", None)
    pair = None
    if ends.get("before_file") and ends.get("after_file"):
        pair = sift_pair(ROOT / name / ends["before_file"], ROOT / name / ends["after_file"])
        points = pair.pop("points", [])
        (ROOT / name / "sift_matches.json").write_text(json.dumps(points), encoding="utf-8")
    summary[name] = {
        "errors": data["errors"], "zero_stamp_count": data["zero_stamp_count"],
        "wall_seconds": data["wall_seconds"], "sim_seconds": data["sim_seconds"],
        "image_count": len(images), "jointly_aligned_image_count": data["jointly_aligned_image_count"],
        "unique_files": len(set(files)) == len(files), "unique_stamps": len(set(stamps)) == len(stamps),
        "max_bracket_side_ms": max(sides) if sides else None,
        "before_count": len(before), "during_count": len(during), "after_count": len(after),
        "endpoints": ends, "sift": pair,
    }
    chosen = []
    pools = [before or both[:1], during or both[len(both)//2:len(both)//2+1], after or both[-1:]]
    for pool in pools:
        step = max(1, len(pool) // 4)
        chosen.extend(pool[::step][:4])
    dedup = []
    seen = set()
    for row in chosen:
        if row["file"] not in seen:
            seen.add(row["file"])
            dedup.append({"file": row["file"], "stamp_ns": row["stamp_ns"]})
    summary[name]["representatives"] = dedup[:12]

(ROOT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: {"aligned": v["jointly_aligned_image_count"], "images": v["image_count"],
                      "model": v["endpoints"].get("model_yaw_delta_deg"),
                      "odom": v["endpoints"].get("odom_yaw_delta_deg"),
                      "sift": None if not v["sift"] else {kk: v["sift"][kk] for kk in v["sift"] if kk != "points"},
                      "counts": [v["before_count"], v["during_count"], v["after_count"]]}
                  for k, v in summary.items()}, indent=2))