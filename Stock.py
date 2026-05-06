import os
import time
import datetime
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

load_dotenv()
# Load environment variables
API_KEY = os.getenv("APCA_API_KEY_ID")
SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL")

# Connect to Alpaca
api = tradeapi.REST(
    API_KEY,
    SECRET_KEY,
    BASE_URL,
    api_version='v2'
)

# -----------------------------
# CONFIGURATION
# -----------------------------
SYMBOLS = ["EA", "LMT", "QQQ", "VLO", "JPM"]  # your portfolio
MAX_TRADES_PER_HOUR = 2
COOLDOWN_SECONDS = 300  # 5 minutes
WINDOW_MINUTES = 60     # full hour for testing

# -----------------------------
# STATE TRACKING
# -----------------------------
state = {
    symbol: {
        "trades_this_hour": 0,
        "last_trade_time": None
    }
    for symbol in SYMBOLS
}

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def in_trading_window():
    minute = datetime.datetime.now().minute
    return minute <= WINDOW_MINUTES


def cooldown_passed(symbol):
    last = state[symbol]["last_trade_time"]
    if last is None:
        return True
    return (time.time() - last) >= COOLDOWN_SECONDS


def get_signal(symbol):
    """Simple momentum signal for each symbol."""
    bars = api.get_bars(symbol, "1Min", limit=3)
    print(f"  {symbol} bars: {[b.c for b in bars]}")  # debug

    if len(bars) < 3:
        return "HOLD"

    p1 = bars[0].c
    p2 = bars[1].c
    p3 = bars[2].c

    if p3 > p2 > p1:
        return "BUY"
    elif p3 < p2 < p1:
        return "SELL"
    else:
        return "HOLD"


def place_trade(symbol, side):
    try:
        api.submit_order(
            symbol=symbol,
            qty=1,
            side=side.lower(),
            type="market",
            time_in_force="day"
        )
        print(f"TRADE EXECUTED: {side} 1 share of {symbol}")

        state[symbol]["trades_this_hour"] += 1
        state[symbol]["last_trade_time"] = time.time()

    except Exception as e:
        print(f"Trade failed for {symbol}:", e)


# -----------------------------
# MAIN TRADING LOGIC
# -----------------------------
def run_trading_logic():
    print("Starting trading window...")

    while in_trading_window():
        for symbol in SYMBOLS:
            print(f"\nChecking {symbol}...")

            if state[symbol]["trades_this_hour"] >= MAX_TRADES_PER_HOUR:
                print(f"{symbol}: Max trades reached.")
                continue

            if not cooldown_passed(symbol):
                print(f"{symbol}: Cooldown active.")
                continue

            signal = get_signal(symbol)
            print(f"{symbol} signal: {signal}")

            if signal in ["BUY", "SELL"]:
                place_trade(symbol, signal)
            else:
                print(f"{symbol}: No trade.")

        time.sleep(30)

    print("Trading window closed.")


# -----------------------------
# ENTRY POINT
# -----------------------------
def main():
    now = datetime.datetime.now()
    print(f"Bot started at {now}")
    print(f"API_KEY loaded: {'YES' if API_KEY else 'NO'}")
    print(f"SECRET_KEY loaded: {'YES' if SECRET_KEY else 'NO'}")
    print(f"BASE_URL: {BASE_URL}")

    try:
        account = api.get_account()
        print(f"Account status: {account.status}")
        print(f"Buying power: ${account.buying_power}")
    except Exception as e:
        print(f"API connection failed: {e}")
        return

    for symbol in SYMBOLS:
        state[symbol]["trades_this_hour"] = 0

    run_trading_logic()  # always run, no window check for testing

    print("Bot finished.")


if __name__ == "__main__":
    main()