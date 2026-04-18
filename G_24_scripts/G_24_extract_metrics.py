#!/usr/bin/env python3
"""
24_extract_metrics.py — Extract REAL metrics from experiment data files.

Computes PRECISE percentiles from sampled sched_delay.csv events (not histogram buckets).
Extracts throughput, context switches, softirq CPU%, retransmits, etc.

Usage: python3 scripts/24_extract_metrics.py > analysis/24_hardcoded_data.py
"""
import os, re, sys, json, csv
import numpy as np

DATA_DIR = os.path.expanduser("~/Desktop/GRS Project/MT25037/data")
ALL_EXPS = [f"E{i}" for i in range(1, 17)]

# ─── Precise Percentiles from Sampled CSV ──────────────────────────
def get_precise_percentiles(csv_path):
    """Read sched_delay.csv and compute exact percentiles from sampled events."""
    if not os.path.exists(csv_path):
        return {}
    delays = []
    with open(csv_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('timestamp') or not line[0].isdigit():
                continue
            parts = line.split(',')
            if len(parts) >= 5:
                try:
                    delays.append(float(parts[4]))
                except ValueError:
                    continue
    if not delays:
        return {}
    arr = np.array(delays)
    return {
        'count': len(arr),
        'mean': round(float(np.mean(arr)), 2),
        'min': round(float(np.min(arr)), 2),
        'max': round(float(np.max(arr)), 2),
        'p50': round(float(np.percentile(arr, 50)), 2),
        'p75': round(float(np.percentile(arr, 75)), 2),
        'p90': round(float(np.percentile(arr, 90)), 2),
        'p95': round(float(np.percentile(arr, 95)), 2),
        'p99': round(float(np.percentile(arr, 99)), 2),
        'p999': round(float(np.percentile(arr, 99.9)), 2),
    }

# ─── Histogram Parsing (for CDF plots) ────────────────────────────
def parse_suffix(s):
    s = s.strip()
    if s.endswith('K'): return int(s[:-1]) * 1024
    if s.endswith('M'): return int(s[:-1]) * 1024 * 1024
    return int(s)

def get_last_histogram(filepath):
    if not os.path.exists(filepath): return []
    with open(filepath, 'r') as f:
        content = f.read()
    blocks, current, in_block = [], [], False
    for line in content.split('\n'):
        if '@runq_delay_us:' in line:
            if current: blocks.append(current)
            current, in_block = [], True
            continue
        if in_block:
            line = line.strip()
            if line.startswith('['):
                m = re.match(r'\[([0-9KMG]+)(?:,\s*([0-9KMG]+))?\)?\s+(\d+)\s+\|', line)
                if m:
                    low = parse_suffix(m.group(1))
                    high = parse_suffix(m.group(2)) if m.group(2) else low + 1
                    count = int(m.group(3))
                    current.append((low, high, count))
            elif line == '' or line.startswith('@'):
                if current: blocks.append(current); current = []
                in_block = '@runq_delay_us:' in line
                if in_block: current = []
    if current: blocks.append(current)
    return blocks[-1] if blocks else []

# ─── Other Metric Extraction ──────────────────────────────────────
def get_ctx_switches(filepath):
    if not os.path.exists(filepath): return 0
    val = 0
    with open(filepath, 'r') as f:
        for line in f:
            if '@ctx_switches:' in line:
                try: val = int(line.split()[-1])
                except Exception: pass
    return val

def get_voluntary(filepath):
    if not os.path.exists(filepath): return 0
    val = 0
    with open(filepath, 'r') as f:
        for line in f:
            if '@voluntary:' in line:
                try: val = int(line.split()[-1])
                except Exception: pass
    return val

def get_iperf3_throughput(filepath):
    if not os.path.exists(filepath): return 0
    try:
        with open(filepath) as f:
            data = json.load(f)
        end = data.get('end', {})
        sr = end.get('sum_received', end.get('sum', {}))
        return sr.get('bits_per_second', 0)
    except Exception: return 0

def get_tcp_retransmits(filepath):
    if not os.path.exists(filepath): return 0
    try:
        lines = open(filepath).readlines()
        if len(lines) < 2: return 0
        first = lines[1].strip().split(',')
        last = lines[-1].strip().split(',')
        return int(last[1]) - int(first[1])
    except Exception: return 0

def get_softnet_squeeze(filepath):
    if not os.path.exists(filepath): return 0
    try:
        lines = open(filepath).readlines()
        if len(lines) < 2: return 0
        header = lines[0].strip().split(',')
        sq_idx = header.index('time_squeeze')
        first_vals, last_vals = {}, {}
        for line in lines[1:11]:
            parts = line.strip().split(',')
            cpu = int(parts[1])
            first_vals[cpu] = int(parts[sq_idx], 16)
        for line in lines[-8:]:
            parts = line.strip().split(',')
            if len(parts) >= 5:
                cpu = int(parts[1])
                last_vals[cpu] = int(parts[sq_idx], 16)
        total = 0
        for cpu in last_vals:
            if cpu in first_vals:
                total += last_vals[cpu] - first_vals[cpu]
        return total
    except Exception: return 0

def get_softirq_per_cpu(filepath):
    if not os.path.exists(filepath): return {}
    with open(filepath, 'r') as f:
        content = f.read()
    pattern = re.compile(r'^@net_rx_count\[(\d+)\]:\s+(\d+)', re.M)
    blocks, current = [], {}
    for line in content.split('\n'):
        m = pattern.match(line.strip())
        if m:
            current[int(m.group(1))] = int(m.group(2))
        elif current:
            blocks.append(current); current = {}
    if current: blocks.append(current)
    return blocks[-1] if blocks else {}

def get_cpu_migrations_total(filepath):
    if not os.path.exists(filepath): return 0
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        blocks, current = [], {}
        for line in content.split('\n'):
            m = re.match(r'@migrations\[(.+?)\]:\s+(\d+)', line.strip())
            if m:
                current[m.group(1)] = int(m.group(2))
            elif current:
                blocks.append(current); current = {}
        if current: blocks.append(current)
        if blocks:
            return sum(blocks[-1].values())
        return 0
    except Exception: return 0

def get_cpu_softirq_pct(filepath):
    """Compute softirq CPU% from cpu_util.csv (delta-based)."""
    if not os.path.exists(filepath): return 0.0
    try:
        rows_by_ts = {}
        with open(filepath) as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts = float(row['timestamp'])
                softirq = int(row['softirq'])
                total = int(row['user']) + int(row['nice']) + int(row['system']) + \
                        int(row['idle']) + int(row['iowait']) + int(row['irq']) + \
                        int(row['softirq']) + int(row['steal'])
                if ts not in rows_by_ts:
                    rows_by_ts[ts] = {'softirq': 0, 'total': 0}
                rows_by_ts[ts]['softirq'] += softirq
                rows_by_ts[ts]['total'] += total
        timestamps = sorted(rows_by_ts.keys())
        if len(timestamps) < 2: return 0.0
        d_si = rows_by_ts[timestamps[-1]]['softirq'] - rows_by_ts[timestamps[0]]['softirq']
        d_total = rows_by_ts[timestamps[-1]]['total'] - rows_by_ts[timestamps[0]]['total']
        return round(d_si / d_total * 100, 2) if d_total > 0 else 0.0
    except Exception: return 0.0

# ─── Average histogram buckets across runs ─────────────────────────
def get_avg_histogram_buckets(exp):
    all_buckets = {}
    for run in ['run_1', 'run_2', 'run_3']:
        fpath = os.path.join(DATA_DIR, exp, run, 'sched_delay_summary.txt')
        buckets = get_last_histogram(fpath)
        for low, high, count in buckets:
            key = (low, high)
            if key not in all_buckets:
                all_buckets[key] = []
            all_buckets[key].append(count)
    result = []
    for (low, high), counts in sorted(all_buckets.items()):
        result.append((low, high, int(np.mean(counts))))
    return result


# ═══════════════════════════════════════════════════════════════════
# MAIN — Write the hardcoded data module
# ═══════════════════════════════════════════════════════════════════
print("#!/usr/bin/env python3")
print('"""')
print("Hardcoded experiment metrics — extracted from real data files.")
print("Percentiles computed from sampled sched_delay.csv events (NOT histogram buckets).")
print(f"Generated by scripts/24_extract_metrics.py")
print('"""')
print()

# ─── Histogram CDF Buckets ─────────────────────────────────────────
print("# ─── Histogram CDF Buckets (averaged across 3 runs) ────────")
print("# Used for CDF curve plotting only")
print("# Format: list of (bucket_low_us, bucket_high_us, avg_count)")
print("HISTOGRAM_BUCKETS = {")
for exp in ALL_EXPS:
    print(f"  Extracting histograms for {exp}...", file=sys.stderr)
    buckets = get_avg_histogram_buckets(exp)
    print(f'    "{exp}": {buckets},')
print("}")
print()

# ─── Per-experiment metrics ────────────────────────────────────────
print("# ─── Per-experiment metrics (averaged across 3 runs) ────────")
print("# PRECISE percentiles computed from sampled sched_delay.csv events")
print("METRICS = {")
for exp in ALL_EXPS:
    print(f"  Extracting metrics for {exp}...", file=sys.stderr)

    # Collect per-run values
    all_pcts = []
    all_ctx = []
    all_vol = []
    all_tp = []
    all_retrans = []
    all_squeeze = []
    all_mig = []
    all_sirq_pct = []

    for run in ['run_1', 'run_2', 'run_3']:
        run_dir = os.path.join(DATA_DIR, exp, run)
        # PRECISE percentiles from sampled CSV
        pcts = get_precise_percentiles(os.path.join(run_dir, 'sched_delay.csv'))
        if pcts:
            all_pcts.append(pcts)
        all_ctx.append(get_ctx_switches(os.path.join(run_dir, 'sched_delay_summary.txt')))
        all_vol.append(get_voluntary(os.path.join(run_dir, 'sched_delay_summary.txt')))
        all_tp.append(get_iperf3_throughput(os.path.join(run_dir, 'iperf3_result.json')))
        all_retrans.append(get_tcp_retransmits(os.path.join(run_dir, 'tcp_stats.csv')))
        all_squeeze.append(get_softnet_squeeze(os.path.join(run_dir, 'softnet_stat.csv')))
        all_mig.append(get_cpu_migrations_total(os.path.join(run_dir, 'cpu_migrations_summary.txt')))
        all_sirq_pct.append(get_cpu_softirq_pct(os.path.join(run_dir, 'cpu_util.csv')))

    # Average percentiles across runs
    avg_pcts = {}
    if all_pcts:
        for key in ['count', 'mean', 'min', 'max', 'p50', 'p75', 'p90', 'p95', 'p99', 'p999']:
            vals = [d[key] for d in all_pcts if key in d]
            avg_pcts[key] = round(float(np.mean(vals)), 2) if vals else 0

    # Softirq per CPU (from run_1)
    sirq_cpu = get_softirq_per_cpu(os.path.join(DATA_DIR, exp, 'run_1', 'softirq_net_summary.txt'))

    print(f'    "{exp}": {{')
    print(f'        "sample_count": {avg_pcts.get("count", 0)},')
    print(f'        "delay_mean": {avg_pcts.get("mean", 0)},')
    print(f'        "delay_min": {avg_pcts.get("min", 0)},')
    print(f'        "delay_max": {avg_pcts.get("max", 0)},')
    print(f'        "p50": {avg_pcts.get("p50", 0)},')
    print(f'        "p75": {avg_pcts.get("p75", 0)},')
    print(f'        "p90": {avg_pcts.get("p90", 0)},')
    print(f'        "p95": {avg_pcts.get("p95", 0)},')
    print(f'        "p99": {avg_pcts.get("p99", 0)},')
    print(f'        "p999": {avg_pcts.get("p999", 0)},')
    print(f'        "ctx_switches": {int(np.mean(all_ctx))},')
    print(f'        "voluntary": {int(np.mean(all_vol))},')
    print(f'        "throughput_bps": {int(np.mean(all_tp))},')
    print(f'        "throughput_mbps": {round(np.mean(all_tp)/1e6, 2)},')
    print(f'        "throughput_gbps": {round(np.mean(all_tp)/1e9, 2)},')
    print(f'        "retransmits": {int(np.mean(all_retrans))},')
    print(f'        "migrations": {int(np.mean(all_mig))},')
    print(f'        "time_squeeze": {int(np.mean(all_squeeze))},')
    print(f'        "softirq_per_cpu": {dict(sorted(sirq_cpu.items()))},')
    print(f'        "softirq_cpu_pct": {round(float(np.mean(all_sirq_pct)), 2)},')
    print(f'    }},')

print("}")
print()

# ─── Experiment configurations ─────────────────────────────────
print("# ─────────────── Experiment configurations ──────────────────────")
print("EXP_CONFIG = {")
configs = [
    ("E1", "none", "low", "default", "none", "default", "default", "tcp"),
    ("E2", "none", "high", "default", "none", "default", "default", "tcp"),
    ("E3", "heavy", "low", "default", "none", "default", "default", "tcp"),
    ("E4", "heavy", "high", "default", "none", "default", "default", "tcp"),
    ("E5", "heavy", "high", "rps_pinned", "none", "default", "default", "tcp"),
    ("E6", "heavy", "high", "rps_spread", "none", "default", "default", "tcp"),
    ("E7", "heavy", "high", "default", "pinned", "default", "default", "tcp"),
    ("E8", "heavy", "high", "rps_pinned", "pinned", "default", "default", "tcp"),
    ("E9", "heavy", "high", "default", "none", "lowlatency", "default", "tcp"),
    ("E10", "heavy", "high", "default", "none", "default", "forced_ksoftirqd", "tcp"),
    ("E11", "none", "high", "default", "none", "default", "default", "udp"),
    ("E12", "heavy", "high", "default", "none", "default", "default", "udp"),
    ("E13", "moderate", "high", "default", "none", "default", "default", "tcp"),
    ("E14", "heavy", "high", "rps_spread", "pinned", "lowlatency", "default", "tcp"),
    ("E15", "heavy", "high", "rps_spread", "none", "default", "default", "tcp"),
    ("E16", "heavy", "high", "default", "none", "default", "default", "tcp"),
]
for c in configs:
    print(f'    "{c[0]}": {{"cpu_stress": "{c[1]}", "net_load": "{c[2]}", "rps": "{c[3]}", '
          f'"app_pin": "{c[4]}", "cfs": "{c[5]}", "softirq_mode": "{c[6]}", "protocol": "{c[7]}"}},')
print("}")
