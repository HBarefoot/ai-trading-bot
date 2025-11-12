#!/usr/bin/env python3
"""
Generate sample portfolio and trade data for testing dashboard
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
import random
from decimal import Decimal
from sqlalchemy.orm import sessionmaker
from data.database import engine, test_connection
from data.models import Portfolio, Trade, Strategy

def create_sample_portfolio():
    """Create sample portfolio data"""
    print("📊 Creating sample portfolio data...")
    
    # Test database connection
    if not test_connection():
        print("❌ Database connection failed!")
        return False
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Clear existing data
        session.query(Portfolio).delete()
        session.query(Trade).delete()
        session.query(Strategy).delete()
        
        # Sample portfolio holdings
        holdings = [
            {"symbol": "BTC", "quantity": 0.5, "avg_cost": 45000.0},
            {"symbol": "ETH", "quantity": 5.0, "avg_cost": 2800.0},
            {"symbol": "ADA", "quantity": 1000.0, "avg_cost": 0.85},
            {"symbol": "DOT", "quantity": 100.0, "avg_cost": 6.5},
            {"symbol": "SOL", "quantity": 20.0, "avg_cost": 180.0},
        ]
        
        # Create portfolio entries
        for holding in holdings:
            portfolio_entry = Portfolio(
                symbol=holding["symbol"],
                quantity=holding["quantity"],
                avg_cost=holding["avg_cost"]
            )
            session.add(portfolio_entry)
        
        # Create sample trades
        trades = []
        for i in range(20):
            symbol = random.choice(["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "SOLUSDT"])
            side = random.choice(["buy", "sell"])
            base_prices = {
                "BTCUSDT": 45000,
                "ETHUSDT": 2800,
                "ADAUSDT": 0.85,
                "DOTUSDT": 6.5,
                "SOLUSDT": 180
            }
            
            price = base_prices[symbol] * random.uniform(0.95, 1.05)
            quantity = random.uniform(0.1, 2.0)
            
            trade = Trade(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                strategy="momentum",
                profit_loss=random.uniform(-100, 100)
            )
            trades.append(trade)
            session.add(trade)
        
        # Create sample strategy
        strategy = Strategy(
            name="Momentum Strategy",
            description="Simple momentum-based trading strategy"
        )
        session.add(strategy)
        
        session.commit()
        
        print(f"✅ Created {len(holdings)} portfolio holdings")
        print(f"✅ Created {len(trades)} sample trades")
        print("✅ Created sample strategy")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("🎲 Generating Sample Portfolio Data for Testing")
    success = create_sample_portfolio()
    
    if success:
        print("🎉 Sample portfolio data generated successfully!")
        print("💡 You can now test the portfolio endpoints and dashboard")
    else:
        print("💥 Failed to generate sample data")