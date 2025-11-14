#!/usr/bin/env python3
import sys
sys.path.append('src')
from data.database import get_db
from data.models import Trade
from datetime import datetime

# Add a test trade to verify database functionality
db = next(get_db())

test_trade = Trade(
    symbol='SOLUSDT',
    side='buy',
    quantity=20.5,
    price=143.21,
    timestamp=datetime.now(),
    strategy='Paper Trading Test',
    profit_loss=0
)

db.add(test_trade)
db.commit()
print('✅ Test trade added to database')

# Verify it was saved
trades = db.query(Trade).all()
print(f'📊 Total trades in database: {len(trades)}')
for trade in trades:
    print(f'  - {trade.side.upper()} {trade.quantity} {trade.symbol} @ ${trade.price}')

db.close()