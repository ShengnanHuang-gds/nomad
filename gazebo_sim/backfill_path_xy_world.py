#!/usr/bin/env python3

"""Add path_xy_world to episode JSONs written before nomad_navigate stored it."""



from __future__ import annotations



import argparse

import json

from pathlib import Path



import numpy as np



from episode_coords import path_xy_world





def gt_first(ep_path: Path, traj: str) -> np.ndarray:

    import pickle



    root = ep_path.resolve().parent.parent

    pkl = root / traj / "traj_data.pkl"

    with open(pkl, "rb") as f:

        return np.asarray(pickle.load(f)["position"][0][:2], dtype=np.float64)





def backfill(ep_path: Path, dry_run: bool) -> bool:

    data = json.loads(ep_path.read_text(encoding="utf-8"))

    if data.get("path_xy_world"):

        return False

    raw = data.get("path_xy") or []

    if not raw:

        return False

    traj = data.get("traj") or "house_run_06"

    teach0 = gt_first(ep_path, traj)

    world = path_xy_world(data, np.asarray(raw), teach0)

    data["path_xy_world"] = world.tolist()

    if not dry_run:

        ep_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return True





def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument("paths", nargs="+", help="episode .json files or directories")

    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    files: list[Path] = []

    for p in args.paths:

        path = Path(p)

        if path.is_dir():

            files.extend(sorted(path.glob("house_*.json")))

        elif path.is_file():

            files.append(path)

    n = 0

    for f in files:

        if backfill(f, args.dry_run):

            print("updated" if not args.dry_run else "would update", f)

            n += 1

    if n == 0:

        print("no episodes needed backfill")





if __name__ == "__main__":

    main()