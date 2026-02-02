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

Run this command to set up automatic DCA every 2 hours:

```bash
(crontab -l 2>/dev/null; echo "0 */2 * * * cd $(pwd) && $(pwd)/.venv/bin/python dca_stake.py >> $(pwd)/logs/cron.log 2>&1") | crontab -
```

**Other schedules:**
- Every hour: `0 * * * *`
- Every 4 hours: `0 */4 * * *`
- Every 6 hours: `0 */6 * * *`
- Daily at 2am: `0 2 * * *`

To view your schedule: `crontab -l`
To remove: `crontab -r`

---

## Important: Mac Sleep Behavior

**Cron jobs do NOT run while your Mac is asleep.** Missed jobs are skipped, not caught up.

### Option A: Wake Mac for DCA (Recommended for laptops)

Set your Mac to wake automatically at your DCA times:

```bash
# Wake every 2 hours (matches default schedule)
sudo pmset repeat wake MTWRFSU 00:00:00
sudo pmset repeat wake MTWRFSU 02:00:00
sudo pmset repeat wake MTWRFSU 04:00:00
sudo pmset repeat wake MTWRFSU 06:00:00
sudo pmset repeat wake MTWRFSU 08:00:00
sudo pmset repeat wake MTWRFSU 10:00:00
sudo pmset repeat wake MTWRFSU 12:00:00
sudo pmset repeat wake MTWRFSU 14:00:00
sudo pmset repeat wake MTWRFSU 16:00:00
sudo pmset repeat wake MTWRFSU 18:00:00
sudo pmset repeat wake MTWRFSU 20:00:00
sudo pmset repeat wake MTWRFSU 22:00:00
```

To clear wake schedule: `sudo pmset repeat cancel`

### Option B: Run on Always-On Server (Best reliability)

For 24/7 reliability, run on:
- A cheap VPS ($5/month from DigitalOcean, Vultr, etc.)
- A Raspberry Pi at home
- Any always-on Linux machine

Just copy the repo, run the setup, and add the cron job.

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

---

## License

MIT
