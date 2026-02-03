# Bittensor DCA Stake

Simple automated Dollar Cost Averaging (DCA) into Bittensor subnets.

---

## Step 1: Buy TAO

Purchase TAO from any of these exchanges:

| Exchange | Link |
|----------|------|
| **Coinbase** | [coinbase.com](https://www.coinbase.com) |
| **Kraken** | [kraken.com](https://www.kraken.com) |
| **Binance** | [binance.com](https://www.binance.com) |

Search for "TAO" or "Bittensor" and buy your desired amount.

---

## Step 2: Create a Bittensor Wallet

Install Bittensor and create a wallet:

```bash
pip install bittensor
btcli wallet create --wallet.name default
```

Save your mnemonic phrase securely. This is your backup.

Your wallet address will be displayed (starts with `5...`). Copy it.

---

## Step 3: Transfer TAO to Your Wallet

On the exchange, withdraw your TAO to the wallet address from Step 2.

Verify it arrived:
```bash
btcli wallet balance --wallet.name default
```

---

## Step 4: Setup DCA Script

```bash
# Clone and setup (one command)
git clone https://github.com/ORO-AI/BittensorDCA.git && cd BittensorDCA && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Save your wallet password (so the script can auto-unlock):
```bash
echo "your-wallet-password" > ~/.bittensor/.wallet_password
chmod 600 ~/.bittensor/.wallet_password
```

Edit `config.yaml` with your settings:
```yaml
wallet_name: "default"
stake_amount: 0.1                # TAO per buy
target_netuid: 15                # Subnet to stake into
```

---

## Step 5: Test It

```bash
.venv/bin/python dca_stake.py --dry-run
```

You should see it connect and show what it would stake.

---

## Step 6: Schedule Automatic Buys

### Why DCA?

Subnet liquidity pools start small and grow over time. If you try to stake a large amount at once, you'll either:
- Get rejected by the liquidity check (pool too small)
- Move the price significantly against yourself

DCA solves this by staking small amounts regularly as liquidity grows. The pool gets deeper every day, so your daily buys become more efficient over time.

### Recommended: Once Daily

**Daily at 2pm is the simplest approach** - one buy per day, easy to track:

```bash
(crontab -l 2>/dev/null; echo "0 14 * * * cd $(pwd) && $(pwd)/.venv/bin/python dca_stake.py >> $(pwd)/logs/cron.log 2>&1") | crontab -
```

**Other schedules:**
- Daily at 2am: `0 2 * * *`
- Daily at 8am: `0 8 * * *`
- Twice daily (8am & 8pm): `0 8,20 * * *`
- Every 6 hours: `0 */6 * * *`

To view your schedule: `crontab -l`
To remove: `crontab -r`

---

## Note: Mac Sleep Behavior

**Cron jobs do NOT run while your Mac is asleep.** Missed jobs are skipped.

**Good news:** If you schedule your daily buy during hours you normally use your laptop (e.g., 2pm), you likely won't need to do anything special. Your Mac will be awake and the cron job will run.

### If You Need Overnight Buys

If you want buys while your Mac sleeps, set it to wake **2 minutes before** your scheduled buy time:

```bash
# Example: Buy at 2:00 AM, wake at 1:58 AM
sudo pmset repeat wake MTWRFSU 01:58:00
```

The Mac will wake, cron runs at 2:00 AM, then it sleeps again.

To clear wake schedule: `sudo pmset repeat cancel`

### For Best Reliability: Always-On Server

For guaranteed 24/7 execution, run on:
- A cheap VPS ($5/month from DigitalOcean, Vultr, etc.)
- A Raspberry Pi at home
- Any always-on Linux machine

Just copy the repo, run the setup, and add the cron job. But this is optional - daily buys during waking hours work fine for most people.

---

## Manual Run

To stake manually anytime:

```bash
cd BittensorDCA
.venv/bin/python dca_stake.py
```

---

## Check Logs

```bash
tail -f logs/cron.log
```

---

## Configuration Options

Edit `config.yaml`:

| Option | Description |
|--------|-------------|
| `wallet_name` | Your Bittensor wallet name |
| `stake_amount` | TAO to stake per run |
| `target_netuid` | Subnet ID to stake into |
| `min_liquidity_ratio` | Safety check (default: 10x) |
| `max_price` | Only stake when price <= this value (TAO) |
| `max_slippage` | Max price change during execution (default: 0.05 = 5%) |
| `max_jitter_seconds` | Random delay before execution (default: 0) |
| `dry_run` | Set `true` to test without staking |

---

## Troubleshooting

**"Wallet password not found"**
```bash
echo "your-password" > ~/.bittensor/.wallet_password
chmod 600 ~/.bittensor/.wallet_password
```

**"Insufficient liquidity"**
- The subnet pool is too small for safe staking
- Try a smaller `stake_amount` or wait for more liquidity

**Check if cron is running:**
```bash
crontab -l
tail -20 logs/cron.log
```

**"Price exceeds max_price - skipping stake"**
- Current price is above your `max_price` threshold
- This is expected - stake will occur when price drops

**"Stake transaction returned failure" (with slippage protection)**
- Price moved more than `max_slippage` during execution
- This protects you from buying at unexpectedly high prices

---

## License

MIT
