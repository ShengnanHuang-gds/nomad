"""E-FT from E-oracle: blend far xy + clean pathact8 8-step (dataset units)."""
import glob, os, subprocess, sys, time
import cv2  # noqa: F401

_NOMAD_PY = r"C:\Users\61078\anaconda3\envs\nomad_train\python.exe"
PY = _NOMAD_PY if os.path.isfile(_NOMAD_PY) else sys.executable
CWD = os.path.dirname(os.path.abspath(__file__))
OUT = "logs/revalidation/e_ft_pathact8"
DINO = "logs/nomad_d/nomad_dino_dir_e60_2026_10_13_19_29_06/dino_dir_best.pth"
WP = "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth"
RUN = "nomad_e_ft_pathact8"
REF = "ray blend_path18 +4.04 / GT-path probe +9.56 / pathpoly E-FT +4.10"

def run(cmd):
    print("+", " ".join(cmd), flush=True)
    env = os.environ.copy()
    root = os.path.join(os.path.dirname(CWD), "diffusion_policy")
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = root if not prev else root + os.pathsep + prev
    subprocess.run(cmd, cwd=CWD, check=True, env=env)

def latest():
    exact = os.path.join(CWD, "logs", "nomad", RUN)
    if os.path.isdir(exact):
        return exact
    found = glob.glob(os.path.join(CWD, "logs", "nomad", RUN + "*"))
    return max(found, key=os.path.getmtime) if found else None

def main():
    os.makedirs(os.path.join(CWD, OUT), exist_ok=True)
    t0 = time.time()
    run([
        PY, "-u", "train_e_dino.py",
        "--config", "config/nomad_e_dino_path.yaml",
        "--init-from", "e_oracle",
        "--goal-pos-mode", "blend_path",
        "--path-source", "wp_poly",
        "--path-units", "dataset",
        "--path-gate", "none",
        "--pos-dim", "18",
        "--dino-head", DINO,
        "--wp-head", WP,
        "--epochs", "8",
        "--lr", "3e-5",
        "--warmup-epochs", "1",
        "--true-pos-prob", "0.2",
        "--run-name", RUN,
        "--num-workers", "0",
        "--batch-size", "32",
    ])
    print("train min", (time.time() - t0) / 60, flush=True)
    rd = latest()
    if not rd:
        raise SystemExit("missing run")
    open(os.path.join(CWD, OUT, "run_dir.txt"), "w", encoding="utf-8").write(rd + "\n")
    run([
        PY, "-u", "eval_e_dino.py",
        "--run-dir", rd,
        "--checkpoint", "ema_latest.pth",
        "--config-e-dino", "config/nomad_e_dino_path.yaml",
        "--goal-pos-mode", "blend_path",
        "--path-source", "wp_poly",
        "--path-units", "dataset",
        "--path-gate", "none",
        "--dino-head", DINO,
        "--wp-head", WP,
        "--wp-run-dir", os.path.dirname(WP),
    ])
    print("compare vs", REF, flush=True)
    print("done", rd, flush=True)

if __name__ == "__main__":
    main()
