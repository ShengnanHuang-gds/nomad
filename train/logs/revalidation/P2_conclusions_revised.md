# P2 conclusions (revised 2026-10-24)

See full Chinese version in 2026-10-24.md P2 section.

- use_cm: higher is better (ADE improvement vs mask-only E-oracle).
- Locked kappa blend: e60 2.56, ctx0 2.68, ctx2 2.80 cm (eval_waypoint).
- Val P3a/b: logs/revalidation/p2_val_bearing/summary.txt
- ctx2 vs e60 turn_strict paired mean err: -1.72 deg [-2.63,-0.80] (cluster bootstrap).
- TODO: locked paired Delta-U cluster bootstrap before deploy swap.
