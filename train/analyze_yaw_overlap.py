"""Curr-goal yaw vs bearing error (locked paired frames)."""
import argparse, csv, os, pickle
import numpy as np
from eval_by_distance import load_config, load_paired_frames
from eval_frame_sets import PAIRED_FRAMES
from eval_goal_dir import angle_diff_deg, bearing_deg
from vint_train.data.data_utils import get_data_path

DINO_PRED = "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/eval_dino_dir_best/predictions.npz"
DFT_PRED = "logs/nomad_d/nomad_dft_2026_10_13_15_42_07/eval_goal_dir_best/predictions.npz"
DYAW_BINS = (0, 10, 20, 30, 45, 60, 90, 180)

def yaw_s(y, i):
    return float(np.ravel(y[i])[0])

def wrap(d):
    return (d + np.pi) % (2 * np.pi) - np.pi

def endpoint_dyaw_deg(y, t, g):
    return float(np.degrees(wrap(yaw_s(y, g) - yaw_s(y, t))))

def path_abs_dyaw_deg(y, t, g):
    if g <= t:
        return 0.0
    s = 0.0
    for i in range(t, g):
        s += abs(wrap(yaw_s(y, i + 1) - yaw_s(y, i)))
    return float(np.degrees(s))

def build_items(moments):
    out = []
    for traj, t, goals in moments:
        for group, _a, _b, k, gt in goals:
            out.append(dict(traj=traj, t=t, goal_time=gt, k=k, group=group))
    return out

def summarize(title, abs_dyaw, err, mask=None):
    m = np.ones(len(err), bool) if mask is None else mask
    a, e = abs_dyaw[m], err[m]
    if len(e) == 0:
        return
    rho = float(np.corrcoef(a, e)[0, 1]) if len(e) > 2 else float("nan")
    print(f"\n=== {title} (n={len(e)}) ===")
    print(f"Pearson(|endpoint d_yaw|, err): {rho:+.3f}")
    print(f"|d_yaw| median {np.median(a):.1f}  err median {np.median(e):.1f}  >45% {100*(e>45).mean():.1f}%")
    print(f"{'bin':<10} {'n':>6} {'med':>8} {'>45%':>8}")
    for b in range(len(DYAW_BINS) - 1):
        lo, hi = DYAW_BINS[b], DYAW_BINS[b + 1]
        sel = (a >= lo) & (a < hi)
        if not sel.any():
            continue
        ee = e[sel]
        print(f"{lo}-{hi:<3} {sel.sum():>6} {np.median(ee):>8.1f} {100*(ee>45).mean():>7.1f}%")

def orb_count(pa, pb):
    import cv2
    a = cv2.imread(pa, 0)
    b = cv2.imread(pb, 0)
    if a is None or b is None:
        return 0
    h, w = a.shape
    sc = min(1.0, 320.0 / max(h, w))
    if sc < 1.0:
        a = cv2.resize(a, (int(w * sc), int(h * sc)))
        b = cv2.resize(b, (int(w * sc), int(h * sc)))
    orb = cv2.ORB_create(400)
    k1, d1 = orb.detectAndCompute(a, None)
    k2, d2 = orb.detectAndCompute(b, None)
    if d1 is None or d2 is None:
        return 0
    pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(d1, d2, k=2)
    good = 0
    for pr in pairs:
        if len(pr) == 2 and pr[0].distance < 0.75 * pr[1].distance:
            good += 1
    return good

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--frames", default=PAIRED_FRAMES)
    p.add_argument("--predictions", default=DINO_PRED)
    p.add_argument("--out-dir", default="logs/revalidation/yaw_overlap_analysis")
    p.add_argument("--orb", action="store_true")
    args = p.parse_args()
    cfg = load_config("config/nomad_b40.yaml")
    data_folder = cfg["datasets"]["go_stanford"]["data_folder"]
    items = build_items(load_paired_frames(args.frames))
    pred = dict(np.load(args.predictions))
    err = angle_diff_deg(bearing_deg(pred["dino_dir"]), bearing_deg(pred["target"]))
    groups = np.array([x["group"] for x in items])
    far = groups == "20-40"
    cache = {}
    ep = np.zeros(len(items))
    path = np.zeros(len(items))
    for i, row in enumerate(items):
        tr = row["traj"]
        if tr not in cache:
            with open(os.path.join(data_folder, tr, "traj_data.pkl"), "rb") as f:
                cache[tr] = pickle.load(f)["yaw"]
        y = cache[tr]
        t, g = row["t"], row["goal_time"]
        ep[i] = endpoint_dyaw_deg(y, t, g)
        path[i] = path_abs_dyaw_deg(y, t, g)
    abs_ep = np.abs(ep)
    os.makedirs(args.out_dir, exist_ok=True)
    orb = np.full(len(items), -1, np.int32)
    if args.orb:
        idx = np.where(far)[0]
        print(f"ORB on {len(idx)} far pairs...")
        for j, i in enumerate(idx):
            r = items[i]
            pa = get_data_path(data_folder, r["traj"], r["t"])
            pb = get_data_path(data_folder, r["traj"], r["goal_time"])
            orb[i] = orb_count(pa, pb)
            if (j + 1) % 250 == 0:
                print(f"  {j+1}/{len(idx)}")
        v = far & (orb >= 0)
        if v.any():
            rho = float(np.corrcoef(orb[v], err[v])[0, 1])
            print(f"\n=== FAR ORB vs err (n={v.sum()}) Pearson(matches, err): {rho:+.3f}")
            for lo, hi in ((0, 15), (15, 30), (30, 60), (60, 9999)):
                sel = v & (orb >= lo) & (orb < hi)
                if not sel.any():
                    continue
                ee = err[sel]
                print(f"ORB [{lo},{hi}) n={sel.sum()} med {np.median(ee):.1f} >45% {100*(ee>45).mean():.1f}%")
    summarize("ALL", abs_ep, err)
    summarize("FAR 20-40", abs_ep, err, far)
    summarize("FAR |dyaw|>=45", abs_ep, err, far & (abs_ep >= 45))
    summarize("FAR |dyaw|<30", abs_ep, err, far & (abs_ep < 30))
    with open(os.path.join(args.out_dir, "per_frame_yaw_overlap.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["traj", "t", "goal_time", "k", "group", "endpoint_dyaw_deg", "path_dyaw_deg", "err_deg", "gt45", "orb"])
        for i, r in enumerate(items):
            w.writerow([r["traj"], r["t"], r["goal_time"], r["k"], r["group"], ep[i], path[i], err[i], int(err[i] > 45), int(orb[i])])
    np.savez_compressed(os.path.join(args.out_dir, "arrays.npz"), endpoint_dyaw_deg=ep, path_dyaw_deg=path, err=err, group=groups, orb=orb)
    print("Saved", os.path.abspath(args.out_dir))

if __name__ == "__main__":
    main()
