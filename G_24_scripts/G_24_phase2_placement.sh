#!/bin/bash
# 24_phase2_placement.sh — Phase 2: Softirq Placement & Pinning (E5–E8)
# Usage: sudo ./scripts/24_phase2_placement.sh [--duration 60] [--runs 3]
#
# Prerequisites:
#   1. sudo ./scripts/24_setup_testbed.sh setup
#   2. Ensure bpftrace, iperf3, stress-ng are installed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_EXP="$SCRIPT_DIR/24_run_experiment.sh"

# Defaults
DURATION=60
RUNS=3

# Parse named arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --duration)  DURATION="$2"; shift 2 ;;
        --runs)      RUNS="$2"; shift 2 ;;
        *)           echo "Unknown arg: $1"; exit 1 ;;
    esac
done

echo "╔═══════════════════════════════════════════════════╗"
echo "║  Phase 2: Softirq Placement & Pinning (E5–E8)    ║"
echo "║  Duration: ${DURATION}s per run, ${RUNS} runs each   "
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# ─── E5: RPS pinned ─────────────────────────────────────────────
bash "$RUN_EXP" --exp E5 \
    --cpu-stress heavy --net-load high --rps-placement rps_pinned \
    --app-pin none --cfs default --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"

# ─── E6: RPS spread ─────────────────────────────────────────────
bash "$RUN_EXP" --exp E6 \
    --cpu-stress heavy --net-load high --rps-placement rps_spread \
    --app-pin none --cfs default --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"


# ─── E7: App pinned ─────────────────────────────────────────────
bash "$RUN_EXP" --exp E7 \
    --cpu-stress heavy --net-load high --rps-placement default \
    --app-pin pinned --cfs default --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"

# ─── E8: RPS pinned + App pinned ────────────────────────────────
bash "$RUN_EXP" --exp E8 \
    --cpu-stress heavy --net-load high --rps-placement rps_pinned \
    --app-pin pinned --cfs default --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"


    


echo ""
echo "Phase 2 (Placement & Pinning) complete! Data directory: ./data/"
