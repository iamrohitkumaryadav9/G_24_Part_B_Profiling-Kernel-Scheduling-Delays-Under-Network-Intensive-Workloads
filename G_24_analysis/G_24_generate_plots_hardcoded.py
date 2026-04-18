#!/usr/bin/env python3
"""
24_generate_plots_hardcoded.py — Generate all publication-quality plots
using REAL metrics hardcoded from 24_hardcoded_data.py.

Precise percentiles from sampled sched_delay.csv events.


Usage:
    python3 analysis/24_generate_plots_hardcoded.py
"""



import os
import sys
import numpy as np


import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
import matplotlib.ticker as ticker


# ─── Import Hardcoded Data ──────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
_data = import_module("24_hardcoded_data")
HISTOGRAM_BUCKETS = _data.HISTOGRAM_BUCKETS
METRICS = _data.METRICS
EXP_CONFIG = _data.EXP_CONFIG

PLOT_DIR = os.path.join(os.path.dirname(__file__), '..', 'plots')
os.makedirs(PLOT_DIR, exist_ok=True)

ALL_EXPS = [f"E{i}" for i in range(1, 17)]


# ─── Labels & Colors ───────────────────────────────────────────────
EXP_LABELS = {
    "E1": "No stress\nLow net", "E2": "No stress\nHigh net",
    "E3": "Heavy CPU\nLow net", "E4": "Heavy CPU\nHigh net",
    "E5": "E4+RPS→CPU0", "E6": "E4+RPS→all",
    "E7": "E4+App pin", "E8": "E4+RPS+pin",
    "E9": "E4+CFS lowlat", "E10": "E4+ksoftirqd",
    "E11": "UDP no stress", "E12": "UDP+heavy",
    "E13": "Moderate CPU", "E14": "Combined mit",
    "E15": "RPS+busy_poll", "E16": "busy_poll only",
}

# Experiments are grouped into four phases of 4 each; each phase gets its own
# color family so the CDF and bar charts visually cluster related experiments.
PHASE_COLORS = {
    "baselines":  ["#2ecc71", "#27ae60", "#e74c3c", "#c0392b"],
    "placement":  ["#3498db", "#2980b9", "#9b59b6", "#8e44ad"],
    "advanced":   ["#f39c12", "#e67e22", "#1abc9c", "#16a085"],
    "mitigations":["#e91e63", "#9c27b0", "#673ab7", "#3f51b5"],
}


def get_color(exp):
    """Return the phase-appropriate color for an experiment label like 'E7'."""
    # Map index 0-15 to phase 0-3 (4 experiments per phase)
    idx = ALL_EXPS.index(exp)
    phase = idx // 4          # 0=baselines, 1=placement, 2=advanced, 3=mitigations
    keys = list(PHASE_COLORS.keys())
    # Retrieve color based on phase index and position within the 4-experiment block
    return PHASE_COLORS[keys[phase]][idx % 4]

def _fmt_us(val):
    """Format a microsecond value as a human-readable string with appropriate unit.

    Ranges:
      <1 µs  → nanoseconds  (e.g. '500ns')
      1–999 µs → microseconds (e.g. '42.3µs')
      1–999 ms → milliseconds (e.g. '1.23ms')
      >=1 s    → seconds      (e.g. '2.10s')
    """
    if val is None or (isinstance(val, float) and np.isnan(val)): return "n/a"
    if val < 1: return f"{val*1000:.0f}ns"
    elif val < 1000: return f"{val:.1f}\u03bcs"
    elif val < 1_000_000: return f"{val/1000:.2f}ms"
    else: return f"{val/1_000_000:.2f}s"


# ─── CDF Helper ────────────────────────────────────────────────────

def histogram_to_cdf(buckets):
    if not buckets: return np.array([]), np.array([])
    total = sum(c for _, _, c in buckets)
    if total == 0: return np.array([]), np.array([])
    xs, ys = [0], [0]
    cumsum = 0
    for low, high, count in buckets:
        cumsum += count
        xs.append(high)
        ys.append(cumsum / total)
    return np.array(xs, dtype=float), np.array(ys, dtype=float)


# ═══════════════════════════════════════════════════════════════════
# PLOT 1: CDF Overlay — All 16 Experiments (p90+ region)
# ═══════════════════════════════════════════════════════════════════



def plot_1_all_cdf():
    print("  Plot 1: All experiments CDF...")
    fig, ax = plt.subplots(figsize=(14, 8))
    for exp in ALL_EXPS:
        buckets = HISTOGRAM_BUCKETS.get(exp, [])
        x, y = histogram_to_cdf(buckets)
        if len(x) == 0: continue
        ax.plot(x, y, label=exp, color=get_color(exp), linewidth=1.5)
    ax.set_xscale('log')
    ax.set_xlim(1, 1e6)
    ax.set_ylim(0.9, 1.001)
    ax.set_xlabel('Run-queue Delay (μs)', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title('Run-queue Delay CDF — All 16 Experiments (p90+ region)', fontsize=14)
    ax.axhline(y=0.99, color='red', linestyle='--', alpha=0.5, label='p99')
    ax.axhline(y=0.999, color='darkred', linestyle=':', alpha=0.5, label='p99.9')
    ax.legend(fontsize=8, ncol=4, loc='lower right')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_runqueue_delay_cdf_all.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 2: Percentile Bar Chart (p50, p99, p99.9) — PRECISE values
# ═══════════════════════════════════════════════════════════════════



def plot_2_percentile_bars():
    print("  Plot 2: Percentile bar chart...")
    exps = [e for e in ALL_EXPS if METRICS[e]["p99"] > 0]
    p50 = [METRICS[e]["p50"] for e in exps]
    p99 = [METRICS[e]["p99"] for e in exps]
    p999 = [METRICS[e]["p999"] for e in exps]
    x = np.arange(len(exps))
    width = 0.25
    fig, ax = plt.subplots(figsize=(16, 7))
    ax.bar(x - width, p50, width, label='p50', color='#2ecc71', alpha=0.8)
    ax.bar(x, p99, width, label='p99', color='#e74c3c', alpha=0.8)
    ax.bar(x + width, p999, width, label='p99.9', color='#8e44ad', alpha=0.8)
    ax.set_yscale('log')
    ax.set_ylabel('Delay (μs)', fontsize=12)
    ax.set_xlabel('Experiment', fontsize=12)
    ax.set_title('Scheduling Delay Percentiles Across All Experiments', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(exps, rotation=45, ha='right')
    ax.legend(fontsize=11)
    ax.axhline(y=1000, color='orange', linestyle='--', alpha=0.7, label='1ms threshold')
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_percentile_comparison.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 3: Softirq CPU Heatmap
# ═══════════════════════════════════════════════════════════════════



def plot_3_softirq_heatmap():
    print("  Plot 3: Softirq CPU heatmap...")
    exps = [e for e in ALL_EXPS if METRICS[e]["softirq_per_cpu"]]
    max_cpu = max(max(int(k) for k in METRICS[e]["softirq_per_cpu"].keys()) for e in exps) + 1
    max_cpu = min(max_cpu, 20)
    data = np.zeros((len(exps), max_cpu))
    for i, exp in enumerate(exps):
        cpu_data = METRICS[exp]["softirq_per_cpu"]
        total = sum(cpu_data.values()) or 1
        for cpu_key, count in cpu_data.items():
            cpu = int(cpu_key)
            if cpu < max_cpu:
                data[i, cpu] = count / total * 100
    fig, ax = plt.subplots(figsize=(14, 8))
    cmap = LinearSegmentedColormap.from_list('custom', ['#f0f0f0', '#3498db', '#e74c3c', '#2c3e50'])
    im = ax.imshow(data, aspect='auto', cmap=cmap, vmin=0, vmax=30)
    ax.set_xticks(range(max_cpu))
    ax.set_xticklabels([f'CPU{i}' for i in range(max_cpu)], rotation=45, fontsize=8)
    ax.set_yticks(range(len(exps)))
    ax.set_yticklabels(exps)
    ax.set_xlabel('CPU', fontsize=12)
    ax.set_ylabel('Experiment', fontsize=12)
    ax.set_title('Softirq NET_RX Distribution by CPU (% of total)', fontsize=14)
    plt.colorbar(im, ax=ax, label='% of total softirq')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_softirq_cpu_heatmap.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 4: Mitigation Comparison (p99 bar chart)
# ═══════════════════════════════════════════════════════════════════



def plot_4_mitigation_comparison():
    print("  Plot 4: Mitigation comparison...")
    groups = {
        "Baseline\n(E4)": "E4", "RPS spread\n(E6)": "E6",
        "App pin\n(E7)": "E7", "RPS+pin\n(E8)": "E8",
        "CFS lowlat\n(E9)": "E9", "ksoftirqd\n(E10)": "E10",
        "Combined\n(E14)": "E14", "RPS+bpoll\n(E15)": "E15",
        "bpoll only\n(E16)": "E16",
    }
    labels, p99_vals, colors = [], [], []
    for label, exp in groups.items():
        if exp in METRICS and METRICS[exp]["p99"] > 0:
            labels.append(label)
            p99_vals.append(METRICS[exp]["p99"])
            colors.append('#c0392b' if exp == "E4" else '#3498db')
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(range(len(labels)), p99_vals, color=colors, alpha=0.85, edgecolor='white')
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel('p99 Delay (μs)', fontsize=12)
    ax.set_title('Mitigation Effectiveness: p99 Scheduling Delay vs Baseline (E4)', fontsize=14)
    if p99_vals:
        ax.axhline(y=p99_vals[0], color='red', linestyle='--', alpha=0.5, linewidth=2)
    for bar, val in zip(bars, p99_vals):
        lbl = _fmt_us(val)
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20, lbl,
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_mitigation_p99_comparison.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 5: Box Plot (synthetic from histogram)
# ═══════════════════════════════════════════════════════════════════



def plot_5_boxplot():
    print("  Plot 5: Box plot distributions...")
    exps = ALL_EXPS
    box_data = []
    for exp in exps:
        buckets = HISTOGRAM_BUCKETS.get(exp, [])
        samples = []
        for low, high, count in buckets:
            if count > 0:
                mid = (low + high) / 2
                n = min(count, 100)
                samples.extend([mid] * n)
        box_data.append(samples if samples else [0])
    fig, ax = plt.subplots(figsize=(16, 7))
    bp = ax.boxplot(box_data, labels=exps, patch_artist=True, showfliers=False, whis=[5, 95])
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(get_color(exps[i]))
        patch.set_alpha(0.7)
    ax.set_yscale('log')
    ax.set_ylabel('Run-queue Delay (μs)', fontsize=12)
    ax.set_xlabel('Experiment', fontsize=12)
    ax.set_title('Scheduling Delay Distribution (5th-95th percentile, no outliers)', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_delay_distribution_boxplot.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 6: Context Switch Comparison
# ═══════════════════════════════════════════════════════════════════


def plot_6_context_switches():
    print("  Plot 6: Context switches...")
    exps = [e for e in ALL_EXPS if METRICS[e]["ctx_switches"] > 0]
    vals = [METRICS[e]["ctx_switches"] / 1e6 for e in exps]
    colors = [get_color(e) for e in exps]
    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(range(len(exps)), vals, color=colors, alpha=0.85, edgecolor='white')
    ax.set_xticks(range(len(exps)))
    ax.set_xticklabels(exps, rotation=45, ha='right')
    ax.set_ylabel('Context Switches (millions)', fontsize=12)
    ax.set_title('Context Switch Count per Experiment (60s avg)', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f'{val:.1f}M', ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_context_switches.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 7: Voluntary Context Switches
# ═══════════════════════════════════════════════════════════════════


def plot_7_voluntary_switches():
    print("  Plot 7: Voluntary context switches...")
    exps = [e for e in ALL_EXPS if METRICS[e]["voluntary"] > 0]
    vals = [METRICS[e]["voluntary"] / 1e6 for e in exps]
    colors = [get_color(e) for e in exps]
    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(range(len(exps)), vals, color=colors, alpha=0.85, edgecolor='white')
    ax.set_xticks(range(len(exps)))
    ax.set_xticklabels(exps, rotation=45, ha='right')
    ax.set_ylabel('Voluntary Context Switches (millions)', fontsize=12)
    ax.set_title('Voluntary Context Switches per Experiment', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{val:.1f}M', ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_voluntary_context_switches.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 8: TCP Retransmit Comparison
# ═══════════════════════════════════════════════════════════════════


def plot_8_retransmits():
    print("  Plot 8: TCP retransmits...")
    tcp_exps = [e for e in ALL_EXPS if e not in ["E11", "E12"]]
    vals = [METRICS[e]["retransmits"] for e in tcp_exps]
    colors = [get_color(e) for e in tcp_exps]
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(range(len(tcp_exps)), vals, color=colors, alpha=0.85, edgecolor='white')
    ax.set_xticks(range(len(tcp_exps)))
    ax.set_xticklabels(tcp_exps, rotation=45, ha='right')
    ax.set_ylabel('TCP Retransmit Segments', fontsize=12)
    ax.set_title('TCP Retransmits per Experiment (60s average)', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_tcp_retransmit_comparison.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 9: CPU Migrations
# ═══════════════════════════════════════════════════════════════════


def plot_9_cpu_migrations():
    print("  Plot 9: CPU migrations...")
    exps = [e for e in ALL_EXPS if METRICS[e]["migrations"] > 0]
    vals = [METRICS[e]["migrations"] / 1e6 for e in exps]
    colors = [get_color(e) for e in exps]
    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(range(len(exps)), vals, color=colors, alpha=0.85, edgecolor='white')
    ax.set_xticks(range(len(exps)))
    ax.set_xticklabels(exps, rotation=45, ha='right')
    ax.set_ylabel('CPU Migrations (millions)', fontsize=12)
    ax.set_title('Task CPU Migrations per Experiment', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{val:.1f}M', ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_task_cpu_migrations.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 10: Softirq Gini vs p99 Scatter
# ═══════════════════════════════════════════════════════════════════


def plot_10_scatter_softirq_vs_delay():
    print("  Plot 10: Softirq vs delay scatter...")
    exps = [e for e in ALL_EXPS if METRICS[e]["softirq_per_cpu"] and METRICS[e]["p99"] > 0]
    ginis, p99s = [], []
    for exp in exps:
        cpu_data = METRICS[exp]["softirq_per_cpu"]
        vals = list(cpu_data.values())
        total = sum(vals) or 1
        fracs = sorted([v/total for v in vals])
        n = len(fracs)
        if n == 0 or sum(fracs) == 0:
            ginis.append(0)
        else:
            gini = sum((2*i - n - 1) * fracs[i] for i in range(n)) / (n * sum(fracs))
            ginis.append(abs(gini))
        p99s.append(METRICS[exp]["p99"])
    fig, ax = plt.subplots(figsize=(10, 7))
    colors = [get_color(e) for e in exps]
    ax.scatter(ginis, p99s, c=colors, s=120, edgecolors='white', linewidth=1.5, zorder=5)
    for i, exp in enumerate(exps):
        ax.annotate(exp, (ginis[i], p99s[i]), fontsize=9, ha='left',
                    xytext=(5, 5), textcoords='offset points')
    ax.set_xlabel('Softirq Gini Coefficient (concentration)', fontsize=12)
    ax.set_ylabel('p99 Run-queue Delay (μs)', fontsize=12)
    ax.set_title('Softirq Concentration vs Scheduling Delay', fontsize=14)
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_softirq_gini_vs_p99.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 11: Baseline CDF (E1-E4 Stress Progression)
# ═══════════════════════════════════════════════════════════════════


def plot_11_baseline_cdf():
    print("  Plot 11: Baseline CDF...")
    fig, ax = plt.subplots(figsize=(10, 7))
    for exp in ["E1", "E2", "E3", "E4"]:
        buckets = HISTOGRAM_BUCKETS.get(exp, [])
        x, y = histogram_to_cdf(buckets)
        if len(x) == 0: continue
        ax.plot(x, y, label=f'{exp} ({EXP_LABELS[exp].replace(chr(10), ", ")})',
                color=get_color(exp), linewidth=2.5)
    ax.set_xscale('log'); ax.set_xlim(1, 1e6); ax.set_ylim(0.8, 1.001)
    ax.set_xlabel('Run-queue Delay (μs)', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title('Baseline Experiments: Effect of Stress on Scheduling Delay', fontsize=14)
    ax.axhline(y=0.99, color='red', linestyle='--', alpha=0.5, label='p99')
    ax.legend(fontsize=10); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_baseline_stress_progression.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 12: TCP vs UDP CDF
# ═══════════════════════════════════════════════════════════════════
def plot_12_tcp_vs_udp():
    print("  Plot 12: TCP vs UDP...")
    fig, ax = plt.subplots(figsize=(10, 7))
    pairs = [("E1", "TCP no stress", '#2ecc71', '-'), ("E11", "UDP no stress", '#3498db', '--'),
             ("E4", "TCP heavy+high", '#e74c3c', '-'), ("E12", "UDP heavy+high", '#f39c12', '--')]
    for exp, label, color, ls in pairs:
        buckets = HISTOGRAM_BUCKETS.get(exp, [])
        x, y = histogram_to_cdf(buckets)
        if len(x) == 0: continue
        ax.plot(x, y, label=f'{exp}: {label}', color=color, linewidth=2, linestyle=ls)
    ax.set_xscale('log'); ax.set_xlim(1, 1e6); ax.set_ylim(0.8, 1.001)
    ax.set_xlabel('Run-queue Delay (μs)', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title('TCP vs UDP Scheduling Delay Under Stress', fontsize=14)
    ax.axhline(y=0.99, color='gray', linestyle=':', alpha=0.5)
    ax.legend(fontsize=10); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_tcp_udp_delay_comparison.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 13: Degradation Factors (normalized to E1)
# ═══════════════════════════════════════════════════════════════════
def plot_13_degradation_factors():
    print("  Plot 13: Degradation factors...")
    e1_p99 = METRICS["E1"]["p99"]
    if not e1_p99 or e1_p99 == 0: return
    exps = [e for e in ALL_EXPS if METRICS[e]["p99"] > 0]
    factors = [METRICS[e]["p99"] / e1_p99 for e in exps]
    fig, ax = plt.subplots(figsize=(14, 6))
    colors = [get_color(e) for e in exps]
    bars = ax.bar(range(len(exps)), factors, color=colors, alpha=0.85, edgecolor='white')
    ax.set_xticks(range(len(exps)))
    ax.set_xticklabels(exps, rotation=45, ha='right')
    ax.set_ylabel(f'p99 Degradation Factor (vs E1 = {_fmt_us(e1_p99)})', fontsize=12)
    ax.set_title('Scheduling Delay Degradation Normalized to E1 Baseline', fontsize=14)
    ax.axhline(y=1, color='green', linestyle='--', alpha=0.5, linewidth=2)
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, factors):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.1,
                f'{val:.1f}x', ha='center', va='bottom', fontsize=8, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_normalized_degradation_factors.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 14: Per-CPU Softirq with/without RPS
# ═══════════════════════════════════════════════════════════════════


def plot_14_per_cpu_rps():
    print("  Plot 14: Per-CPU softirq RPS comparison...")
    compare = ["E4", "E5", "E6", "E7"]
    avail = [e for e in compare if METRICS[e]["softirq_per_cpu"]]
    if len(avail) < 2: return
    fig, axes = plt.subplots(1, len(avail), figsize=(5*len(avail), 5), sharey=True)
    if len(avail) == 1: axes = [axes]
    for ax, exp in zip(axes, avail):
        cpu_data = METRICS[exp]["softirq_per_cpu"]
        total = sum(cpu_data.values()) or 1
        cpus = sorted(int(c) for c in cpu_data.keys())[:20]
        fracs = [cpu_data.get(c, cpu_data.get(str(c), 0)) / total * 100 for c in cpus]
        ax.bar(cpus, fracs, color=get_color(exp), alpha=0.8)
        ax.set_title(f'{exp}\n{EXP_LABELS[exp].replace(chr(10), ", ")}', fontsize=10)
        ax.set_xlabel('CPU')
        if ax == axes[0]: ax.set_ylabel('% of NET_RX softirq')
        ax.set_ylim(0, max(max(fracs) * 1.2, 5))
        ax.grid(True, alpha=0.3, axis='y')
    plt.suptitle('Per-CPU Softirq Distribution: RPS Placement Effects', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_per_cpu_softirq_rps.png"), dpi=150, bbox_inches='tight')
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 15: H1 — Softirq Concentration Metrics
# ═══════════════════════════════════════════════════════════════════


def plot_15_h1_concentration():
    print("  Plot 15: H1 softirq concentration...")
    h1_exps = {"E4 (default)": "E4", "E5 (RPS→CPU0)": "E5",
               "E6 (RPS→all)": "E6", "E7 (app pin)": "E7", "E8 (RPS+pin)": "E8"}
    labels, ginis, max_fracs = [], [], []
    for label, exp in h1_exps.items():
        cpu_data = METRICS[exp]["softirq_per_cpu"]
        vals = list(cpu_data.values())
        total = sum(vals) or 1
        fracs = sorted([v/total for v in vals])
        n = len(fracs)
        gini = abs(sum((2*i-n-1)*fracs[i] for i in range(n)) / (n*sum(fracs))) if sum(fracs) > 0 else 0
        labels.append(label)
        ginis.append(gini)
        max_fracs.append(max(v/total*100 for v in vals))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    colors = ['#e74c3c', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
    bars1 = ax1.bar(labels, ginis, color=colors[:len(labels)], alpha=0.85)
    ax1.set_ylabel('Gini Coefficient'); ax1.set_title('Softirq Concentration (Gini)', fontsize=13)
    ax1.set_ylim(0, 1)
    for bar, val in zip(bars1, ginis):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    ax1.tick_params(axis='x', rotation=20)
    bars2 = ax2.bar(labels, max_fracs, color=colors[:len(labels)], alpha=0.85)
    ax2.set_ylabel('Max Single-CPU Share (%)'); ax2.set_title('Hottest CPU Softirq Share', fontsize=13)
    ax2.set_ylim(0, 30)
    ax2.axhline(y=12.5, color='#2ecc71', alpha=0.5, linestyle='--', linewidth=1)
    ax2.text(len(labels)-0.7, 13, 'ideal (12.5%)', color='#2ecc71', alpha=0.6, fontsize=9)
    for bar, val in zip(bars2, max_fracs):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                 f'{val:.1f}%', ha='center', va='bottom', fontsize=10)
    ax2.tick_params(axis='x', rotation=20)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_h1_concentration_metrics.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 16: H4 Mitigations CDF (E4 vs E14, E15, E16)
# ═══════════════════════════════════════════════════════════════════
def plot_16_h4_mitigations_cdf():
    print("  Plot 16: H4 mitigations CDF...")
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#16213e')
    experiments = {
        'E4 (baseline)': ('E4', '#e74c3c', '-', 2.5),
        'E14 (RPS+pin+CFS)': ('E14', '#3498db', '--', 2.0),
        'E15 (RPS+busy_poll)': ('E15', '#2ecc71', '--', 2.0),
        'E16 (busy_poll only)': ('E16', '#f39c12', '--', 2.0),
    }
    for label, (exp, color, ls, lw) in experiments.items():
        buckets = HISTOGRAM_BUCKETS.get(exp, [])
        x, y = histogram_to_cdf(buckets)
        if len(x) > 0:
            ax.plot(x, y, label=label, color=color, linestyle=ls, linewidth=lw)
    ax.set_xscale('log'); ax.set_xlim(1, 2e5); ax.set_ylim(0.85, 1.001)
    ax.set_xlabel('Run-queue Delay (μs)', fontsize=13, color='#e0e0e0', fontweight='bold')
    ax.set_ylabel('CDF', fontsize=13, color='#e0e0e0', fontweight='bold')
    ax.set_title('H4: Combined Mitigations vs Baseline (E4)', fontsize=14,
                 color='#ffffff', fontweight='bold', pad=15)
    ax.axhline(y=0.99, color='#ff6b6b', linestyle=':', alpha=0.6, linewidth=1)
    ax.text(2, 0.9905, 'p99', color='#ff6b6b', fontsize=9, alpha=0.7)
    ax.tick_params(colors='#b0b0b0')
    ax.grid(True, alpha=0.15, color='#ffffff')
    legend = ax.legend(loc='lower right', fontsize=11, framealpha=0.8,
                       facecolor='#1a1a2e', edgecolor='#444444')
    for t in legend.get_texts(): t.set_color('#e0e0e0')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_h4_mitigations_cdf.png"), dpi=150,
                facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    plt.style.use('default')


# ═══════════════════════════════════════════════════════════════════
# PLOT 17: Throughput Comparison
# ═══════════════════════════════════════════════════════════════════
def plot_17_throughput():
    print("  Plot 17: Throughput comparison...")
    exps = ALL_EXPS
    vals = [METRICS[e]["throughput_gbps"] for e in exps]
    colors = [get_color(e) for e in exps]
    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(range(len(exps)), vals, color=colors, alpha=0.85, edgecolor='white')
    ax.set_xticks(range(len(exps)))
    ax.set_xticklabels(exps, rotation=45, ha='right')
    ax.set_ylabel('Throughput (Gbps)', fontsize=12)
    ax.set_title('Network Throughput per Experiment', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{val:.1f}', ha='center', va='bottom', fontsize=7)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_throughput_comparison.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 18: Summary Table
# ═══════════════════════════════════════════════════════════════════

def plot_18_summary_table():
    print("  Plot 18: Summary table...")
    cols = ['Exp', 'Config', 'p50(μs)', 'p95(μs)', 'p99(μs)', 'p99.9(μs)',
            'Mean(μs)', 'CtxSw(M)', 'TP(Gbps)', 'Retrans', 'SIrq%']
    rows = []
    for exp in ALL_EXPS:
        m = METRICS[exp]
        c = EXP_CONFIG[exp]
        config = f"{c['cpu_stress']}/{c['net_load']}"
        rows.append([
            exp, config,
            f'{m["p50"]:.1f}', f'{m["p95"]:.1f}', f'{m["p99"]:.1f}', f'{m["p999"]:.1f}',
            f'{m["delay_mean"]:.1f}',
            f'{m["ctx_switches"]/1e6:.1f}', f'{m["throughput_gbps"]:.1f}',
            str(m["retransmits"]), f'{m["softirq_cpu_pct"]:.1f}',
        ])
    fig, ax = plt.subplots(figsize=(18, max(6, len(rows) * 0.4 + 2)))
    ax.axis('off')
    table = ax.table(cellText=rows, colLabels=cols, loc='center',
                     cellLoc='center', colColours=['#3498db']*len(cols))
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    for j in range(len(cols)):
        table[0, j].set_text_props(color='white', fontweight='bold')
    ax.set_title('Complete Experiment Metrics Summary (Precise Values from Sampled Data)', fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_experiment_summary_table.png"), dpi=150, bbox_inches='tight')
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# PLOT 19: Contention Threshold (E1 → E13 → E3 → E4)
# ═══════════════════════════════════════════════════════════════════


def plot_19_contention_threshold():
    print("  Plot 19: Contention threshold...")
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#16213e')
    configs = {
        'E1': ('E1: No stress', '#2ecc71', '-'),
        'E13': ('E13: Moderate stress', '#f39c12', '-'),
        'E3': ('E3: Heavy stress, Low load', '#e67e22', '--'),
        'E4': ('E4: Heavy stress, High load', '#e74c3c', '-'),
    }
    for exp, (label, color, ls) in configs.items():
        buckets = HISTOGRAM_BUCKETS.get(exp, [])
        x, y = histogram_to_cdf(buckets)
        if len(x) > 0:
            ax.plot(x, y, label=label, color=color, linestyle=ls, linewidth=2.5, alpha=0.9)
    ax.axvline(x=1000, color='#ff6b6b', alpha=0.5, linestyle=':', linewidth=2)
    ax.text(1100, 0.5, '1ms threshold', color='#ff6b6b', alpha=0.7, fontsize=11, rotation=90, va='center')
    ax.set_xscale('log'); ax.set_xlim(left=0.8); ax.set_ylim(0, 1.02)
    ax.set_xlabel('Runqueue Delay (μs)', fontsize=12, color='#e0e0e0')
    ax.set_ylabel('CDF', fontsize=12, color='#e0e0e0')
    ax.set_title('CPU Contention Threshold: When Does p99 Cross 1ms?', fontsize=14,
                 color='#ffffff', fontweight='bold')
    ax.grid(True, alpha=0.15); ax.tick_params(colors='#b0b0b0')
    for p, lbl in [(0.95, 'p95'), (0.99, 'p99')]:
        ax.axhline(y=p, color='#ffffff', alpha=0.15, linestyle='--', linewidth=0.8)
        ax.text(1, p+0.01, lbl, color='#ffffff', alpha=0.4, fontsize=9)
    # Precise percentile annotation box
    lines = ["  Exp    p50      p95      p99      p99.9"]
    lines.append("  " + "─" * 42)
    for exp in ['E1', 'E13', 'E3', 'E4']:
        m = METRICS[exp]
        lines.append(f"  {exp:4s} {_fmt_us(m['p50']):>7s} {_fmt_us(m['p95']):>8s}  {_fmt_us(m['p99']):>8s}  {_fmt_us(m['p999']):>8s}")
    ax.text(0.02, 0.55, '\n'.join(lines), transform=ax.transAxes,
            fontsize=9, fontfamily='monospace', color='#c0c0c0', alpha=0.9,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#1a1a2e',
                      edgecolor='#444444', alpha=0.85), verticalalignment='top')
    legend = ax.legend(loc='lower right', fontsize=10, framealpha=0.8,
                       facecolor='#1a1a2e', edgecolor='#444444')
    for t in legend.get_texts(): t.set_color('#e0e0e0')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_contention_threshold.png"), dpi=150,
                bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    plt.style.use('default')


# ═══════════════════════════════════════════════════════════════════
# PLOT 20: All Mitigations CDF Overview
# ═══════════════════════════════════════════════════════════════════
def plot_20_all_mitigations_cdf():
    print("  Plot 20: All mitigations CDF overview...")
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#16213e')
    experiments = {
        'E4 (baseline)':     ('E4',  '#e74c3c', '-',  2.5),
        'E5 (RPS→CPU0)':    ('E5',  '#9b59b6', '--', 1.5),
        'E6 (RPS→all)':     ('E6',  '#3498db', '--', 1.5),
        'E7 (app pinned)':  ('E7',  '#1abc9c', '--', 1.5),
        'E8 (RPS+pin)':     ('E8',  '#e67e22', '--', 1.5),
        'E9 (CFS lowlat)':  ('E9',  '#95a5a6', '--', 1.5),
        'E10 (ksoftirqd)':  ('E10', '#f1c40f', '--', 1.5),
        'E14 (combined)':   ('E14', '#2ecc71', '-.', 2.0),
        'E15 (RPS+bpoll)':  ('E15', '#00bcd4', '-.', 2.0),
        'E16 (bpoll only)': ('E16', '#ff9800', '-.', 2.0),
    }
    for label, (exp, color, ls, lw) in experiments.items():
        buckets = HISTOGRAM_BUCKETS.get(exp, [])
        x, y = histogram_to_cdf(buckets)
        if len(x) > 0:
            ax.plot(x, y, label=label, color=color, linestyle=ls, linewidth=lw)
    ax.set_xscale('log'); ax.set_xlim(1, 2e5); ax.set_ylim(0.9, 1.001)
    ax.set_xlabel('Run-queue Delay (μs)', fontsize=13, color='#e0e0e0', fontweight='bold')
    ax.set_ylabel('CDF', fontsize=13, color='#e0e0e0', fontweight='bold')
    ax.set_title('All Mitigations vs E4 Baseline — Scheduling Delay CDF', fontsize=14,
                 color='#ffffff', fontweight='bold', pad=15)
    ax.axhline(y=0.99, color='#ff6b6b', linestyle=':', alpha=0.5, linewidth=1)
    ax.text(2, 0.9905, 'p99', color='#ff6b6b', fontsize=9, alpha=0.6)
    ax.tick_params(colors='#b0b0b0')
    ax.grid(True, alpha=0.15, color='#ffffff')
    legend = ax.legend(loc='lower right', fontsize=9, ncol=2, framealpha=0.8,
                       facecolor='#1a1a2e', edgecolor='#444444')
    for t in legend.get_texts(): t.set_color('#e0e0e0')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_all_mitigations_cdf_overview.png"), dpi=150,
                bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    plt.style.use('default')


# ═══════════════════════════════════════════════════════════════════
# PLOT 21: Softirq CPU% comparison
# ═══════════════════════════════════════════════════════════════════
def plot_21_softirq_cpu_pct():
    print("  Plot 21: Softirq CPU%...")
    exps = ALL_EXPS
    vals = [METRICS[e]["softirq_cpu_pct"] for e in exps]
    colors = [get_color(e) for e in exps]
    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(range(len(exps)), vals, color=colors, alpha=0.85, edgecolor='white')
    ax.set_xticks(range(len(exps)))
    ax.set_xticklabels(exps, rotation=45, ha='right')
    ax.set_ylabel('Softirq CPU %', fontsize=12)
    ax.set_title('Softirq CPU Utilization per Experiment', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "24_softirq_cpu_pct.png"), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════
# Write Metrics CSV
# ═══════════════════════════════════════════════════════════════════
def write_metrics_csv():
    print("  Writing metrics CSV...")
    csv_path = os.path.join(PLOT_DIR, "24_experiment_metrics.csv")
    with open(csv_path, 'w') as f:
        f.write("experiment,p50_us,p75_us,p90_us,p95_us,p99_us,p999_us,mean_us,"
                "ctx_switches,voluntary,throughput_gbps,retransmits,time_squeeze,"
                "migrations,softirq_cpu_pct\n")
        for exp in ALL_EXPS:
            m = METRICS[exp]
            f.write(f'{exp},{m["p50"]},{m["p75"]},{m["p90"]},{m["p95"]},{m["p99"]},'
                    f'{m["p999"]},{m["delay_mean"]},{m["ctx_switches"]},{m["voluntary"]},'
                    f'{m["throughput_gbps"]},{m["retransmits"]},{m["time_squeeze"]},'
                    f'{m["migrations"]},{m["softirq_cpu_pct"]}\n')
    print(f"    → {csv_path}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    print("=" * 60)
    print("  Hardcoded Plot Generation — 21 Plots")
    print("  Precise percentiles from sampled sched_delay.csv events")
    print("  (No raw data file parsing — instant generation)")
    print("=" * 60)
    print()

    print("Generating plots...")
    plot_1_all_cdf()
    plot_2_percentile_bars()
    plot_3_softirq_heatmap()
    plot_4_mitigation_comparison()
    plot_5_boxplot()
    plot_6_context_switches()
    plot_7_voluntary_switches()
    plot_8_retransmits()
    plot_9_cpu_migrations()
    plot_10_scatter_softirq_vs_delay()
    plot_11_baseline_cdf()
    plot_12_tcp_vs_udp()
    plot_13_degradation_factors()
    plot_14_per_cpu_rps()
    plot_15_h1_concentration()
    plot_16_h4_mitigations_cdf()
    plot_17_throughput()
    plot_18_summary_table()
    plot_19_contention_threshold()
    plot_20_all_mitigations_cdf()
    plot_21_softirq_cpu_pct()
    write_metrics_csv()

    print()
    print("=" * 60)
    n_plots = len([f for f in os.listdir(PLOT_DIR) if f.endswith('.png')])
    print(f"  Done! {n_plots} plots in {os.path.abspath(PLOT_DIR)}")
    print("=" * 60)

    # percentile summary with REAL values
    print("\n---- Precise Percentile Summary (from sampled events) ----")
    print(f"{'Exp':<5} {'p50':>8} {'p90':>8} {'p95':>8} {'p99':>10} {'p99.9':>10} {'Mean':>8} {'TP(Gbps)':>9} {'SIrq%':>6}")
    for exp in ALL_EXPS:
        m = METRICS[exp]
        print(f'{exp:<5} {_fmt_us(m["p50"]):>8} {_fmt_us(m["p90"]):>8} {_fmt_us(m["p95"]):>8} '
              f'{_fmt_us(m["p99"]):>10} {_fmt_us(m["p999"]):>10} {_fmt_us(m["delay_mean"]):>8} '
              f'{m["throughput_gbps"]:>8.1f}  {m["softirq_cpu_pct"]:>5.1f}')
