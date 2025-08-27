#!/usr/bin/env python3
import json
from urllib.request import urlopen, Request
from typing import Dict, List

USER_AGENT = 'CryptoAnalytics/1.0 (+https://localhost)'

SYMBOL_TO_COINGECKO = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'ADA': 'cardano',
    'SOL': 'solana',
    'DOT': 'polkadot',
    'LINK': 'chainlink',
    'MATIC': 'matic-network',
    'AVAX': 'avalanche-2',
}


def fetch_prices_usd(symbols: List[str]) -> Dict[str, float]:
    ids = ','.join({SYMBOL_TO_COINGECKO.get(sym.upper(), '') for sym in symbols if SYMBOL_TO_COINGECKO.get(sym.upper())})
    if not ids:
        return {}
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd'
    req = Request(url, headers={'User-Agent': USER_AGENT})
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    prices: Dict[str, float] = {}
    for sym, cg in SYMBOL_TO_COINGECKO.items():
        if cg in data and 'usd' in data[cg]:
            prices[sym] = float(data[cg]['usd'])
    return prices

if __name__ == '__main__':
    print(fetch_prices_usd(['BTC','ETH','SOL']))
