#!/usr/bin/env python3
import sys
sys.path.append('src')
import requests

# Test what the dashboard API client should be doing
try:
    response = requests.get('http://localhost:9000/api/trades?limit=50', timeout=5)
    print(f'Status Code: {response.status_code}')
    response.raise_for_status()
    data = response.json()
    print(f'Success! Got {len(data)} trades')
    for trade in data:
        print(f'  - {trade["side"].upper()} {trade["quantity"]} {trade["symbol"]} @ ${trade["price"]}')
except Exception as e:
    print(f'Error: {e}')