
import ccxt
import time
import logging
import json
from dotenv import load_dotenv
import os


load_dotenv()

# ================================
# Configuration
# ================================

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

SYMBOL = 'DOGS/USDT'
ORDER_SIZE_USDT = 1.2       # USDT amount to spend per buy order
ORDER_TYPE = 'limit'        # 'limit' or 'market'

# ================================
# Logging Configuration
# ================================

logging.basicConfig(
    level=logging.INFO,
    filename='trading_bot.log',
    format='%(asctime)s [%(levelname)s] %(message)s',
    filemode='w'
)
logger = logging.getLogger(__name__)

# ================================
# Initialize Exchange
# ================================

exchange = ccxt.mexc({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {
        'adjustForTimeDifference': True,
        'recvWindow': 60000,  # 60 seconds
    }
})
exchange.load_markets()
exchange.load_time_difference()

logger.info("Bot configured for DOGS/USDT trading.")

# ================================
# Global State for Position
# ================================
# When no position is held, 'position' is None.
# When a position is held, 'position' stores:
#   - 'entry_price': The price at which DOGS was bought.
#   - 'quantity': The amount of DOGS held.
position = None

# ================================
# Helper Functions
# ================================

def get_current_price(symbol):
    """Fetch the current ticker price for the given symbol."""
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        logger.error(f"Error fetching ticker for {symbol}: {e}")
        return None

def get_free_balance():
    """Fetch the available balance from the exchange."""
    try:
        balance = exchange.fetch_balance()
        free_balance = balance.get('free', {})
        usdt_balance = free_balance.get('USDT', 0)
        dogs_balance = free_balance.get('DOGS', 0)
        logger.info(f"💰 Available Balance - USDT: {usdt_balance}, DOGS: {dogs_balance}")
        return usdt_balance, dogs_balance
    except Exception as e:
        logger.error(f"⚠️ Error fetching balance: {e}")
        return 0, 0

def calculate_order_amount(usdt_amount, price):
    """Calculate how many DOGS tokens to buy with a given USDT amount."""
    return usdt_amount / price

def place_order(symbol, order_type, side, amount, price=None):
    """Place an order on the exchange after checking balances."""
    usdt_balance, dogs_balance = get_free_balance()

    if side == "buy":
        required_usdt = amount * price if price else amount
        if usdt_balance < required_usdt:
            logger.error(f"🚨 Insufficient USDT balance to place buy order. Required: {required_usdt}, Available: {usdt_balance}")
            return None
    elif side == "sell":
        if dogs_balance < amount:
            logger.error(f"🚨 Insufficient DOGS balance to place sell order. Required: {amount}, Available: {dogs_balance}")
            return None

    try:
        if order_type == 'limit':
            order = exchange.create_order(symbol, order_type, side, amount, price)
        else:
            order = exchange.create_order(symbol, order_type, side, amount)
        logger.info(f"✅ Placed {side} {order_type} order for {amount:.6f} units of {symbol} at {price if price else 'market price'}.")
        return order
    except Exception as e:
        error_str = str(e)
        try:
            error_data = json.loads(error_str) if error_str.startswith("{") else {}
            if error_data.get("code") == 30004 or "Insufficient position" in error_data.get("msg", ""):
                logger.error("🚨 Insufficient balance to place order. Pausing for 5 minutes...")
                time.sleep(300)
                return None
        except json.JSONDecodeError:
            pass
        logger.error(f"⚠️ Order placement error: {error_str}")
        return None

# ================================
# Trading Logic
# ================================

def check_and_trade(buy_threshold, sell_threshold):
    """
    Trading rules:
      - When no position is held and current price is at or above the buy_threshold, buy DOGS.
      - When a position is held and current price falls to or below the sell_threshold, sell the entire position.
      - This process then repeats.
    """
    global position

    current_price = get_current_price(SYMBOL)
    if current_price is None:
        return

    logger.info(f"Current price of {SYMBOL}: {current_price}")

    if position is None:
        # No position held: Look to buy when price is at or above the buy threshold.
        if current_price >= buy_threshold:
            logger.info(f"Price {current_price} is at or above your buy threshold {buy_threshold}. Attempting to buy.")
            order_amount = calculate_order_amount(ORDER_SIZE_USDT, current_price)
            result = place_order(SYMBOL, ORDER_TYPE, 'buy', order_amount, current_price if ORDER_TYPE == 'limit' else None)
            if result is not None:
                position = {
                    'entry_price': current_price,
                    'quantity': order_amount
                }
                logger.info(f"Bought {order_amount:.6f} DOGS at {current_price}. Position: {position}")
        else:
            logger.info(f"Waiting for price to reach your buy threshold of {buy_threshold}.")
    else:
        # Position held: Look to sell when price falls to or below the sell threshold.
        if current_price <= sell_threshold:
            logger.info(f"Price {current_price} is at or below your sell threshold {sell_threshold}. Attempting to sell.")
            result = place_order(SYMBOL, ORDER_TYPE, 'sell', position['quantity'], current_price if ORDER_TYPE == 'limit' else None)
            if result is not None:
                logger.info(f"Sold {position['quantity']:.6f} DOGS at {current_price}. Exiting position.")
                position = None
        else:
            logger.info(f"Holding DOGS. Waiting for price to drop to your sell threshold of {sell_threshold}.")

# ================================
# Main Loop
# ================================

def main():
    # Prompt for thresholds. For DOGS, the price values might be very small (for example, 0.000205).
    try:
        buy_threshold = float(input("Enter your desired BUY threshold for DOGS (e.g., 0.000205 or 1.0 if DOGS trades near $1): "))
        sell_threshold = float(input("Enter your desired SELL threshold for DOGS (e.g., 0.000200 or 0.9 if DOGS trades near $1): "))
    except ValueError:
        logger.error("Invalid input for thresholds. Exiting.")
        return

    logger.info("🚀 Starting the DOGS/USDT trading bot...")
    usdt_balance, dogs_balance = get_free_balance()
    logger.info(f"Initial balance: USDT={usdt_balance}, DOGS={dogs_balance}")

    while True:
        try:
            check_and_trade(buy_threshold, sell_threshold)
        except Exception as e:
            error_str = str(e)
            try:
                error_data = json.loads(error_str) if error_str.startswith("{") else {}
                if error_data.get("code") == 30004 or "Insufficient position" in error_data.get("msg", ""):
                    logger.error("🚨 Insufficient balance to place order. Pausing for 5 minutes...")
                    time.sleep(300)
                    continue
            except json.JSONDecodeError:
                pass
            logger.error(f"⚠️ Error in main loop: {error_str}")

        time.sleep(60)  # Check every 60 seconds

if __name__ == "__main__":
    main()
