## DOGS/USDT Trading Bot

This is a simple trading bot for DOGS/USDT that repeatedly buys and sells based on user-defined thresholds. The bot:

1. Buys DOGS when the price is at or above a specified "buy threshold."
2. Sells the entire DOGS position if the price falls to or below a specified "sell threshold."
3. Repeats this process indefinitely.

## Features

- **Customizable Thresholds:** You set the buy and sell thresholds when starting the bot.
- **Simple Logic:** No complex indicators—just price levels and automated order placement.
- **Continuous Operation:** The bot checks the price every minute and reacts accordingly.

## Prerequisites

- **Python 3.6+**
- The following Python packages:
  - `ccxt`
  - `json`
  - `time`
  - `logging`

You can install the required packages via pip:
```bash
pip install ccxt
```

## Configuration

Before running the bot, make sure to update the following variables in the code:

- **`API_KEY` and `API_SECRET`**: Your MEXC exchange API keys.
- **`SYMBOL`**: The trading pair (default is `DOGS/USDT`).
- **`ORDER_SIZE_USDT`**: The amount of USDT to spend on each buy order.
- **`ORDER_TYPE`**: The order type (`'limit'` or `'market'`).

## Usage

1. **Run the script**:  
   ```bash
   python trading_bot.py
   ```

2. **Enter thresholds**:  
   You’ll be prompted to enter your buy and sell thresholds. For example:
   ```
   Enter your desired BUY threshold for DOGS: 0.000205
   Enter your desired SELL threshold for DOGS: 0.000200
   ```

3. **Let it run**:  
   The bot will start and continuously check the current price, buying and selling as conditions are met. Logs are stored in `trading_bot.log`.

## How It Works

- **No position held:**  
  If the current price is at or above the buy threshold, the bot places a buy order and sets the position to "held."
  
- **Position held:**  
  If the price falls to or below the sell threshold, the bot places a sell order, clears the position, and starts looking for the next buy opportunity.

## Notes

- **Profit and Risk:** This bot does not guarantee profits. It’s a simple price-based trading strategy, and you should fully understand the risks before using it.
- **API Permissions:** Ensure your API key has the necessary permissions for reading balances and placing trades.
