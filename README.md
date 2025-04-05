# Solana Whale Order Book Visualizer & Tracker

## 🚀 What It Does

This tool scans the **top holders of any SPL token**, fetches their **active limit orders** (via Jupiter/Trigger), and **aggregates those orders by price level**. It then overlays that orderbook information as **horizontal lines** on top of the **real-time price chart** (pulled from Birdeye API).

Buy orders are shown in **green**, sell orders in **red**, with their respective sizes (in SOL equivalent) labeled on the side of the chart.

> Perfect for visualizing where big players are waiting to buy or sell.

---

## Why This Matters

Large holders often place visible limit orders. By tracking and plotting them:

- You can **anticipate key price levels** where large buy/sell pressure will kick in.
- You can **frontrun large buy orders** by buying slightly ahead of their price and selling into the slippage if they get filled.
- Similarly, you can **short/sell before large sell walls** get hit, profiting from the anticipated pullback.

It becomes a **map of where the whales sit**, and you're the drone flying overhead.

---

## How It Works

1. **Finds Top Holders**:
   - Uses the Helius API to scan token accounts and find top wallets holding the token.

2. **Fetches Active Orders**:
   - For each top wallet, it queries Jupiter's Trigger API to check open limit orders.

3. **Interprets Order Direction**:
   - Determines whether the holder is buying or selling the token.

4. **Aggregates Orders**:
   - Merges all open orders at similar price levels and sums their size in SOL equivalent.

5. **Fetches Price History**:
   - Pulls 1-minute resolution price data for the token via the Birdeye API.

6. **Plots Price + Orders**:
   - Overlays buy/sell walls as horizontal lines on top of a price chart with EMA smoothing.

---

## 💡 Frontrunning Strategy Use Case

This script can help you identify moments like:

- **Whale has buy wall at $0.0140 with 120 SOL**:
  - You buy at $0.0141.
  - Price dips and hits the whale's buy wall, triggering a rebound.
  - You sell at $0.0143–$0.0145 for a **quick gain** off slippage + reaction.

- **Whale has large sell wall at $0.0200**:
  - You sell slightly below or short.
  - Price approaches and stalls at resistance.
  - You exit profitably before full fill or breakout.

---

## ⚙️ Requirements

- Python 3.9+
- `.env` file with:
  ```
  HELIUS_KEY=your_helius_key
  BIRDEYE_KEY=your_birdeye_key
  ```
- Required Python packages:
  ```bash
  pip install requests matplotlib pandas python-dotenv
  ```

---

## 🧪 Run It

```bash
orderbook.py
```

---

## 🛠️ Future Ideas

- Real-time WebSocket updates for limit order book
- Telegram bot alerts when large new orders are placed
- Add candlestick chart option
- Backtest price reactions to whale orders

---

## ⚠️ Disclaimer

This is a research/analytics tool. It **does not place trades** or interact with any trading platform directly. Use at your own risk. Trading based on on-chain data has risks, including front-running, MEV, and latency issues.

