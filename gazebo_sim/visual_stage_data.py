"""Cache-free data and labels for a new visual adaptation stage."""

import hashlib
import json
import math
import pickle
import tarfile
from pathlib import Path

import numpy as np
from PIL import Image

TRAIN_ROUTES = tuple(f"house_run_{i:02d}" for i in range(5))
VALID_ROUTES = ("house_run_05",)
ALLOWED_ROUTES = TRAIN_ROUTES + VALID_ROUTES


def audit_legacy_train_index(bundle):
    results = []
    for path in (Path(bundle) / "splits/train").glob("*.pkl"):
        with path.open("rb") as f:
            observations, goals = pickle.load(f)
        actual = sorted({r for r, *_ in observations} | {r for r, _ in goals})
        unexpected = sorted(set(actual) - set(ALLOWED_ROUTES))
        results.append({"path": str(path), "observations": len(observations),
                        "goals": len(goals), "cached_routes": actual,
                        "unexpected_routes": unexpected,
                        "unexpected_observations": sum(r in unexpected for r, *_ in observations)})
    return results


def extract_verified_handoff(handoff, destination):
    handoff, destination = Path(handoff), Path(destination)
    manifest = json.loads((handoff / "manifest.json").read_text(encoding="utf-8"))
    archive = handoff / Path(manifest["archive"]["path"]).name
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["archive"]["sha256"]:
        raise ValueError("Training archive SHA256 mismatch")
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        for member in members:
            path = (destination / member.name).resolve()
            if not path.is_relative_to(destination.resolve()) or not (member.isfile() or member.isdir()):
                raise ValueError(f"Unsafe archive member: {member.name}")
        tar.extractall(destination, members=members, filter="data")
    for entry in manifest["files"]:
        path = destination / entry["archive_path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Handoff file mismatch: {entry['archive_path']}")
    return manifest


class VisualStageData:
    def __init__(self, root, context=3, horizon=8, spacing_m=0.12):
        self.root = Path(root)
        self.context, self.horizon, self.spacing_m = context, horizon, spacing_m
        self.routes = {}
        self.indices = {}
        for route in ALLOWED_ROUTES:
            folder = self.root / route
            with (folder / "traj_data.pkl").open("rb") as f:
                raw = pickle.load(f)
            xy = np.asarray(raw["position"], dtype=np.float64)
            yaw = np.asarray(raw["yaw"], dtype=np.float64).reshape(-1)
            if xy.ndim != 2 or xy.shape[1] != 2 or len(xy) != len(yaw):
                raise ValueError(f"Invalid poses in {route}")
            if not np.isfinite(xy).all() or not np.isfinite(yaw).all():
                raise ValueError(f"Nonfinite poses in {route}")
            paths = sorted(folder.glob("*.jpg"), key=lambda p: int(p.stem))
            if [int(p.stem) for p in paths] != list(range(len(xy))):
                raise ValueError(f"Images/poses do not match in {route}")
            for path in paths:
                with Image.open(path) as pil:
                    pil.verify()
            self.routes[route] = {"xy": xy, "yaw": yaw, "paths": paths}
            self.indices[route] = [(route, i) for i in range(context, len(xy) - horizon)]
        self.train = [item for r in TRAIN_ROUTES for item in self.indices[r]]
        self.valid = [item for r in VALID_ROUTES for item in self.indices[r]]
        if not self.train or not self.valid:
            raise ValueError("Empty train/validation data")

    def local_positions(self, route, node, positions):
        data = self.routes[route]
        dx = np.asarray(positions) - data["xy"][node]
        c, s = math.cos(data["yaw"][node]), math.sin(data["yaw"][node])
        return np.stack([dx[..., 0]*c + dx[..., 1]*s,
                         -dx[..., 0]*s + dx[..., 1]*c], axis=-1)

    def actions(self, route, node):
        xy = self.routes[route]["xy"]
        return self.local_positions(route, node, xy[node+1:node+1+self.horizon])

    def turn_class(self, route, node):
        point = self.actions(route, node)[2]
        angle = math.degrees(math.atan2(point[1], point[0]))
        if np.linalg.norm(point) < 0.03:
            return "straight"
        return "left" if angle > 15 else "right" if angle < -15 else "straight"

    def sampling_weights(self):
        classes = [self.turn_class(*item) for item in self.train]
        counts = {label: classes.count(label) for label in set(classes)}
        return np.asarray([1 / counts[label] for label in classes], dtype=float)

    def report(self):
        report = {"train_routes": list(TRAIN_ROUTES), "validation_routes": list(VALID_ROUTES),
                  "heldout_routes_read": [], "train_observations": len(self.train),
                  "validation_observations": len(self.valid), "cache_used": False,
                  "metric_waypoint_spacing_m": self.spacing_m, "routes": {}}
        for route in ALLOWED_ROUTES:
            groups = [self.turn_class(*item) for item in self.indices[route]]
            report["routes"][route] = {"images": len(self.routes[route]["paths"]),
                                        "observations": len(groups),
                                        "turn_classes": {k: groups.count(k) for k in ("left", "right", "straight")}}
        return report
