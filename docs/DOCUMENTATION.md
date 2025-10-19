# Pocketnet Watch - Comprehensive Documentation

Complete guide to installation, configuration, and usage of Pocketnet Watch v2.0.0.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Metrics Reference](#metrics-reference)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
- [Contributing](#contributing)

---

## Installation

### Prerequisites

**Required:**
- Python 3.10 or higher
- Running Pocketnet node
- `pocketcoin-cli` in your PATH

**System utilities:**
```bash
# Ubuntu/Debian
sudo apt-get install jq bc

# Check if already installed
which jq bc pocketcoin-cli
```

### Setup

1. **Clone or download the repository:**
   ```bash
   git clone https://github.com/Pewejekubam/pocketnet_watch.git
   cd pocketnet_watch
   ```

2. **Make executable:**
   ```bash
   chmod +x watch.py
   ```

3. **Test run:**
   ```bash
   ./watch.py
   ```

If you see the monitoring dashboard, you're ready to go!

---

## Configuration

### Command-Line Arguments

```bash
./watch.py [OPTIONS]
```

| Option            | Description                 | Default  |
|-------------------|-----------------------------|----------|
| `-h, --help`      | Show help message           |     -    |
| `-c, --compact`   | Use compact UI (no borders) | Boxed UI |
| `-b, --boxed`     | Use boxed UI (with borders) | Enabled  |
| `-r, --refresh N` | Refresh interval in seconds | 5        |
|-------------------|-----------------------------|----------|

**Examples:**
```bash
# Boxed UI, 5-second refresh (default)
./watch.py

# Compact mode, 3-second refresh
./watch.py -c -r 3

# Boxed mode with 10-second refresh
./watch.py -b -r 10
```

### Environment Variables

If your `pocketcoin-cli` requires special arguments, edit the `POCKETCOIN_CLI_ARGS` variable in `watch.py`:

```python
# Line 41 in watch.py
POCKETCOIN_CLI_ARGS = ""  # Add custom args here if needed
```

Example for custom RPC port:
```python
POCKETCOIN_CLI_ARGS = "-rpcport=38081"
```

### Custom Refresh Rate

The default refresh rate is 5 seconds, which provides a good balance between real-time updates and system load. Adjust based on your needs:

- **Fast updates (2-3s)**: Good for active monitoring during debugging
- **Normal (5s)**: Recommended for general use
- **Slow (10-15s)**: Reduces load on node, good for background monitoring

---

## Usage

### Basic Operation

1. **Start monitoring:**
   ```bash
   ./watch.py
   ```

2. **Stop monitoring:**
   Press `Ctrl+C`

3. **Switch modes:**
   ```bash
   ./watch.py -c  # Compact mode
   ./watch.py -b  # Boxed mode (default)
   ```

### Understanding the Display

#### Boxed Mode Layout

```
┌─ Section_Name ───────────────────────────────────┐
│ Metric Label: Value    Metric Label: Value       │
│ Metric Label: Value                              │
└──────────────────────────────────────────────────┘
```

#### Compact Mode Layout

```
-- Section_Name --
Metric Label: Value
Metric Label: Value
```

### Visual Indicators

| Indicator | Meaning |
|--------------|-------------------------|
| `✓`          | Healthy (fork count ≤3) |
| `⚠`          | Warning (fork count >3) |
| `TRUE/FALSE` | Staking status          |
| `#####`      | Histogram bars          |

---

## Metrics Reference

### Node Status Section

| Metric | Description | Source |
|--------|-------------|--------|
| Node Version | Pocketcoin version | `getinfo` |
| Node Time | Current UTC time | System |
| Uptime | Node uptime | `uptime` RPC |
| Sync Status | Blockchain sync percentage | `getblockchaininfo` |

### Blockchain Section

| Metric | Description | Source |
|--------|-------------|--------|
| Block Height | Current block with fork indicator | `getblockchaininfo` + `getchaintips` |
| Difficulty | Current network difficulty | `getstakinginfo` |
| Hash Rate | Network hash rate (H/s, KH/s, etc.) | `getnetworkhashps` |
| Memory Pool | Transaction count and size | `getmempoolinfo` |
| Net Stake Weight | Total network staking weight | `getstakinginfo` |
| Fork Alert | Conditional alert for >3 recent forks | `getchaintips` |

**Fork Detection:**
- Monitors forks within last 100 blocks
- Only counts `valid-fork` status
- Ignores historical orphaned blocks

### Connected Nodes Section

| Metric | Description | Source |
|--------|-------------|--------|
| Total Peers | Count with In/Out breakdown | `getnetworkinfo` |
| Version Histogram | Top 3 versions with visual bars | `getpeerinfo` |

**Histogram Details:**
- Shows version, count, percentage, visual bar
- Capped at 3 versions to save space
- Bar length scales with peer percentage
- Unknown versions labeled as "Unknown"

### Peers & Database Section

| Metric | Description | Source |
|--------|-------------|--------|
| Blockchain Database | Total consumed disk space | `du` on blocks, chainstate, indexes, pocketdb |

### Wallet Section

| Metric | Description | Source |
|--------|-------------|--------|
| Balance | Formatted wallet balance | `getwalletinfo` |
| Status | Lock status and time remaining | `getwalletinfo` |
| Unconfirmed Balance | Pending transactions | `getwalletinfo` |
| Address | Highest balance address | `listaddressgroupings` |

### Staking Section

| Metric | Description | Source |
|--------|-------------|--------|
| Status | Whether staking is active | `getstakinginfo` |
| Weight Ratio | Your weight / network weight | `getstakinginfo` |
| Last Reward | Time since last stake | `getstakereport` |
| Expected Time | Estimated time to next stake | `getstakinginfo` |
| Stake Report | Earnings over 1D/7D/30D/1Y | `getstakereport` |
| Stake Wins | Total successful stakes | `getstakereport` |

### System Resources Section

| Metric | Description | Source |
|--------|-------------|--------|
| Disk | Blockchain directory usage | `df` |
| CPU | Current CPU usage percentage | `top` |
| RAM | Total/Used/Free memory | `free` |
| Swap | Swap usage | `free` |
| Uptime | System uptime | `uptime` |
| Load Avg | 1/5/15 minute load averages | `uptime` |

---

## Customization

### Modifying the JSON Configuration

The UI layout is defined in the `DEFAULT_UI_SECTIONS` dictionary (line 46 in `watch.py`). You can modify this to add, remove, or reorder sections.

**Structure:**
```python
"Section_Name": {
    "layout": [
        {
            "row": [
                {
                    "metric": "function_name",  # Name of get_* function
                    "label": "Display Label",    # What user sees
                    "width": 32                  # Column width
                }
            ]
        }
    ]
}
```

### Adding a Custom Metric

1. **Create a metric function in the `MetricCollector` class:**
   ```python
   def get_custom_metric(self) -> str:
       """Your custom metric description"""
       try:
           # Get your data
           result = subprocess.run("your-command",
                                   shell=True, capture_output=True, text=True)
           return result.stdout.strip()
       except:
           return "Unknown"
   ```

2. **Add to JSON configuration:**
   ```python
   {
       "row": [
           {
               "metric": "custom_metric",  # matches get_custom_metric()
               "label": "My Metric",
               "width": 40
           }
       ]
   }
   ```

### Multi-line Metrics

For metrics that return multiple lines (like `get_peer_versions()`):

1. Return lines joined with `\n`:
   ```python
   return '\n'.join(lines)
   ```

2. The renderer will automatically:
   - Apply the label to the first line
   - Display subsequent lines without labels

### Conditional Metrics

For metrics that should only display when relevant (like `fork_alert`):

1. Return empty string when not needed:
   ```python
   if condition_not_met:
       return ""
   ```

2. The renderer will skip empty values

---

## Troubleshooting

### Common Issues

**Problem: `/usr/bin/env: 'python3\r': No such file or directory`**
- **Cause:** Windows line endings (CRLF)
- **Fix:** Run `dos2unix watch.py` or `sed -i 's/\r$//' watch.py`

**Problem: `pocketcoin-cli: command not found`**
- **Cause:** `pocketcoin-cli` not in PATH
- **Fix:** Add to PATH or use full path in `POCKETCOIN_CLI_ARGS`

**Problem: Display flickers or jumps**
- **Cause:** Terminal doesn't support curses properly
- **Fix:** Try a different terminal emulator (recommended: GNOME Terminal, Konsole, iTerm2)

**Problem: Colors don't match my terminal theme**
- **Cause:** Curses was forcing black background (fixed in v2.0.0)
- **Fix:** Update to latest version with `use_default_colors()`

**Problem: Metrics show "N/A" or "Unknown"**
- **Cause:** RPC call failed or timed out
- **Fix:**
  - Check if node is running: `pocketcoin-cli getinfo`
  - Check RPC permissions
  - Increase timeout in code if needed

**Problem: Fork count shows huge number (>1000)**
- **Cause:** Bug in older version counting all historical forks
- **Fix:** Update to v2.0.0+ which only counts recent forks

### Debug Mode

To see detailed error messages, you can run Python directly:

```bash
python3 -u watch.py 2>&1 | tee watch-debug.log
```

This will capture all output including exceptions.

### Performance Issues

If the script feels slow:

1. **Increase refresh interval:**
   ```bash
   ./watch.py -r 10  # Update every 10 seconds
   ```

2. **Check node performance:**
   ```bash
   pocketcoin-cli getblockchaininfo  # Should respond quickly
   ```

3. **Monitor system resources:**
   - Watch CPU usage with `top`
   - Check if node is syncing or under heavy load

---

## Architecture

### Technology Stack

- **Python 3.10+**: Core language
- **curses library**: Terminal UI rendering
- **subprocess**: RPC communication with `pocketcoin-cli`
- **json**: Data parsing
- **argparse**: Command-line arguments

### Code Structure

```
watch.py
├── Configuration (lines 40-288)
│   └── DEFAULT_UI_SECTIONS JSON
├── DataCache class (lines 290-329)
│   └── RPC call caching
├── Utility Functions (lines 335-366)
│   └── Formatting helpers
├── MetricCollector class (lines 372-720)
│   └── All get_* metric functions
├── UIRenderer class (lines 727-933)
│   └── Curses rendering logic
└── Main application (lines 938-978)
    └── Argument parsing and loop
```

### Design Principles

1. **Separation of concerns**: Data collection, processing, and rendering are separate
2. **Caching**: RPC calls are cached to reduce load (every 3 cycles for less-frequently-changing data)
3. **Error handling**: Graceful fallbacks for all RPC failures
4. **Flexibility**: JSON-driven configuration for easy customization
5. **Performance**: Curses only redraws changed content

### Data Flow

```
1. Main loop starts
   ↓
2. DataCache.update() calls pocketcoin-cli RPCs
   ↓
3. MetricCollector reads from cache
   ↓
4. UIRenderer formats and displays
   ↓
5. Sleep for refresh interval
   ↓
6. Repeat from step 2
```

---

## Contributing

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Test thoroughly:**
   ```bash
   ./watch.py  # Test normal mode
   ./watch.py -c  # Test compact mode
   ```
5. **Commit with descriptive message:**
   ```bash
   git commit -m "Add amazing feature that does X"
   ```
6. **Push to your fork:**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Coding Guidelines

- **Python style**: Follow PEP 8
- **Type hints**: Use for all function signatures
- **Docstrings**: Add for all public functions
- **Error handling**: Use try/except with fallbacks
- **Comments**: Explain why, not what

### Testing Checklist

Before submitting a PR:

- [ ] Runs without errors on Python 3.10+
- [ ] Works in both boxed and compact modes
- [ ] Handles RPC failures gracefully
- [ ] No line ending issues (Unix LF only)
- [ ] Documentation updated if needed

### Ideas for Contribution

- Add new metrics (bandwidth, transaction history, etc.)
- Improve error messages
- Add color coding for warnings/errors
- Create configuration file support
- Add interactive features (pause, sort, filter)
- Improve documentation
- Add unit tests
- Create installation script

---

## Changelog

### v2.0.0 (2025-10-19) - Python Rewrite

**Major Changes:**
- Complete rewrite from Bash to Python
- Curses library for flicker-free rendering
- Terminal color scheme adaptation
- Efficient screen updates (only changed content)

**New Features:**
- Fork detection with visual indicators (✓/⚠)
- Multi-line peer version histogram
- Time since last stake reward
- Recent fork filtering (100 blocks)
- Conditional metric display
- Command-line argument parsing

**Improvements:**
- Hidden cursor during updates
- Better error handling
- Improved time formatting
- Float parsing for stake report
- Empty version handling in peer list

**Bug Fixes:**
- Fixed huge fork count display
- Fixed stake report format errors
- Fixed deprecated datetime warnings
- Fixed line ending issues

### v0.6.0 (2025-10-18) - Bash Refactor

- JSON-driven UI configuration
- Modular metric functions
- Improved code organization
- Function-based architecture

### Earlier Versions

See `legacy/` directory for historical versions (v0.0 - v0.5.0).

---

## FAQ

**Q: Why Python instead of Bash?**
A: Python with curses provides flicker-free rendering, better structure, and easier maintenance.

**Q: Does it work on macOS?**
A: Yes! Python 3.10+ and curses are available on macOS. Just ensure `pocketcoin-cli` is in your PATH.

**Q: Can I run this over SSH?**
A: Absolutely! Curses works great over SSH. Just make sure your terminal supports it.

**Q: How much system resources does it use?**
A: Minimal - typically <1% CPU and <50MB RAM. The RPC calls to your node have more impact than the script itself.

**Q: Can I monitor multiple nodes?**
A: Not currently from one instance. You'd need to run separate instances with different `POCKETCOIN_CLI_ARGS` pointing to different nodes.

**Q: Is there a web interface version?**
A: Not yet, but it's a great contribution idea!

---

## Support

- **Issues**: [GitHub Issues](https://github.com/Pewejekubam/pocketnet_watch/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Pewejekubam/pocketnet_watch/discussions)
- **Pocketnet Community**: [pocketnet.app](https://pocketnet.app)

---

**Last Updated**: 2025-10-19
**Version**: 2.0.0
