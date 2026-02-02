# Bittensor DCA Stake

Simple cron-based Dollar Cost Averaging (DCA) for Bittensor subnet staking.

Run via cron to automatically stake TAO at regular intervals with built-in liquidity protection.

## Features

- **Simple**: Single script, runs once and exits
- **Cron-friendly**: Schedule with standard cron jobs
- **Safe**: Liquidity checks before staking
- **Flexible**: Single subnet or whitelist mode

## Quick Start

### 1. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

Edit `config.yaml`:

```yaml
wallet_name: "your-wallet"
validator_hotkey: "5F4tQyWrhfGVcNhoqeiNsR6KjD4wMZ2kfhLj4oHYuyHbZAc3"
stake_amount: 0.1
target_netuid: 15                # Your target subnet
min_liquidity_ratio: 10.0        # Pool must have 10x stake amount
```

### 3. Set Wallet Password

```bash
export WALLET_PASSWORD="your-password"
```

Or create a password file:
```bash
echo "your-password" > ~/.bittensor/.wallet_password
chmod 600 ~/.bittensor/.wallet_password
```

### 4. Test (Dry Run)

```bash
python dca_stake.py --dry-run
```

### 5. Run

```bash
python dca_stake.py
```

---

## Cron Setup

Edit crontab:
```bash
crontab -e
```

Add your schedule:

```bash
# Set password (required)
WALLET_PASSWORD=your-password-here

# === Example Schedules ===

# Every 6 hours (recommended for moderate DCA)
0 */6 * * * cd /path/to/DCABot && .venv/bin/python dca_stake.py

# Daily at 2:00 AM UTC
0 2 * * * cd /path/to/DCABot && .venv/bin/python dca_stake.py

# Hourly (aggressive DCA)
0 * * * * cd /path/to/DCABot && .venv/bin/python dca_stake.py

# Every 4 hours
0 */4 * * * cd /path/to/DCABot && .venv/bin/python dca_stake.py
```

---

## Configuration Reference

| Option | Default | Description |
|--------|---------|-------------|
| `wallet_name` | required | Bittensor wallet name |
| `validator_hotkey` | required | Validator hotkey SS58 address |
| `stake_amount` | required | TAO amount per stake |
| `target_netuid` | null | Single subnet to stake into |
| `whitelist` | [] | List of subnets (picks best scoring) |
| `min_liquidity_ratio` | 10.0 | Pool liquidity / stake amount ratio |
| `network` | finney | Network: finney, test, local |
| `log_file` | logs/dca.log | Log file path |
| `dry_run` | false | Preview without staking |

### Target Modes

**Single Subnet** (recommended):
```yaml
target_netuid: 15
```

**Whitelist** (picks best from list):
```yaml
target_netuid: null
whitelist: [15, 22, 48]
```

---

## Protection Mechanisms

### Liquidity Check
Pool must have at least `min_liquidity_ratio` times your stake amount:
```
Required: pool_tao >= stake_amount * min_liquidity_ratio
```

**Example**: With default 10x ratio, staking 1 TAO requires the pool to have 10+ TAO.

Note: Slippage protection is handled natively by btcli.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success OR graceful skip (conditions not met) |
| 1 | Error (config, network, wallet, transaction) |

Cron can use exit codes for alerting on actual failures.

---

## Logs

Logs are written to both stdout (for cron MAILTO) and the configured log file.

```
2025-01-25 14:00:01 | INFO     | Starting DCA stake run
2025-01-25 14:00:02 | INFO     | Connected to finney
2025-01-25 14:00:02 | INFO     | Subnet 15 (ORO): Price = 1.234567 TAO
2025-01-25 14:00:02 | INFO     | Liquidity check: Pool: 500.00 TAO > 1.00 TAO required
2025-01-25 14:00:05 | INFO     | SUCCESS: Staked 0.1 TAO to subnet 15 (ORO)
```

---

## Command Line Options

```
python dca_stake.py [OPTIONS]

Options:
  --config, -c PATH    Config file path (default: config.yaml)
  --dry-run, -n        Preview without staking
```

---

## Troubleshooting

**"Wallet password not found"**
- Set `WALLET_PASSWORD` environment variable, or
- Create `~/.bittensor/.wallet_password` file

**"Insufficient liquidity"**
- Pool doesn't have enough TAO for safe staking
- Wait for more liquidity or reduce `stake_amount`

**"Subnet not found"**
- Check `target_netuid` is correct
- Verify subnet exists on the network

---

## License

MIT
