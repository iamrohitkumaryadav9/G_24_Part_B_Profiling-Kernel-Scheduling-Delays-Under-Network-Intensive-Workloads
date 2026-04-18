#!/bin/bash
# 24_phase1_baselines.sh — Phase 1: Baseline Experiments (E1–E4)
# Usage: sudo ./scripts/24_phase1_baselines.sh [--duration 60] [--runs 3]
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
echo "║  Phase 1: Baselines (E1–E4)                      ║"
echo "║  Duration: ${DURATION}s per run, ${RUNS} runs each   "
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# ─── E1: No stress, low network ─────────────────────────────────
bash "$RUN_EXP" --exp E1 \
    --cpu-stress none --net-load low --rps-placement default \
    --app-pin none --cfs default --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"

# ─── E2: No stress, high network ────────────────────────────────
bash "$RUN_EXP" --exp E2 \
    --cpu-stress none --net-load high --rps-placement default \
    --app-pin none --cfs default --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"

# ─── E3: Heavy stress, low network ──────────────────────────────
bash "$RUN_EXP" --exp E3 \
    --cpu-stress heavy --net-load low --rps-placement default \
    --app-pin none --cfs default --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"

# ─── E4: Heavy stress, high network ─────────────────────────────
bash "$RUN_EXP" --exp E4 \
    --cpu-stress heavy --net-load high --rps-placement default \
    --app-pin none --cfs default --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"

echo ""
echo " Phase 1 (Baselines) complete! Data directory: ./data/"
