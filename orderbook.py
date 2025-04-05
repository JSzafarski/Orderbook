import time
import requests
import matplotlib.pyplot as plt
from collections import defaultdict
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env into environment

HELIUS_KEY = os.getenv("HELIUS_KEY ")
BIRDEYE_KEY = os.getenv("BIRDEYE_KEY")

# Only focusing on USDC, WSOL, USDT swaps
USDC = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
WSOL = 'So11111111111111111111111111111111111111112'
USDT = 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
SOL_PRICE = 125  # Approx

STABLE_OR_SOL = {USDC, USDT, WSOL}


def fetch_open_orders(wallet):
    url = 'https://api.jup.ag/trigger/v1/getTriggerOrders'
    params = {
        'user': wallet,
        'orderStatus': 'active'
    }

    response = requests.get(url, params=params)
    return response.json()


def interpreter(data, token_of_interest):
    orders = data.get('orders', [])
    interpreted = []

    for order in orders:
        input_mint = order['inputMint']
        output_mint = order['outputMint']

        # Selling the token (token -> USDC/USDT/SOL)
        if input_mint == token_of_interest and output_mint in STABLE_OR_SOL:
            price = float(order['takingAmount']) / float(order['makingAmount'])
            sol_equiv = (
                float(order['takingAmount']) if output_mint == WSOL
                else float(order['takingAmount']) / SOL_PRICE
            )
            interpreted.append({
                'side': 'sell',
                'target_price': round(price, 6),
                'amount_in_sol': round(sol_equiv, 6)
            })

        # Buying the token (USDC/USDT/SOL -> token)
        elif output_mint == token_of_interest and input_mint in STABLE_OR_SOL:
            price = float(order['makingAmount']) / float(order['takingAmount'])
            sol_equiv = (
                float(order['makingAmount']) if input_mint == WSOL
                else float(order['makingAmount']) / SOL_PRICE
            )
            interpreted.append({
                'side': 'buy',
                'target_price': round(price, 6),
                'amount_in_sol': round(sol_equiv, 6)
            })

    return {'orders': interpreted}

def fetch_top_token_holders(token, top_n=20):
    page = 1
    all_accounts = []  # This will store dictionaries of owner and amount
    url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_KEY}"
    headers = {
        "Content-Type": "application/json",
    }

    while True:
        payload = {
            "jsonrpc": "2.0",
            "method": "getTokenAccounts",
            "id": "helius-test",
            "params": {
                "page": page,
                "limit": 1000,
                "displayOptions": {},
                "mint": f"{token}",
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        if not response.ok:
            print(f"Error: {response.status_code}, {response.text}")
            break

        data = response.json()
        token_accounts = data.get("result", {}).get("token_accounts", [])
        if not token_accounts:
            break

        for account in token_accounts:
            all_accounts.append({
                "owner": account["owner"],
                "amount": account["amount"]
            })

        page += 1

    # Combine by owner in case the same owner has multiple accounts
    owner_balances = {}
    for acc in all_accounts:
        owner = acc["owner"]
        amount = acc["amount"]
        owner_balances[owner] = owner_balances.get(owner, 0) + amount

    # Sort by amount descending and return top N
    top_holders = sorted(owner_balances.items(), key=lambda x: x[1], reverse=True)[:top_n]


    hol = [owner for owner, _ in top_holders]
    return hol

def aggregate_orders(order_lists, precision=4):
    """
    Merges many users' orders into a combined book.
    Groups by price level and sums amounts.
    """
    buy_book = defaultdict(float)
    sell_book = defaultdict(float)

    for user_orders in order_lists:
        for order in user_orders['orders']:
            price = round(order['target_price'], precision)
            amt = order['amount_in_sol']

            if order['side'] == 'buy':
                buy_book[price] += amt
            else:
                sell_book[price] += amt

    # Convert to sorted lists
    buy_side = sorted(buy_book.items(), key=lambda x: -x[0])  # descending price
    sell_side = sorted(sell_book.items(), key=lambda x: x[0])  # ascending price
    return buy_side, sell_side

def plot_price_with_orders(token_address, buy_orders, sell_orders, api_key=BIRDEYE_KEY):
    """
    Fetches token price data from Birdeye, calculates EMA,
    and plots it with horizontal limit order levels.
    """
    # Step 1: Fetch price history
    current_unix_time = int(time.time())
    url = 'https://public-api.birdeye.so/defi/history_price'
    params = {
        'address': token_address,
        'address_type': 'token',
        'type': '1m',
        'time_from': '0',
        'time_to': f'{current_unix_time}'
    }
    headers = {
        'accept': 'application/json',
        'x-chain': 'solana',
        'X-API-KEY': api_key
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Failed to fetch price data: {response.status_code}")
        return

    res = response.json()['data']['items']
    if not res:
        print("No price data returned.")
        return

    # Step 2: Create DataFrame
    prices = [snap['value'] for snap in res]
    times = [snap['unixTime'] for snap in res]

    df = pd.DataFrame({
        'Time': pd.to_datetime(times, unit='s'),
        'Price': prices
    })

    # Step 3: Calculate EMA
    df['EMA_20'] = df['Price'].ewm(span=20, adjust=False).mean()

    # Step 4: Plot price + limit orders
    plt.figure(figsize=(14, 7))
    plt.plot(df['Time'], df['EMA_20'], linestyle='-', color='black', label='EMA 20')

    for price, size in buy_orders:
        plt.hlines(price, xmin=df['Time'].min(), xmax=df['Time'].max(),
                   color='green', alpha=0.4, linestyle='--')
        plt.text(df['Time'].max(), price, f'{round(size, 2)}',
                 va='center', ha='left', color='green', fontsize=9)

    for price, size in sell_orders:
        plt.hlines(price, xmin=df['Time'].min(), xmax=df['Time'].max(),
                   color='red', alpha=0.4, linestyle='--')
        plt.text(df['Time'].max(), price, f'{round(size, 2)}',
                 va='center', ha='left', color='red', fontsize=9)

    plt.xlabel('Time')
    plt.ylabel('Price (USD)')
    plt.title('Token Price + Limit Orders')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.xticks(rotation=45)
    plt.show()

def main():
    token = 'GNwWV9y6XqbXcZFZBbuDcEXaMm8jegfwEJfN2z6Wpump'
    top_holders = fetch_top_token_holders(token)
    order_list = []
    for holder in top_holders:
        print(holder)
        orders = interpreter(fetch_open_orders(holder),token)
        order_list.append(orders)
        time.sleep(.2)
    print(order_list)
    buy_side, sell_side = aggregate_orders(order_list)
    plot_price_with_orders(token,buy_side, sell_side)


main()