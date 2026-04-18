# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-04-18

### Added
- Complete experiment framework with 16 experiments (E1-E16)
- eBPF instrumentation probes for scheduling delay measurement
  - G_24_sched_delay.bt: runqueue delay histograms + sampled CSV
  - G_24_softirq_net.bt: per-CPU NET_RX/TX softirq duration
  - G_24_net_drops.bt: packet drops and TCP retransmits
  - G_24_cpu_migrations.bt: task CPU migration tracking
  - G_24_proc_pollers.sh: /proc polling for system stats
- Experiment orchestration scripts (4 phases)
- Analysis and visualization pipeline (21 plots)
- Hypothesis validation scripts (H1-H4)
- Custom SO_BUSY_POLL echo server for E15/E16
- Raw experiment data (48 runs, ~64 MB)
- 46 publication-quality plots
- Comprehensive README with results and architecture

### Fixed
- Renamed all files to follow G_24_ naming convention
- Fixed README image paths to match actual file structure
- Fixed Quick Start commands to use correct directory paths
- Fixed .gitignore to use correct G_24_ directory paths
- Fixed bare except clauses in Python scripts (PEP 8 E722)

### Documentation
- Added requirements.txt for Python dependencies
- Added MIT LICENSE file
- Added CONTRIBUTING.md with project guidelines
- Added .editorconfig for consistent coding standards
- Added CHANGELOG.md (this file)