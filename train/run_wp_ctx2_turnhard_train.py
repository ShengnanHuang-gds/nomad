import cv2  # noqa: F401
import argparse, glob, os, subprocess, sys, time
INIT = "logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/dino_dir_best.pth"
PREFIX = "nomad_dino_wp_hist_ctx2_turnhard"
def latest_run():
    d = glob.glob(os.path.join("logs", "nomad_d", PREFIX + "_*"))
    return max(d, key=os.path.getmtime) if d else None
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=18)
    ap.add_argument("--skip-train", action="store_true")
    ap.add_argument("--run-dir", default="")
    ap.add_argument("--skip-eval", action="store_true")
    ap.add_argument("--max-batches", type=int, default=0)
    a = ap.parse_args()
    cwd = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable
    if not a.skip_train:
        cmd = [py, "-u", "train_goal_dino.py", "--target", "endpoint", "--context", "2", "--init", INIT,
               "--run-name", PREFIX, "--epochs", str(a.epochs), "--turn-strict-weight", "3.0",
               "--hard-bearing-deg", "30", "--hard-weight", "2.5", "--turn-winding-deg", "45", "--turn-weight", "2.0"]
        if a.max_batches: cmd += ["--max-batches", str(a.max_batches)]
        t0 = time.time()
        print("+", " ".join(cmd), flush=True)
        subprocess.run(cmd, cwd=cwd, check=True)
        print("train min", (time.time()-t0)/60)
    rd = a.run_dir or latest_run()
    if not rd: raise SystemExit("no run")
    if not os.path.isabs(rd): rd = os.path.join(cwd, rd)
    if a.skip_eval: return
    subprocess.run([py, "-u", "eval_waypoint_head.py", "--run-dir", rd, "--skip-tune"], cwd=cwd, check=True)
    subprocess.run([py, "-u", "eval_blend_ablation.py", "--run-dir", rd], cwd=cwd, check=True)
if __name__ == "__main__": main()
