#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Pocketnet Watch Script - Python/Curses Version
# -----------------------------------------------------------------------------
# This script monitors the status of a Pocketnet node by displaying various
# metrics and logs in a compact, organized UI. It retrieves information about
# wallet balance, node status, blockchain details, staking info, and system
# resources.
#
# REVISION HISTORY:
# v2.0.0 - 2025-10-19 - Major architecture shift from Bash to Python
#          - Migrated from Bash to Python 3 with curses library
#          - Implements flicker-free rendering with double-buffering
#          - Efficient screen updates (only redraws changed content)
#          - Hidden cursor during updates for cleaner display
#          - Maintains same JSON configuration structure from v0.6.0
#          - All metrics and functionality preserved from Bash version
#          - Professional TUI implementation similar to htop/vim
#
# v0.6.0 - 2025-10-18 - Refactored for maintainability (Bash)
#          - JSON-driven UI configuration
#          - Modular metric functions
#          - Improved code organization
#
# Previous versions (v0.0 - v0.5.0): See legacy/ directory
# -----------------------------------------------------------------------------

import curses
import json
import subprocess
import time
import os
import shutil
import argparse
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import configparser

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
# Default paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "pocketnet_watch_config.ini")
EXAMPLE_CONFIG_FILE = os.path.join(SCRIPT_DIR, "pocketnet_watch_config.ini.example")
DEFAULT_DATA_DIR = os.path.expanduser("~/.pocketcoin")
DEFAULT_PROBE_NODES_LOG = os.path.expanduser("~/probe_nodes/probe_nodes.log")

# Load configuration - create from example if it doesn't exist
config = configparser.ConfigParser()

if not os.path.exists(CONFIG_FILE) and os.path.exists(EXAMPLE_CONFIG_FILE):
    print(f"Creating default config file: {CONFIG_FILE}")
    shutil.copy(EXAMPLE_CONFIG_FILE, CONFIG_FILE)
config.read(CONFIG_FILE)

# Get configuration values or use defaults
POCKETCOIN_CLI_ARGS = config.get('pocketcoin', 'cli_args', fallback="")
REFRESH_SECONDS = config.getint('ui', 'refresh_seconds', fallback=5)
USE_BOXED_UI = config.getboolean('ui', 'use_boxed_ui', fallback=True)
DATA_DIR = config.get('pocketcoin', 'data_dir', fallback=DEFAULT_DATA_DIR)
PROBE_NODES_LOG = config.get('logs', 'probe_nodes_log', fallback=DEFAULT_PROBE_NODES_LOG)

# UI display mode - True for boxed UI with borders, False for compact mode
# Can be overridden via command-line arguments (-c or -b)

# Default JSON configuration for UI_SECTIONS
# This defines the layout, metrics, and structure of the monitoring dashboard.
# Each section contains:
#   - "layout": Array of rows, each containing metrics to display
#   - "metric": Name of the function to call (e.g., "node_version" calls get_node_version())
#   - "label": Display label shown to user
#   - "width": Column width for formatting
# Or for file-based sections:
#   - "file": Dictionary with "path" and "lines" to tail from a file
DEFAULT_UI_SECTIONS = {
    "Node_Status": {
        "layout": [
            {
                "row": [
                    {
                        "metric": "node_version",
                        "label": "Node Version",
                        "width": 32
                    },
                    {
                        "metric": "node_time",
                        "label": "Node Time",
                        "width": 34
                    }
                ]
            },
            {
                "row": [
                    {
                        "metric": "node_uptime",
                        "label": "Uptime",
                        "width": 32
                    },
                    {
                        "metric": "sync_status",
                        "label": "Sync Status",
                        "width": 20
                    }
                ]
            }
        ]
    },
    "Blockchain": {
        "layout": [
            {
                "row": [
                    {
                        "metric": "blockchain_blocks",
                        "label": "Block Height",
                        "width": 32
                    },
                    {
                        "metric": "difficulty",
                        "label": "Difficulty",
                        "width": 32
                    }
                ]
            },
            {
                "row": [
                    {
                        "metric": "network_hashps",
                        "label": "Hash Rate",
                        "width": 32
                    },
                    {
                        "metric": "mempool_info",
                        "label": "Memory Pool",
                        "width": 32
                    }
                ]
            },
            {
                "row": [
                    {
                        "metric": "net_stake_weight",
                        "label": "Net Stake Weight",
                        "width": 60
                    }
                ]
            },
            {
                "row": [
                    {
                        "metric": "fork_alert",
                        "label": "",
                        "width": 70
                    }
                ]
            }
        ]
    },
    "Peers_and_Database": {
        "layout": [
            {
                "row": [
                    {
                        "metric": "peer_versions",
                        "label": "Connected Nodes",
                        "width": 72
                    }
                ]
            },
            {
                "row": [
                    {
                        "metric": "blockchain_size",
                        "label": "Blockchain database total consumed",
                        "width": 72
                    }
                ]
            }
        ]
    },
    "Wallet": {
        "layout": [
            {
                "row": [
                    {
                        "metric": "wallet_balance",
                        "label": "Balance",
                        "width": 32
                    },
                    {
                        "metric": "wallet_status",
                        "label": "Status",
                        "width": 32
                    }
                ]
            },
            {
                "row": [
                    {
                        "metric": "unconfirmed_balance",
                        "label": "Unconfirmed Balance",
                        "width": 32
                    },
                    {
                        "metric": "highest_balance_address",
                        "label": "Address",
                        "width": 43
                    }
                ]
            }
        ]
    },
    "Staking": {
        "layout": [
            {
                "row": [
                    {
                        "metric": "staking_status",
                        "label": "Status",
                        "width": 32
                    },
                    {
                        "metric": "staking_info",
                        "label": "Weight Ratio",
                        "width": 40
                    }
                ]
            },
            {
                "row": [
                    {
                        "metric": "last_stake_reward",
                        "label": "Last Reward",
                        "width": 32
                    },
                    {
                        "metric": "expected_time",
                        "label": "Expected Time",
                        "width": 32
                    }
                ]
            },
            {
                "row": [
                    {
                        "metric": "stake_report",
                        "label": "Stake Report",
                        "width": 60
                    }
                ]
            },
            {
                "row": [
                    {
                        "metric": "stake_wins",
                        "label": "Stake Wins",
                        "width": 32
                    }
                ]
            }
        ]
    },
    "System_Resources": {
        "layout": [
            {
                "row": [
                    {
                        "metric": "disk_usage",
                        "label": "Disk",
                        "width": 32
                    },
                    {
                        "metric": "cpu_usage",
                        "label": "CPU",
                        "width": 25
                    }
                ]
            },
            {
                "row": [
                    {
                        "metric": "memory_usage",
                        "label": "RAM",
                        "width": 48
                    },
                    {
                        "metric": "swap_memory",
                        "label": "Swap",
                        "width": 32
                    }
                ]
            },
            {
                "row": [
                    {
                        "metric": "system_uptime",
                        "label": "Uptime",
                        "width": 32
                    },
                    {
                        "metric": "load_averages",
                        "label": "Load Avg",
                        "width": 32
                    }
                ]
            }
        ]
    },
    "Debug_Log": {
        "file": {
            "path": f"{DATA_DIR}/debug.log",
            "lines": 5
        }
    },
    "Probe_Nodes_Log": {
        "file": {
            "path": PROBE_NODES_LOG,
            "lines": 7
        }
    }
}


# -----------------------------------------------------------------------------
# Data Cache Class
# -----------------------------------------------------------------------------

class DataCache:
    """
    Cache for pocketcoin-cli RPC data to minimize expensive node queries.

    This class implements a two-tier caching strategy:
    - Fast-changing data (blocks, network, mempool) updated every cycle
    - Slow-changing data (wallet, staking) updated every 3 cycles

    This reduces load on the node while keeping critical metrics up-to-date.
    """

    def __init__(self):
        """Initialize empty cache dictionaries for all RPC endpoints."""
        self.counter = 0  # Cycle counter for less-frequent updates

        # Updated every cycle (fast-changing data)
        self.getinfo = {}
        self.blockchain_info = {}
        self.network_info = {}
        self.mempool_info = {}

        # Updated every 3 cycles (slow-changing data)
        self.wallet_info = {}
        self.staking_info = {}
        self.stake_report = {}
        self.listaddressgroupings = []

    def update(self):
        """
        Update cached data from pocketcoin-cli.

        Uses tiered update strategy:
        - Every cycle: Node status, blockchain, network, mempool
        - Every 3rd cycle: Wallet, staking info, stake report

        This reduces RPC load while maintaining fresh data for critical metrics.
        """
        # Frequent updates (every cycle) - data that changes rapidly
        self.getinfo = self._run_cli("-getinfo")
        self.blockchain_info = self._run_cli("getblockchaininfo")
        self.network_info = self._run_cli("getnetworkinfo")
        self.mempool_info = self._run_cli("getmempoolinfo")

        # Less frequent updates (every 3 cycles) - data that changes slowly
        if self.counter % 3 == 0:
            self.wallet_info = self._run_cli("getwalletinfo")
            self.staking_info = self._run_cli("getstakinginfo")
            self.stake_report = self._run_cli("getstakereport")
            self.listaddressgroupings = self._run_cli("listaddressgroupings")

        self.counter += 1

    def _run_cli(self, command: str) -> Any:
        """
        Execute pocketcoin-cli command and return parsed JSON result.

        Args:
            command: RPC command to execute (e.g., "getblockchaininfo")

        Returns:
            Parsed JSON response as dict/list, or empty dict/list on error

        Handles:
            - Command timeouts (10 second limit)
            - JSON parsing errors
            - Non-zero exit codes
            - Empty responses
        """
        try:
            cmd = f"pocketcoin-cli {POCKETCOIN_CLI_ARGS} {command}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
            return {} if command != "listaddressgroupings" else []
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            return {} if command != "listaddressgroupings" else []


# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def format_with_commas(value: int) -> str:
    """
    Format integer with thousand separators for readability.

    Args:
        value: Integer to format (e.g., 1234567)

    Returns:
        Formatted string with commas (e.g., "1,234,567")

    Example:
        >>> format_with_commas(1000000)
        '1,000,000'
    """
    return f"{value:,}"


def format_number_with_commas(value: float) -> str:
    """
    Format decimal number with commas and exactly 8 decimal places.

    Used for cryptocurrency values which require high precision.
    Integer part gets comma separators, decimal always shows 8 digits.

    Args:
        value: Float to format (e.g., 12345.123)

    Returns:
        Formatted string (e.g., "12,345.12300000")

    Example:
        >>> format_number_with_commas(1234.5)
        '1,234.50000000'
    """
    integer_part = int(value)
    decimal_part = str(value).split('.')[1][:8] if '.' in str(value) else "00000000"
    decimal_part = decimal_part.ljust(8, '0')  # Pad to 8 decimals
    return f"{format_with_commas(integer_part)}.{decimal_part}"


def format_time_seconds(seconds: int, prefix: str = "") -> str:
    """
    Convert seconds to human-readable time format.

    Automatically selects appropriate units (days, hours, minutes, seconds)
    based on the magnitude of the input.

    Args:
        seconds: Time duration in seconds
        prefix: Optional prefix string (e.g., "~" for estimates)

    Returns:
        Human-readable time string (e.g., "5d 12h", "3h 45m", "42s")

    Examples:
        >>> format_time_seconds(172800)
        '2d 0h'
        >>> format_time_seconds(3665)
        '1h 1m'
        >>> format_time_seconds(45, "~")
        '~45s'
    """
    if seconds == 0 or seconds is None:
        return "Unknown"

    # Days and hours for long durations (>1 day)
    if seconds > 86400:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{prefix}{days}d {hours}h"
    # Hours and minutes for medium durations (1 hour - 1 day)
    elif seconds > 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{prefix}{hours}h {minutes}m"
    # Minutes only for short durations (1 minute - 1 hour)
    elif seconds > 60:
        minutes = seconds // 60
        return f"{prefix}{minutes}m"
    # Seconds for very short durations (<1 minute)
    else:
        return f"{prefix}{seconds}s"


# -----------------------------------------------------------------------------
# Metric Functions
# -----------------------------------------------------------------------------

class MetricCollector:
    """
    Collects and formats all metrics for display in the monitoring dashboard.

    This class contains all the get_* methods that are called by the UI renderer.
    Each method:
    1. Retrieves data from the DataCache (which talks to pocketcoin-cli)
    2. Processes/formats the data for display
    3. Returns a string ready for the UI

    The method naming convention is important:
    - get_node_version() corresponds to metric: "node_version" in JSON config
    - get_blockchain_blocks() corresponds to metric: "blockchain_blocks"

    Attributes:
        cache: DataCache instance providing access to RPC data
    """

    def __init__(self, cache: DataCache):
        """
        Initialize MetricCollector with a data cache reference.

        Args:
            cache: DataCache instance for accessing pocketcoin-cli data
        """
        self.cache = cache

    # -------------------------------------------------------------------------
    # Node Status Metrics
    # -------------------------------------------------------------------------

    def get_node_version(self) -> str:
        version = self.cache.getinfo.get('version', 'Unknown')
        return f"v{version}" if version != 'Unknown' else 'Unknown'

    def get_node_time(self) -> str:
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC'

    def get_node_uptime(self) -> str:
        try:
            # Use _run_cli instead of direct subprocess
            result = self.cache._run_cli("uptime")
            if isinstance(result, int):
                uptime_seconds = result
            elif isinstance(result, str) and result.isdigit():
                uptime_seconds = int(result)
            return format_time_seconds(uptime_seconds)
        except:
            pass
        return "Unknown"

    def get_sync_status(self) -> str:
        blocks = self.cache.blockchain_info.get('blocks', 0)
        headers = self.cache.blockchain_info.get('headers', 0)

        if headers == 0 or blocks == 0:
            return "Unknown"
        elif blocks < headers:
            return f"{(blocks * 100) // headers}%"
        else:
            return "100%"

    # -------------------------------------------------------------------------
    # Blockchain Metrics
    # -------------------------------------------------------------------------

    def get_blockchain_blocks(self) -> str:
        """
        Get current block height with fork health indicator.

        Queries blockchain height and analyzes chain tips to detect forks.
        Returns block number with a visual indicator:
        - ✓ (checkmark) = Healthy (0-3 recent forks)
        - ⚠ (warning) = Unhealthy (>3 recent forks)

        Fork Detection Logic:
        - Only counts forks with status 'valid-fork' (actual competing chains)
        - Ignores forks older than 100 blocks (historical orphans)
        - Threshold of 3 forks is normal for PoS; >3 may indicate issues

        Returns:
            Block height string with indicator (e.g., "3521027 ✓")

        Note:
            Calls getchaintips separately (not cached) for real-time fork detection
        """
        blocks = self.cache.blockchain_info.get('blocks', 0)

        # Query chain tips for fork detection (not cached - needs to be real-time)
        try:
            result = self._run_cli("getchaintips")
            if result.returncode == 0:
                tips = json.loads(result.stdout)

                # Count only recent valid forks to avoid false positives from old orphans
                # valid-fork = competing chain at similar height
                # Height filter prevents counting thousands of historical orphans
                recent_fork_count = sum(1 for tip in tips
                                       if tip.get('status') == 'valid-fork'
                                       and tip.get('height', 0) >= blocks - 100)

                # Visual health indicator based on fork count
                if recent_fork_count > 3:
                    return f"{blocks} ⚠"  # Warning: excessive forks
                else:
                    return f"{blocks} ✓"  # Healthy: normal fork count
        except:
            pass  # Silently fall back to plain block number on error

        return str(blocks)  # Fallback if fork detection fails

    def get_difficulty(self) -> str:
        diff = self.cache.staking_info.get('difficulty')
        if diff is not None:
            return format_number_with_commas(float(diff))
        return "Unknown"

    def get_network_hashps(self) -> str:
        try:
            result = self.cache._run_cli("getnetworkhashps")
            try:
                hashps = float(result)
            except (TypeError, ValueError):
                return "Unknown"

            if hashps > 1_000_000_000_000:
                return f"{hashps/1_000_000_000_000:.2f} TH/s"
            elif hashps > 1_000_000_000:
                return f"{hashps/1_000_000_000:.2f} GH/s"
            elif hashps > 1_000_000:
                return f"{hashps/1_000_000:.2f} MH/s"
            elif hashps > 1_000:
                return f"{hashps/1_000:.2f} KH/s"
            else:
                return f"{hashps:.2f} H/s"
        except Exception:
            pass
        return "Unknown"

    def get_mempool_info(self) -> str:
        size_info = self.cache.mempool_info.get('size', {})
        tx_count = size_info.get('memory', 0) if isinstance(size_info, dict) else 0
        sqlite_count = size_info.get('sqlite', 0) if isinstance(size_info, dict) else 0
        bytes_count = self.cache.mempool_info.get('bytes', 0)

        mb = bytes_count / 1048576
        combined_count = tx_count + sqlite_count
        return f"{combined_count} txs ({mb:.1f} MB)"

    def get_net_stake_weight(self) -> str:
        netweight = self.cache.staking_info.get('netstakeweight', 0)
        if netweight > 0:
            coins = netweight / 100000000
            return format_number_with_commas(coins)
        return "Unknown"

    def get_fork_alert(self) -> str:
        """Alert when fork count exceeds threshold"""
        try:
            # Get current height
            blocks = self.cache.blockchain_info.get('blocks', 0)

            result = self._run_cli("getchaintips")
            if result.returncode == 0:
                tips = json.loads(result.stdout)
                # Only count recent valid forks (within 100 blocks of current height)
                recent_fork_count = sum(1 for tip in tips
                                       if tip.get('status') == 'valid-fork'
                                       and tip.get('height', 0) >= blocks - 100)

                if recent_fork_count > 3:
                    return f"⚠ Fork Alert: {recent_fork_count} recent competing chains detected!"
                else:
                    return ""  # Return empty string when no alert needed
        except:
            pass
        return ""

    # -------------------------------------------------------------------------
    # Peers and Database Metrics
    # -------------------------------------------------------------------------

    def get_peer_versions(self) -> str:
        """
        Generate multi-line histogram of connected peer versions.

        Queries all connected peers, parses version strings, and generates
        a visual histogram showing version distribution.

        Output Format:
            Line 1: "86 total (In:76/Out:10)"
            Lines 2-4: "  v0.22.19  82 (95%) ##############################"

        Features:
        - Shows top 3 versions only (to save screen space)
        - Histogram bars scale with peer percentage
        - Unknown/empty versions labeled as "Unknown"
        - Handles peer version string variations (/Pocketcoin: or /Satoshi:)

        Returns:
            Multi-line string with peer statistics and histogram
            Lines joined with \\n for UIRenderer to parse

        Example:
            "87 total (In:77/Out:10)\\n  v0.22.19  85 (98%) ###############"
        """
        try:
            # Use _run_cli instead of direct subprocess
            peer_info = self.cache._run_cli("getpeerinfo")
            if not peer_info or 'error' in peer_info:
                return "No peers connected"

            total_peers = len(peer_info)

            if total_peers == 0:
                return "No peers connected"

            # Get connection details from cached network info
            inbound = self.cache.network_info.get('connections_in', 0)
            outbound = self.cache.network_info.get('connections_out', 0)

            # Parse and count peer versions
            versions = {}
            for peer in peer_info:
                subver = peer.get('subver', '')
                # Clean up version string (handle /Pocketcoin:0.22.19/ or /Satoshi:0.22.19/)
                version = subver.replace('/Pocketcoin:', '').replace('/Satoshi:', '').replace('/', '').strip()
                # Label empty/malformed versions
                if not version:
                    version = 'Unknown'
                versions[version] = versions.get(version, 0) + 1

            # Sort by count (most common first)
            sorted_versions = sorted(versions.items(), key=lambda x: x[1], reverse=True)

            # Build multi-line output
            lines = [f"{total_peers} total (In:{inbound}/Out:{outbound})"]

            # Generate histogram for top 3 versions
            max_bars = 30  # Maximum bar length in characters
            for i, (version, count) in enumerate(sorted_versions[:3]):  # Cap at 3 versions
                percentage = (count * 100) // total_peers
                # Scale bar length based on percentage
                bars = (count * max_bars) // total_peers
                bars = max(1, bars) if count > 0 else 0  # Minimum 1 bar if count > 0
                bar = '#' * bars
                # Format: "  v0.22.19  85 (95%) ##############################"
                lines.append(f"  v{version:<7} {count:3d} ({percentage:2d}%) {bar}")

            return '\n'.join(lines)
        except:
            return "Error fetching peers"

    def get_blockchain_size(self) -> str:
        """Calculate total blockchain database size"""
        blockchain_dir = DATA_DIR
        if not os.path.isdir(blockchain_dir):
            return "Directory not found"
        try:
            # Get sizes in KB for all four components
            def get_dir_size_kb(path):
                result = subprocess.run(f"du -sk {path}", shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    return int(result.stdout.split()[0])
                return 0

            blocks_size = get_dir_size_kb(f"{blockchain_dir}/blocks")
            chainstate_size = get_dir_size_kb(f"{blockchain_dir}/chainstate")
            indexes_size = get_dir_size_kb(f"{blockchain_dir}/indexes")
            pocketdb_size = get_dir_size_kb(f"{blockchain_dir}/pocketdb")

            total_kb = blocks_size + chainstate_size + indexes_size + pocketdb_size

            # Convert to human-readable
            if total_kb >= 1073741824:
                return f"{total_kb/1073741824:.1f}T"
            elif total_kb >= 1048576:
                return f"{total_kb/1048576:.0f}G"
            elif total_kb >= 1024:
                return f"{total_kb/1024:.1f}M"
            else:
                return f"{total_kb}K"
        except:
            return "Error"

    # Wallet Metrics

    def get_wallet_balance(self) -> str:
        sql_balance = self.cache.wallet_info.get('sql_balance', 0)
        return format_number_with_commas(float(sql_balance))

    def get_unconfirmed_balance(self) -> str:
        return str(self.cache.wallet_info.get('unconfirmed_balance', 0))

    def get_wallet_status(self) -> str:
        if 'unlocked_until' in self.cache.wallet_info:
            unlock_time = self.cache.wallet_info['unlocked_until']
            if unlock_time == 0:
                return "Locked"
            else:
                current_time = int(time.time())
                if unlock_time > current_time:
                    mins = (unlock_time - current_time) // 60
                    return f"Unlocked ({mins} min)"
                else:
                    return "Unlock expired"
        return "Unencrypted"

    def get_highest_balance_address(self) -> str:
        try:
            if isinstance(self.cache.listaddressgroupings, list) and len(self.cache.listaddressgroupings) > 0:
                addresses = []
                for group in self.cache.listaddressgroupings[0]:
                    if len(group) >= 2 and group[1] is not None:
                        addresses.append((group[0], group[1]))

                if addresses:
                    highest = max(addresses, key=lambda x: x[1])
                    return highest[0]
        except:
            pass
        return "Unknown"

    # Staking Metrics

    def get_staking_status(self) -> str:
        status = self.cache.staking_info.get('staking', False)
        return "TRUE" if status else "FALSE"

    def get_staking_info(self) -> str:
        weight = self.cache.staking_info.get('weight', 0)
        netweight = self.cache.staking_info.get('netstakeweight', 0)

        coins_weight = weight // 100000000
        coins_netweight = netweight // 100000000

        formatted_weight = format_with_commas(coins_weight)
        formatted_netweight = format_with_commas(coins_netweight)

        percentage = (weight * 100) // netweight if netweight > 0 else 0

        return f"{formatted_weight}/{formatted_netweight} ({percentage}%)"

    def get_expected_time(self) -> str:
        expected_seconds = self.cache.staking_info.get('expectedtime', 0)
        return format_time_seconds(expected_seconds, "~")

    def get_last_stake_reward(self) -> str:
        """Calculate time since last stake reward"""
        latest_time_str = self.cache.stake_report.get('Latest Time')

        if not latest_time_str or latest_time_str == "0":
            return "Never"

        try:
            # Parse ISO format timestamp
            from datetime import datetime, timezone
            latest_time = datetime.fromisoformat(latest_time_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            diff_seconds = int((now - latest_time).total_seconds())
            return format_time_seconds(diff_seconds)
        except:
            return "Unknown"

    def get_stake_report(self) -> str:
        report = self.cache.stake_report

        last_24h = report.get('Last 24H')
        last_7d = report.get('Last 7 Days')
        last_30d = report.get('Last 30 Days')
        last_365d = report.get('Last 365 Days')

        parts = []
        # Values come as strings, need to convert to float
        try:
            if last_24h is not None:
                parts.append(f"1D: {float(last_24h):.2f}")
            if last_7d is not None:
                parts.append(f"7D: {float(last_7d):.2f}")
            if last_30d is not None:
                parts.append(f"30D: {float(last_30d):.2f}")
            if last_365d is not None:
                parts.append(f"1Y: {float(last_365d):.2f}")
        except (ValueError, TypeError):
            return "Error parsing data"

        return " | ".join(parts) if parts else "No data"

    def get_stake_wins(self) -> str:
        wins = self.cache.stake_report.get('Stake counted')
        if wins is not None:
            return format_with_commas(int(wins))
        return "Unknown"

    # System Resource Metrics

    def get_disk_usage(self) -> str:
        blockchain_dir = DATA_DIR
        try:
            result = subprocess.run(f"df -h {blockchain_dir}", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 5:
                        used = parts[2]
                        total = parts[1]
                        percent = parts[4]
                        return f"{used}/{total} ({percent})"
        except:
            pass
        return "Unknown"

    def get_cpu_usage(self) -> str:
        try:
            result = subprocess.run("top -bn1 | grep 'Cpu(s)'", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                # Parse: %Cpu(s):  0.5 us,  0.3 sy,  0.0 ni, 99.2 id, ...
                line = result.stdout.strip()
                parts = line.split(',')
                us = float(parts[0].split(':')[1].strip().split()[0])
                sy = float(parts[1].strip().split()[0])
                usage = us + sy
                return f"{usage:.2f}%"
        except:
            pass
        return "Unknown"

    def get_memory_usage(self) -> str:
        try:
            result = subprocess.run("free -h", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 4:
                        total = parts[1]
                        used = parts[2]
                        free = parts[3]
                        return f"Total: {total}, Used: {used}, Free: {free}"
        except:
            pass
        return "Unknown"

    def get_swap_memory(self) -> str:
        try:
            result = subprocess.run("free -h", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 3:
                    parts = lines[2].split()
                    if len(parts) >= 3:
                        total = parts[1]
                        used = parts[2]
                        return f"{used}/{total}"
        except:
            pass
        return "Unknown"

    def get_system_uptime(self) -> str:
        try:
            result = subprocess.run("uptime", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                # Parse uptime output
                output = result.stdout.strip()
                if 'up' in output:
                    parts = output.split('up')[1].split(',')
                    uptime = ','.join(parts[:2]).strip()
                    return uptime
        except:
            pass
        return "Unknown"

    def get_load_averages(self) -> str:
        try:
            result = subprocess.run("uptime", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                output = result.stdout.strip()
                if 'load average:' in output:
                    return output.split('load average:')[1].strip()
        except:
            pass
        return "Unknown"


# -----------------------------------------------------------------------------
# UI Renderer
# -----------------------------------------------------------------------------

class UIRenderer:
    """
    Handles curses-based UI rendering for flicker-free terminal display.

    This class implements the presentation layer using Python's curses library,
    providing smooth, professional terminal UI similar to htop or vim.

    Key Features:
    - Double-buffered rendering (no flicker)
    - Hidden cursor during updates
    - Adapts to terminal's color scheme
    - Supports boxed (bordered) and compact modes
    - Handles multi-line metrics
    - Truncates output to fit screen width
    - Gracefully handles screen overflow

    Attributes:
        stdscr: Curses screen object for rendering
        ui_sections: Dictionary defining UI layout from JSON config
        metrics: MetricCollector instance for retrieving data
        use_boxed: Boolean - True for bordered boxes, False for compact
    """

    def __init__(self, stdscr, ui_sections: Dict, metrics: MetricCollector, use_boxed: bool = True):
        """
        Initialize UIRenderer with curses screen and configuration.

        Args:
            stdscr: Curses screen object (created by curses.wrapper)
            ui_sections: UI layout configuration dictionary
            metrics: MetricCollector for fetching metric values
            use_boxed: Display mode - True for boxed, False for compact
        """
        self.stdscr = stdscr
        self.ui_sections = ui_sections
        self.metrics = metrics
        self.use_boxed = use_boxed

        # Configure curses for optimal display
        curses.curs_set(0)  # Hide cursor - cleaner appearance during updates

        # Adapt to terminal's color scheme instead of forcing black background
        # -1 means "use terminal default" for background color
        if curses.has_colors():
            curses.use_default_colors()  # Respect user's terminal colors
            curses.init_pair(1, curses.COLOR_CYAN, -1)    # For future use
            curses.init_pair(2, curses.COLOR_GREEN, -1)   # For future use
            curses.init_pair(3, curses.COLOR_YELLOW, -1)  # For future use

    def render(self):
        """
        Main render loop - draws entire UI to screen.

        Process:
        1. Clears screen
        2. Iterates through all UI sections
        3. Renders each section (boxed or compact mode)
        4. Draws lines to screen row by row
        5. Refreshes screen (curses double-buffer swap)

        Handles screen overflow gracefully by catching curses.error
        when bottom of screen is reached.
        """
        self.stdscr.clear()  # Clear previous frame

        current_row = 0

        # Render each section defined in UI configuration
        for section_name in self.ui_sections.keys():
            # Choose rendering mode based on configuration
            if self.use_boxed:
                section_lines = self.render_section(section_name)
            else:
                section_lines = self.render_section_compact(section_name)

            # Draw each line to screen
            for line in section_lines:
                try:
                    # Truncate to screen width - 1 to avoid edge wrapping issues
                    self.stdscr.addstr(current_row, 0, line[:curses.COLS-1])
                    current_row += 1
                except curses.error:
                    # Reached bottom of screen - silently stop rendering
                    pass

        # Swap buffers - makes all changes visible at once (no flicker)
        self.stdscr.refresh()

    def render_section(self, section_name: str) -> List[str]:
        """Render a single section and return lines"""
        section = self.ui_sections.get(section_name)
        if not section:
            return []

        if 'layout' in section:
            return self.render_layout_section(section_name, section['layout'])
        elif 'file' in section:
            return self.render_file_section(section_name, section['file'])

        return []

    def render_layout_section(self, section_name: str, layout: List) -> List[str]:
        """Render a layout-based section"""
        content_lines = []

        for row in layout:
            metrics = row.get('row', [])

            # Check if single metric (might be multi-line)
            if len(metrics) == 1:
                metric = metrics[0]
                key = metric['metric']
                label = metric.get('label', key)
                width = metric['width']

                # Get metric value
                value = self.get_metric_value(key)

                # Skip empty values (for conditional metrics like fork_alert)
                if not value or value.strip() == "":
                    continue

                # Check if multi-line
                if '\n' in value:
                    lines = value.split('\n')
                    # First line gets label
                    content_lines.append(self.format_label_value(label, lines[0], width))
                    # Subsequent lines without label
                    for line in lines[1:]:
                        content_lines.append(line)
                else:
                    content_lines.append(self.format_label_value(label, value, width))
            else:
                # Multiple metrics on one row
                row_content = ""
                for metric in metrics:
                    key = metric['metric']
                    label = metric.get('label', key)
                    width = metric['width']
                    value = self.get_metric_value(key)
                    row_content += self.format_label_value(label, value, width)
                content_lines.append(row_content)

        return self.create_boxed_section(section_name, content_lines)

    def render_file_section(self, section_name: str, file_config: Dict) -> List[str]:
        """Render a file-based section"""
        file_path = file_config['path']
        lines_count = file_config['lines']

        content_lines = self.display_file_content(file_path, lines_count)
        return self.create_boxed_section(section_name, content_lines)

    def get_metric_value(self, metric_name: str) -> str:
        """Get value for a metric"""
        method_name = f"get_{metric_name}"
        if hasattr(self.metrics, method_name):
            try:
                return str(getattr(self.metrics, method_name)())
            except Exception as e:
                return f"Error: {e}"
        return "N/A"

    def format_label_value(self, label: str, value: str, width: int) -> str:
        """Format label:value pair with width enforcement"""
        pair = f"{label}: {value}"
        if len(pair) > width:
            return pair[:width]
        else:
            return pair.ljust(width)

    def create_boxed_section(self, title: str, content: List[str]) -> List[str]:
        """Create a boxed section with title and content"""
        if not content:
            return []

        # Calculate max content width
        max_content_width = max(len(line) for line in content)

        internal_width = max_content_width + 2

        # Top border with title
        title_part = f"─ {title} "
        remaining_dashes = internal_width - len(title_part)
        top_border = f"┌{title_part}{'─' * remaining_dashes}┐"

        # Content lines
        boxed_lines = [top_border]
        for line in content:
            boxed_lines.append(f"│ {line.ljust(max_content_width)} │")

        # Bottom border
        bottom_border = f"└{'─' * internal_width}┘"
        boxed_lines.append(bottom_border)

        return boxed_lines

    def display_file_content(self, file_path: str, lines: int) -> List[str]:
        """Display content from a file"""
        try:
            if os.path.isfile(file_path):
                result = subprocess.run(f"tail -n {lines} {file_path}",
                                        shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')
                else:
                    return [f"Error reading file: {file_path}"]
            else:
                return [f"File not found: {file_path}"]
        except Exception as e:
            return [f"Error: {e}"]

    def render_section_compact(self, section_name: str) -> List[str]:
        """Render a section in compact mode (no boxes)"""
        section = self.ui_sections.get(section_name)
        if not section:
            return []

        output_lines = [f"-- {section_name} --"]

        if 'layout' in section:
            for row in section['layout']:
                metrics = row.get('row', [])

                if len(metrics) == 1:
                    # Single metric (might be multi-line)
                    metric = metrics[0]
                    key = metric['metric']
                    label = metric.get('label', key)
                    value = self.get_metric_value(key)

                    if '\n' in value:
                        lines = value.split('\n')
                        output_lines.append(f"{label}: {lines[0]}")
                        for line in lines[1:]:
                            output_lines.append(line)
                    else:
                        output_lines.append(f"{label}: {value}")
                else:
                    # Multiple metrics on one row
                    row_parts = []
                    for metric in metrics:
                        key = metric['metric']
                        label = metric.get('label', key)
                        value = self.get_metric_value(key)
                        row_parts.append(f"{label}: {value}")
                    output_lines.append("  ".join(row_parts))

        elif 'file' in section:
            file_path = section['file']['path']
            lines_count = section['file']['lines']
            content_lines = self.display_file_content(file_path, lines_count)
            output_lines.extend(content_lines)

        output_lines.append("")  # Blank line between sections
        return output_lines


# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------

def main(stdscr, use_boxed: bool, refresh_seconds: int):
    """
    Main application loop - the heart of Pocketnet Watch.

    Initializes all components and runs the continuous monitoring loop:
    1. Creates DataCache for RPC data
    2. Creates MetricCollector to process data
    3. Creates UIRenderer for display
    4. Loops forever: update data → render UI → sleep → repeat

    Args:
        stdscr: Curses screen object (provided by curses.wrapper)
        use_boxed: True for boxed UI, False for compact mode
        refresh_seconds: Time to sleep between updates

    Loop runs indefinitely until:
    - User presses Ctrl+C (KeyboardInterrupt)
    - Terminal is closed
    - Process is killed
    """
    # Initialize the three core components
    cache = DataCache()  # Handles pocketcoin-cli RPC calls
    metrics = MetricCollector(cache)  # Processes data into displayable metrics
    renderer = UIRenderer(stdscr, DEFAULT_UI_SECTIONS, metrics, use_boxed)  # Renders to screen

    # Infinite monitoring loop
    while True:
        # Fetch fresh data from pocketcoin-cli (uses tiered caching strategy)
        cache.update()

        # Render updated UI to screen (flicker-free with curses)
        renderer.render()

        # Sleep before next update (reduces CPU and node load)
        time.sleep(refresh_seconds)

def test_connection():
    """Test function to check pocketcoin-cli connection with config settings"""

    print("Testing pocketcoin-cli connection...")
    print(f"Config file: {CONFIG_FILE}")
    print(f"Using CLI args: '{POCKETCOIN_CLI_ARGS}'")
    print("-" * 60)

    class TempCache:
        def _run_cli(self, command: str) -> Any:
            try:
                cmd = f"pocketcoin-cli {POCKETCOIN_CLI_ARGS} {command}"
                print(f"Running command: {cmd}")

                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                print(f"Return code: {result.returncode}")

                if result.stdout:
                    print(f"STDOUT length: {len(result.stdout)} characters")
                if result.stderr:
                    print(f"STDERR: {result.stderr.strip()}")

                if result.returncode == 0 and result.stdout.strip():
                    try:
                        data = json.loads(result.stdout)
                        print("\n✅ SUCCESS: pocketcoin-cli is responding correctly!")
                        print(f"Block height : {data.get('blocks', 'Unknown')}")
                        print(f"Headers      : {data.get('headers', 'Unknown')}")
                        print(f"Chain        : {data.get('chain', 'Unknown')}")
                        print(f"Verification : {data.get('verificationprogress', 0):.4f}")
                        return data
                    except json.JSONDecodeError:
                        print("❌ Could not parse JSON response")
                        return None
                else:
                    print("❌ Command failed or returned no output")
                    return None

            except Exception as e:
                print(f"❌ EXCEPTION: {e}")
                return None

    # Run the test
    print("\nExecuting test query...")
    cache = TempCache()
    cache._run_cli("getblockchaininfo")

if __name__ == "__main__":
    """
    Entry point - parses command-line arguments and starts the application.

    Command-line Arguments:
        -c, --compact: Use compact mode (no boxes)
        -b, --boxed: Use boxed mode with borders (default)
        -r, --refresh N: Update every N seconds (default: 5)
        -t, --test-connection: Test the pocketcoin-cli connection and exit

    Example Usage:
        ./watch.py                    # Default: boxed mode, 5s refresh
        ./watch.py -c -r 3            # Compact mode, 3s refresh
        ./watch.py --boxed -r 10      # Boxed mode, 10s refresh
        ./watch.py --test-connection  # Test connection with pocketcoin-cli

    Press Ctrl+C to exit gracefully.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Pocketnet Watch - Real-time monitoring for Pocketnet nodes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Press Ctrl+C to exit. See docs/DOCUMENTATION.md for details.'
    )
    parser.add_argument('-c', '--compact', action='store_true',
                        help='Use compact UI without borders')
    parser.add_argument('-b', '--boxed', action='store_true',
                        help='Use boxed UI with borders (default)')
    parser.add_argument('-r', '--refresh', type=int, default=REFRESH_SECONDS,
                        help=f'Refresh interval in seconds (default: {REFRESH_SECONDS})')
    parser.add_argument('-t', '--test-connection',
                        action='store_true',
                        dest='test_connection',
                        help='Test the pocketcoin-cli connection and exit')

    args = parser.parse_args()

    # Handle test connection early
    if args.test_connection:
        test_connection()
        sys.exit(0)

    # Determine UI mode from arguments (compact takes precedence)
    use_boxed = not args.compact if args.compact else USE_BOXED_UI
    refresh_seconds = args.refresh

    # Start the application with curses wrapper
    # curses.wrapper handles initialization and cleanup automatically
    try:
        curses.wrapper(lambda stdscr: main(stdscr, use_boxed, refresh_seconds))
    except KeyboardInterrupt:
        # Graceful exit on Ctrl+C (curses.wrapper handles terminal cleanup)
        pass
