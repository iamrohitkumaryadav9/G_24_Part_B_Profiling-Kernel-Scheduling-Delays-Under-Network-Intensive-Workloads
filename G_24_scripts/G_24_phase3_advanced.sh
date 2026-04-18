#!/bin/bash
# 24_phase3_advanced.sh — Phase 3: CFS, Softirq, UDP (E9–E13)
# Usage: sudo ./scripts/24_phase3_advanced.sh [--duration 60] [--runs 3]
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
echo "║  Phase 3: CFS, Softirq, UDP (E9–E13)             ║"
echo "║  Duration: ${DURATION}s per run, ${RUNS} runs each   "
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# ─── E9: CFS low-latency tuning ─────────────────────────────────
bash "$RUN_EXP" --exp E9 \
    --cpu-stress heavy --net-load high --rps-placement default \
    --app-pin none --cfs lowlatency --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"

# ─── E10: Forced ksoftirqd ───────────────────────────────────────
bash "$RUN_EXP" --exp E10 \
    --cpu-stress heavy --net-load high --rps-placement default \
    --app-pin none --cfs default --softirq forced_ksoftirqd \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"

# ─── E11: UDP, no stress ────────────────────────────────────────
bash "$RUN_EXP" --exp E11 \
    --cpu-stress none --net-load high --rps-placement default \
    --app-pin none --cfs default --softirq default \
    --protocol udp --duration "$DURATION" --runs "$RUNS"

# ─── E12: UDP, heavy stress ─────────────────────────────────────
bash "$RUN_EXP" --exp E12 \
    --cpu-stress heavy --net-load high --rps-placement default \
    --app-pin none --cfs default --softirq default \
    --protocol udp --duration "$DURATION" --runs "$RUNS"

# ─── E13: Moderate stress, high network ─────────────────────────
bash "$RUN_EXP" --exp E13 \
    --cpu-stress moderate --net-load high --rps-placement default \
    --app-pin none --cfs default --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"

echo ""
echo " Phase 3 (Advanced) complete! Data directory: ./data/"
