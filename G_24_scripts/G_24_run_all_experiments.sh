#!/bin/bash
# 24_run_all_experiments.sh 
#— Execute the full 16-experiment matrix
# Usage: sudo ./24_run_all_experiments.sh [--duration 60] [--runs 3] [--phase baselines|placement|advanced|mitigations|all]
#
# This orchestrator delegates to individual phase scripts
# Where each phase represents
#   Phase 1: 24_phase1_baselines.sh    (E1–E4)
#   Phase 2: 24_phase2_placement.sh    (E5–E8)
#   Phase 3: 24_phase3_advanced.sh     (E9–E13)
#   Phase 4: 24_phase4_mitigations.sh  (E14–E16)
#
# Prerequisites:
#  
#   1. sudo ./scripts/24_setup_testbed.sh setup
# This setup step esatblishes clent and server namespaces and links them using veth 
#   2. Ensure bpftrace, iperf3, stress-ng are installed


set -euo pipefail


SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Defaults
DURATION=60
RUNS=3
PHASE="all"


# Parse named arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --duration)  DURATION="$2"; shift 2 ;;
        --runs)      RUNS="$2"; shift 2 ;;
        --phase)     PHASE="$2"; shift 2 ;;
        *)           echo "Unknown arg: $1"; exit 1 ;;
    esac
done


COMMON_ARGS="--duration $DURATION --runs $RUNS"

echo "╔═══════════════════════════════════════════════════╗"
echo "║  Experiment Suite — Phase: ${PHASE}                  "
echo "║  Duration: ${DURATION}s per run, ${RUNS} runs each   "
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# ─── Phase 1: Baselines (E1–E4) ─────────────────────────────────
if [[ "$PHASE" == "all" || "$PHASE" == "baselines" ]]; then
    bash "$SCRIPT_DIR/24_phase1_baselines.sh" $COMMON_ARGS
fi


# ─── Phase 2: Softirq Placement & Pinning (E5–E8) ───────────────
if [[ "$PHASE" == "all" || "$PHASE" == "placement" ]]; then
    bash "$SCRIPT_DIR/24_phase2_placement.sh" $COMMON_ARGS
fi

# ─── Phase 3: CFS, Softirq, UDP (E9–E13) ────────────────────────
if [[ "$PHASE" == "all" || "$PHASE" == "advanced" ]]; then
    bash "$SCRIPT_DIR/24_phase3_advanced.sh" $COMMON_ARGS
fi


# ─── Phase 4: Mitigations (E14–E16) ─────────────────────────────
if [[ "$PHASE" == "all" || "$PHASE" == "mitigations" ]]; then
    bash "$SCRIPT_DIR/24_phase4_mitigations.sh" $COMMON_ARGS
fi


echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║  Phase '${PHASE}' complete!                        "
echo "║  Data directory: ./data/                           ║"
echo "╚═══════════════════════════════════════════════════╝"


