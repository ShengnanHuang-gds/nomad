import os, subprocess, sys
PY = r"C:\Users\61078\anaconda3\envs\nomad_train\python.exe"
INIT = os.path.join(os.getcwd(), "logs/nomad_d/nomad_dino_wp_ctx2_pathact8_2026_11_02_10_56_32/dino_dir_best.pth")
common = [
    PY, "-u", "train_path_correction_ab.py",
    "--init", INIT,
    "--batch-size", "128",
    "--epochs", "8",
    "--seed", "0",
    "--min-goal-m", "0.3",
    "--lr", "1e-4",
    "--weight-decay", "0.05",
    "--context", "2",
    "--path-steps", "8",
]
env = os.environ.copy()
env["PYTHONPATH"] = "../diffusion_policy"
for mode, name in [("dist", "nomad_dino_wp_pathcorr_dist"), ("dir", "nomad_dino_wp_pathcorr_dir")]:
    cmd = common + ["--correction-mode", mode, "--run-name", name]
    print("RUN", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, env=env, cwd=os.getcwd())
    if r.returncode != 0:
        sys.exit(r.returncode)
print("both trainings done", flush=True)