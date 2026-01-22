# Bittensor Telegram DCA Bot (ORO Fork)

Interactive DCA script which uses a Telegram frontend to pass commands.

> **Thanks to [@const](https://github.com/unconst) for the original [DynamicBot](https://github.com/unconst/DynamicBot) script that this fork is based on!** 🙏

## Fork Modifications

This fork adds three key features for safer DCA operations:

### 1. Whitelist Mode (Include List)
Instead of excluding subnets, you can now specify exactly which subnets to DCA into. This is ideal for investors who want to focus on specific subnets (like your own).

### 2. Liquidity Protection
The bot now checks pool liquidity before staking. If a subnet has low liquidity, the bot will skip it to avoid moving the market significantly.

### 3. MEV/Slippage Protection
Added slippage tolerance to protect against sandwich attacks and excessive price impact. The bot calculates estimated price impact before staking and rejects trades that exceed your tolerance.

---

## Getting Started

1. **Make a Telegram bot:**
   - Visit [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot` and follow the prompts to create your bot
   - Save the API token that BotFather gives you - this will be your `telegram_token` in config.yaml
   - Add your bot to a private Telegram channel/group with just you.
   - Send a test message to your bot
   - Visit https://api.telegram.org/bot<your_token>/getUpdates to get your chat_id.
   - Copy the "id" field from the JSON response - this will be your `telegram_chat_id` in config.yaml
   - Disable privacy mode by sending `/setprivacy` to BotFather and selecting your bot
   - Send another test message to verify everything is working

2. **Fill in config:**

    Create a `config.yaml` file in the project root. Below is an example configuration:

    ```yaml
    wallet: "<your wallet name>"
    stake_amount: 0.01        # Base TAO amount to stake per block.
    validator: "5F4tQyWrhfGVcNhoqeiNsR6KjD4wMZ2kfhLj4oHYuyHbZAc3" # OTF

    # BLACKLIST: Never stake in these subnets
    exclude_list: []

    # WHITELIST: ONLY stake in these subnets (takes precedence over exclude_list)
    # When non-empty, the bot will ONLY DCA into these subnets
    include_list: []
    # Example: include_list: [22, 48, 52]  # Only stake in subnets 22, 48, 52

    # MEV PROTECTION: Maximum acceptable slippage/price impact
    # 0.02 = 2% max slippage. Lower values = more protection but may reject more trades
    max_slippage: 0.02

    # LIQUIDITY PROTECTION: Minimum ratio of pool liquidity to stake amount
    # 10.0 means pool must have at least 10x your stake amount in liquidity
    # Note: With 10x ratio, max price impact is ~9.1% - this is by design
    min_liquidity_ratio: 10.0

    preferences:               # Preference multipliers per subnet.
        "4": 1.5
        "9": 2.0 # (2 here means this subnet gets a score multiple of 2x when choosing the best subnet to DCA into.

    telegram_token: "YOUR_TELEGRAM_BOT_TOKEN"  # ( see step 1.)
    telegram_chat_id: "-123456789"    # Your Telegram channel/group chat ID ( see step 1.)
    telegram_update_interval: 10      # Send periodic updates every 10 blocks.
    ```

    **Note:**
    - The `preferences` keys must be strings.
    - Update `telegram_token` and `telegram_chat_id` with your actual Telegram bot token and channel/group ID.


3. **Clone the Repository:**

   ```bash
   git clone https://github.com/ORO-AI/DCABot.git
   cd DCABot
   ```

4. **Install Dependencies:**

    Use pip to install required packages:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    ```

5. **Install PM2:**

    For Ubuntu/Debian:
    ```bash
    apt update
    apt install -y nodejs npm
    npm install -g pm2
    ```

    For MacOS:
    ```bash
    # Install Homebrew if not already installed
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Install Node.js and npm
    brew install node

    # Install PM2 globally
    npm install -g pm2
    ```

6. **Run**

    Run the bot.

    ```bash
    export WALLET_PASSWORD='<YOUR WALLET PASSWORD HERE>'; pm2 delete autobot; pm2 start autobot.py --interpreter python3 --name autobot --cron-restart="0 * * * *"; pm2 logs autobot
    ```

7. **Use Telegram to interact**

Interact with the bot using Telegram. Below are the supported commands:

### Basic Commands

- **/pause**
  _Description:_ Stops the bot staking into subnets.
  _Response:_ Confirms the bot has been paused.

- **/start**
  _Description:_ Starts the bot staking into subnets
  _Response:_ Confirms the bot has been started.

- **/info `<netuid>`**
  _Description:_ Returns information about the specified subnet, including:
  - Current price.
  - Your current stake.
  - Current preference multiplier.
  - Current block number.

- **/boost `<netuid>`**
  _Description:_ Increases the preference multiplier for the specified subnet by 0.1.
  _Response:_ New preference value.

- **/slash `<netuid>`**
  _Description:_ Decreases the preference multiplier for the specified subnet by 0.1 (minimum 0.1).
  _Response:_ New preference value.

### Whitelist/Blacklist Commands

- **/include `<netuid>`**
  _Description:_ Adds the specified subnet to the whitelist. When the whitelist is non-empty, the bot will ONLY stake in whitelisted subnets.
  _Response:_ Confirmation message.

- **/remove `<netuid>`**
  _Description:_ Removes the specified subnet from the whitelist.
  _Response:_ Confirmation message.

- **/exclude `<netuid>`**
  _Description:_ Adds the specified subnet to the blacklist. The bot will never stake in blacklisted subnets (only applies when whitelist is empty).
  _Response:_ Confirmation message.

- **/lists**
  _Description:_ Shows current whitelist, blacklist, and protection settings.
  _Response:_ Current configuration summary.

### Protection Commands (NEW)

- **/slippage `<value>`**
  _Description:_ Sets the maximum acceptable slippage/price impact. Use decimal format (e.g., 0.02 for 2%).
  _Example:_ `/slippage 0.01` sets max slippage to 1%.
  _Response:_ New slippage tolerance.

- **/liquidity `<value>`**
  _Description:_ Sets the minimum liquidity ratio. The pool must have at least this multiple of your stake amount in liquidity.
  _Example:_ `/liquidity 20` requires pools to have 20x your stake amount.
  _Response:_ New liquidity ratio.

### Staking Commands

- **/unstake `<netuid>` `<amount>`**
  _Description:_ Sells (unstakes) the specified amount of TAO from the given subnet.
  _Response:_ Confirmation of the unstake action.

- **/stake `<netuid>` `<amount>`**
  _Description:_ Buys (stakes) the specified amount of TAO into the given subnet.
  _Response:_ Confirmation of the stake action.

- **/amount `<value>`**
  _Description:_ Sets the base stake amount used per block to the specified value.
  _Response:_ New stake amount.

### Portfolio Commands

- **/balance**
  _Description:_ Returns a summary of your current portfolio, including:
  - Wallet balance.
  - Current block.
  - Staked amounts per subnet.

- **/history**
  _Description:_ Returns a detailed history summary since the last `/history` command. The summary includes:
  - Time elapsed and number of blocks since the last history snapshot.
  - Total amount staked during this period.
  - The difference in total stake.
  - PNL (difference between the previous and current combined wallet + stake value).
  - A per-subnet breakdown of the increase in stake.
  _Response:_ A formatted message with all the details.


## How Protection Works

### Liquidity Check
Before staking, the bot calculates:
```
liquidity_ratio = pool_tao_in / stake_amount
```
If this ratio is below your `min_liquidity_ratio`, the stake is rejected.

### Slippage/MEV Protection
The bot estimates price impact using:
```
price_impact = stake_amount / pool_tao_in
```
If this exceeds your `max_slippage`, the stake is rejected.

### Example
With these settings:
- `stake_amount: 10`
- `max_slippage: 0.02` (2%)
- `min_liquidity_ratio: 10`

A subnet with only 50 TAO in the pool would:
1. Fail liquidity check (50 < 10 * 10 = 100)
2. Have 20% price impact (10/50 = 0.20), failing slippage check

This protects you from:
- Moving the market significantly on low-liquidity subnets
- MEV bots sandwiching your transactions
- Excessive slippage on large orders

**Note:** With the default 10x liquidity ratio, the maximum price impact is approximately 9.1%. This is intentional - it provides protection while still allowing trades on reasonably liquid pools.


## Troubleshooting

- **Telegram Updates Not Received:**
  - Ensure that your Telegram bot is added to your group or channel and that privacy mode is disabled if necessary.
  - Verify that your `telegram_token` and `telegram_chat_id` are correct.

- **Wallet Connection Issues:**
  - Check that the `WALLET_PASSWORD` environment variable is set.
  - Verify the wallet name and file permissions.

- **Bittensor Connectivity:**
  - Confirm that the endpoint in your configuration is correct and that you have a stable network connection.

- **All Subnets Rejected:**
  - Check `/whitelist` to ensure you have subnets in your whitelist
  - Try lowering `max_slippage` or `min_liquidity_ratio` if being too conservative
  - Use `/info <netuid>` to check specific subnet liquidity

---

## License

DYOR. NFA.

[MIT License](LICENSE)

---
