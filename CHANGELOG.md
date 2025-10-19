# Changelog

All notable changes to Pocketnet Watch will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-19

### 🎉 Major Architecture Shift - Bash to Python

This release represents a complete rewrite of Pocketnet Watch from Bash to Python 3 with the curses library, delivering a professional, flicker-free monitoring experience.

### Added
- **Python/curses implementation** - Smooth, flicker-free terminal UI similar to htop/vim
- **Fork detection system** - Visual indicators (✓/⚠) for blockchain health monitoring
  - Only counts recent forks (within 100 blocks)
  - Alerts when >3 competing chains detected
- **Multi-line peer histogram** - Visual representation of node version distribution
  - Shows top 3 peer versions with ASCII bar graphs
  - Displays connection breakdown (In/Out)
- **Enhanced time formatting** - Human-readable durations (days/hours/minutes)
- **Command-line arguments** - `-c` (compact), `-b` (boxed), `-r` (refresh interval)
- **Comprehensive documentation** - Full docstrings, inline comments, and user guides
- **Screenshots** - Visual examples of boxed and compact modes
- **CHANGELOG.md** - This file for tracking version history

### Changed
- **Rendering engine** - Migrated from bash clear/echo to curses double-buffering
- **Display modes** - Improved boxed and compact UI layouts
- **Color handling** - Now respects terminal color schemes (no more forced black background)
- **Cursor visibility** - Hidden during updates for cleaner appearance
- **Data caching** - Two-tier strategy (fast/slow updates) to reduce node load
- **Node Status section** - Removed redundant "Network Status" metric
- **Connection details** - Moved to "Connected Nodes" in Peers section
- **Database metrics** - Now shows total consumed space from all 4 components
- **Peer versions** - Changed from single-line to multi-line histogram display
- **Label updates** - "Peer Versions" → "Connected Nodes"

### Fixed
- **Flickering display** - Completely eliminated through curses implementation
- **Scrolling issues** - Display now updates in-place without scrolling
- **Fork count bug** - Was counting 38,000+ historical forks, now filters to recent only
- **Stake report errors** - Fixed "Unknown format code 'f'" by converting strings to floats
- **Empty peer versions** - Now labeled as "Unknown" instead of showing "v"
- **Line ending issues** - Proper Unix (LF) line endings throughout
- **Deprecated warnings** - Updated to `datetime.now(timezone.utc)` from `utcnow()`

### Technical Details
- **Language**: Python 3.10+
- **Dependencies**: curses (built-in), argparse, json, subprocess
- **Architecture**: MVC-like pattern (DataCache → MetricCollector → UIRenderer)
- **Performance**: Minimal CPU usage with efficient screen updates
- **Compatibility**: Ubuntu 22.04+, works over SSH

## [0.6.0] - 2025-10-18

### Changed - Bash Refactor
- JSON-driven UI configuration for flexible customization
- Modular metric functions for better maintainability
- Improved code organization with clear function separation
- Enhanced number formatting with thousand separators

### Added
- Multi-line histogram for peer versions
- Configurable UI sections via JSON
- Support for external configuration files
- Detailed stake reports (1D, 7D, 30D, 365D)

## [0.5.0 and earlier] - 2025-03-26 and before

### Legacy Versions
- See `legacy/` directory for historical bash implementations
- Progressive improvements to metrics display
- Various UI enhancements and bug fixes
- Evolution from simple monitoring to comprehensive dashboard

---

## Version Numbering

- **Major version** (X.0.0) - Incompatible API/architecture changes
- **Minor version** (0.X.0) - New features, backwards compatible
- **Patch version** (0.0.X) - Bug fixes, backwards compatible

## Links

- [GitHub Repository](https://github.com/Pewejekubam/pocketnet_watch)
- [Documentation](docs/DOCUMENTATION.md)
- [Issues](https://github.com/Pewejekubam/pocketnet_watch/issues)
