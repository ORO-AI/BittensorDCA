#!/usr/bin/env python3
"""
Simple cron-based DCA staking for Bittensor subnets.

Run via cron to stake a fixed amount at regular intervals.
Exits after a single stake operation (or graceful skip if conditions not met).

Usage:
    python dca_stake.py                    # Use default config.yaml
    python dca_stake.py --config my.yaml   # Use custom config file
    python dca_stake.py --dry-run          # Preview without staking

Exit codes:
    0 = Success OR graceful skip (insufficient liquidity/high slippage)
    1 = Error (config, network, wallet, transaction failure)
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple

import yaml
import bittensor as bt
from tenacity import retry, stop_after_attempt, wait_exponential

# ============ CONFIGURATION ============

@dataclass
class Config:
    """Configuration for DCA staking."""
    wallet_name: str
    validator_hotkey: str
    stake_amount: float
    target_netuid: Optional[int]
    whitelist: List[int]
    min_liquidity_ratio: float
    network: str
    log_file: str
    dry_run: bool


def load_config(config_path: str = "config.yaml") -> Config:
    """Load and validate configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    # Required fields
    if "wallet_name" not in data:
        raise ValueError("Config missing required field: wallet_name")
    if "validator_hotkey" not in data:
        raise ValueError("Config missing required field: validator_hotkey")
    if "stake_amount" not in data:
        raise ValueError("Config missing required field: stake_amount")

    return Config(
        wallet_name=data["wallet_name"],
        validator_hotkey=data["validator_hotkey"],
        stake_amount=float(data["stake_amount"]),
        target_netuid=data.get("target_netuid"),
        whitelist=data.get("whitelist", []),
        min_liquidity_ratio=float(data.get("min_liquidity_ratio", 10.0)),
        network=data.get("network", "finney"),
        log_file=data.get("log_file", "logs/dca.log"),
        dry_run=data.get("dry_run", False),
    )


# ============ LOGGING ============

def setup_logging(log_file: str) -> logging.Logger:
    """Configure dual file/stdout logging."""
    # Create logs directory if needed
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Format: timestamp, level, message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler (append mode)
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(formatter)

    # Stdout handler (for cron MAILTO)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    logger = logging.getLogger("dca_stake")
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    return logger


# ============ BITTENSOR CONNECTION ============

FALLBACK_NETWORKS = ["finney", "subvortex", "archive"]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def connect_with_retry(network: str) -> bt.AsyncSubtensor:
    """Connect to Bittensor network with retry logic."""
    sub = bt.AsyncSubtensor(network=network)
    # Test connection
    await sub.get_current_block()
    return sub


async def connect_to_bittensor(primary_network: str, log: logging.Logger) -> bt.AsyncSubtensor:
    """Connect to Bittensor, falling back to other networks if needed."""
    # Try primary network first
    networks_to_try = [primary_network] + [n for n in FALLBACK_NETWORKS if n != primary_network]

    last_error = None
    for network in networks_to_try:
        try:
            log.info(f"Connecting to {network}...")
            sub = await connect_with_retry(network)
            log.info(f"Connected to {network}")
            return sub
        except Exception as e:
            log.warning(f"Failed to connect to {network}: {e}")
            last_error = e
            continue

    raise ConnectionError(f"Failed to connect to any network. Last error: {last_error}")


# ============ WALLET ============

def get_wallet_password() -> str:
    """Get wallet password from environment variable or file."""
    # Try environment variable first
    password = os.environ.get("WALLET_PASSWORD")
    if password:
        return password

    # Try password file
    password_file = Path.home() / ".bittensor" / ".wallet_password"
    if password_file.exists():
        return password_file.read_text().strip()

    raise ValueError(
        "Wallet password not found. Either:\n"
        "  1. Set WALLET_PASSWORD environment variable, or\n"
        "  2. Create ~/.bittensor/.wallet_password file"
    )


def unlock_wallet(wallet_name: str, log: logging.Logger) -> bt.Wallet:
    """Unlock wallet using password."""
    password = get_wallet_password()
    wallet = bt.Wallet(name=wallet_name)
    wallet.coldkey_file.save_password_to_env(password)
    wallet.unlock_coldkey()
    log.info(f"Wallet '{wallet_name}' unlocked")
    return wallet


# ============ SUBNET HELPERS ============

async def get_subnet_by_netuid(subtensor: bt.AsyncSubtensor, netuid: int):
    """Get subnet info by netuid."""
    subnets = await subtensor.all_subnets()
    for s in subnets:
        if s.netuid == netuid:
            return s
    return None


async def select_best_from_whitelist(
    subtensor: bt.AsyncSubtensor,
    whitelist: List[int],
    stake_amount: float,
    min_liquidity_ratio: float,
    log: logging.Logger
) -> Tuple[Optional[object], Optional[str]]:
    """Select best subnet from whitelist based on score (emission/price)."""
    subnets = await subtensor.all_subnets()

    best_subnet = None
    best_score = 0.0

    for s in subnets:
        if s.netuid not in whitelist:
            continue

        # Check price
        try:
            price = float(s.price)
        except Exception:
            log.debug(f"Subnet {s.netuid}: Invalid price")
            continue

        if price <= 0:
            log.debug(f"Subnet {s.netuid}: Zero or negative price")
            continue

        # Check liquidity
        try:
            tao_in_pool = float(s.tao_in)
        except (AttributeError, TypeError):
            log.debug(f"Subnet {s.netuid}: Unable to get liquidity")
            continue

        if tao_in_pool < stake_amount * min_liquidity_ratio:
            log.debug(f"Subnet {s.netuid}: Insufficient liquidity ({tao_in_pool:.2f} TAO)")
            continue

        # Calculate score
        try:
            score = float(s.tao_in_emission) / price
        except Exception:
            score = 0.0

        if score > best_score:
            best_score = score
            best_subnet = s

    if best_subnet:
        return best_subnet, None
    return None, "No eligible subnets in whitelist"


# ============ VALIDATION ============

def check_liquidity(
    subnet,
    stake_amount: float,
    min_ratio: float
) -> Tuple[bool, float, str]:
    """Check if pool has sufficient liquidity."""
    try:
        tao_in_pool = float(subnet.tao_in)
    except (AttributeError, TypeError):
        return False, 0.0, "Unable to determine pool liquidity"

    if tao_in_pool <= 0:
        return False, tao_in_pool, "Pool has zero liquidity"

    required = stake_amount * min_ratio
    if tao_in_pool < required:
        return False, tao_in_pool, f"Pool: {tao_in_pool:.2f} TAO < {required:.2f} TAO required"

    return True, tao_in_pool, "OK"


# ============ STAKING ============

async def execute_stake(
    subtensor: bt.AsyncSubtensor,
    wallet: bt.Wallet,
    validator_hotkey: str,
    netuid: int,
    amount: float,
    log: logging.Logger
) -> bool:
    """Execute the stake transaction."""
    log.info(f"Executing stake: {amount} TAO to subnet {netuid}...")

    result = await subtensor.add_stake(
        wallet=wallet,
        hotkey_ss58=validator_hotkey,
        netuid=netuid,
        amount=bt.Balance.from_tao(amount),
        wait_for_inclusion=True,
        wait_for_finalization=False
    )

    return result


# ============ MAIN ============

async def run(config: Config, log: logging.Logger) -> int:
    """Main execution logic. Returns exit code."""

    # Connect to Bittensor
    try:
        subtensor = await connect_to_bittensor(config.network, log)
    except ConnectionError as e:
        log.error(f"Connection failed: {e}")
        return 1

    try:
        # Unlock wallet
        try:
            wallet = unlock_wallet(config.wallet_name, log)
        except Exception as e:
            log.error(f"Wallet unlock failed: {e}")
            return 1

        # Check wallet balance
        try:
            balance = float(await subtensor.get_balance(wallet.coldkey.ss58_address))
            if balance < config.stake_amount + 0.01:  # +0.01 for fees
                log.error(f"Insufficient balance: {balance:.4f} TAO (need {config.stake_amount + 0.01:.4f})")
                return 1
            log.info(f"Wallet balance: {balance:.4f} TAO")
        except Exception as e:
            log.error(f"Failed to check balance: {e}")
            return 1

        # Get target subnet
        subnet = None
        if config.target_netuid is not None:
            # Single subnet mode
            log.info(f"Target subnet: {config.target_netuid}")
            subnet = await get_subnet_by_netuid(subtensor, config.target_netuid)
            if not subnet:
                log.error(f"Subnet {config.target_netuid} not found")
                return 1
        elif config.whitelist:
            # Whitelist mode - select best
            log.info(f"Selecting best from whitelist: {config.whitelist}")
            subnet, error = await select_best_from_whitelist(
                subtensor,
                config.whitelist,
                config.stake_amount,
                config.min_liquidity_ratio,
                log
            )
            if not subnet:
                log.warning(f"No eligible subnets: {error}")
                return 0  # Graceful exit
        else:
            log.error("No target_netuid or whitelist specified in config")
            return 1

        # Log subnet info
        try:
            price = float(subnet.price)
            log.info(f"Subnet {subnet.netuid} ({subnet.subnet_name}): Price = {price:.6f} TAO")
        except Exception:
            log.error("Invalid subnet price data")
            return 1

        # Check liquidity
        liquidity_ok, tao_in_pool, liquidity_msg = check_liquidity(
            subnet, config.stake_amount, config.min_liquidity_ratio
        )
        log.info(f"Liquidity check: {liquidity_msg}")
        if not liquidity_ok:
            log.warning("Skipping stake due to insufficient liquidity")
            return 0  # Graceful exit

        # Execute stake (or dry run)
        if config.dry_run:
            log.info(f"DRY RUN: Would stake {config.stake_amount} TAO to subnet {subnet.netuid}")
            return 0

        try:
            success = await execute_stake(
                subtensor,
                wallet,
                config.validator_hotkey,
                subnet.netuid,
                config.stake_amount,
                log
            )
            if success:
                log.info(f"SUCCESS: Staked {config.stake_amount} TAO to subnet {subnet.netuid} ({subnet.subnet_name})")
                return 0
            else:
                log.error("Stake transaction returned failure")
                return 1
        except Exception as e:
            log.error(f"Stake failed: {e}")
            return 1

    finally:
        await subtensor.close()


def main() -> int:
    """Entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Simple cron-based DCA staking for Bittensor subnets"
    )
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to config file (default: config.yaml)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview what would happen without actually staking"
    )
    args = parser.parse_args()

    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"ERROR: Failed to load config: {e}", file=sys.stderr)
        return 1

    # Override dry_run from CLI if specified
    if args.dry_run:
        config.dry_run = True

    # Setup logging
    log = setup_logging(config.log_file)
    log.info("=" * 50)
    log.info("Starting DCA stake run")
    if config.dry_run:
        log.info("DRY RUN MODE - no actual staking")

    # Run async main
    import asyncio
    exit_code = asyncio.run(run(config, log))

    log.info(f"Finished with exit code {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
