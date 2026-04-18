#!/bin/bash

# 24_phase4_mitigations.sh — Phase 4: Mitigations (E14–E16)
# Usage: sudo ./scripts/24_phase4_mitigations.sh [--duration 60] [--runs 3]
#
# Prerequisites:

#   1. sudo ./scripts/24_setup_testbed.sh setup
#   2. Ensure bpftrace, iperf3, stress-ng are installed
#
# NOTE: E15 requires RPS spread + SO_BUSY_POLL setup.
#       E16 requires SO_BUSY_POLL only.
#       See 24_PROJECT_BLUEPRINT.md for configuration commands.

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
echo "║  Phase 4: Mitigations (E14–E16)                  ║"
echo "║  Duration: ${DURATION}s per run, ${RUNS} runs each   "
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# ─── E14: RPS spread + App pinned + CFS low-latency ─────────────


bash "$RUN_EXP" --exp E14 \
    --cpu-stress heavy --net-load high --rps-placement rps_spread \
    --app-pin pinned --cfs lowlatency --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"

# ─── E15: RPS spread + SO_BUSY_POLL ─────────────────────────────
bash "$RUN_EXP" --exp E15 \
    --cpu-stress heavy --net-load high --rps-placement rps_spread \
    --app-pin none --cfs default --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"

# ─── E16: SO_BUSY_POLL only ─────────────────────────────────────
bash "$RUN_EXP" --exp E16 \
    --cpu-stress heavy --net-load high --rps-placement default \
    --app-pin none --cfs default --softirq default \
    --protocol tcp --duration "$DURATION" --runs "$RUNS"


echo ""

echo "Phase 4 (Mitigations) complete! Data directory: ./data/"
