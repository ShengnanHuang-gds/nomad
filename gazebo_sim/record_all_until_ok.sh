#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$ROOT"
source "$ROOT/gazebo_sim/nomad_wsl_env.sh"
exec "$NOMAD_PY" "$ROOT/gazebo_sim/record_house_multi.py" --rerecord-until-ok --runs "${RUNS:-house_run_06}" --max-tries "${MAX_TRIES:-8}" "$@"