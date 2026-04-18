# Contributing to G_24 â€” Kernel Scheduling Delay Profiling

Thank you for your interest in contributing to this project!

## Project Overview

This project profiles kernel scheduling delays under network-intensive
workloads using eBPF on Linux. It includes 16 controlled experiments
with automated orchestration, data collection, and analysis.

## Repository Structure

- **G_24_scripts/** â€” Experiment orchestration shell scripts
- **G_24_ebpf_tools/** â€” eBPF/bpftrace instrumentation probes
- **G_24_analysis/** â€” Python analysis and visualization scripts
- **G_24_data/** â€” Raw experiment data (16 experiments x 3 runs)
- **G_24_plots/** â€” Generated publication-quality plots

## Getting Started

### Prerequisites

- Ubuntu 22.04 LTS (or compatible)
- Linux kernel >= 5.15 with BTF support
- bpftrace >= 0.17.0
- Python 3.9+ with numpy and matplotlib

### Setup

`ash
# Install dependencies
sudo apt update && sudo apt install -y \
    bpftrace bpfcc-tools linux-tools- \
    iperf3 stress-ng memcached libmemcached-tools \
    python3-matplotlib python3-numpy

# Set up testbed
sudo G_24_scripts/G_24_setup_testbed.sh setup
`

## Running Experiments

Refer to the main [README.md](README.md) for detailed instructions
on running experiments and generating plots.

## Code Style

- **Python**: PEP 8, 4 spaces indentation
- **Shell**: POSIX-compatible bash, 4 spaces indentation
- **bpftrace**: 4 spaces indentation, descriptive probe comments

## Team

| Name | ID | Role |
|------|-----|------|
| Rohit Kumar | MT25037 | Experiment design & orchestration |
| Arpit Kumar | MT25017 | Data analysis & visualization |
| Abhinay Prakash | MT25010 | eBPF instrumentation & setup |
| Nindra Dhanush | MT25074 | Hypothesis validation |
| Adarsh Shukla | PhD25001 | Project lead & architecture |