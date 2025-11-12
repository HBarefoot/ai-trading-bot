"""
Training script for LSTM model
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lstm_model import ModelTrainer
from data.database import engine, test_connection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main training function"""
    print("🤖 Starting LSTM Model Training")
    
    # Test database connection
    if not test_connection():
        print("❌ Database connection failed")
        return
    
    # Define symbols to train models for
    symbols = ['BTCUSDT', 'ETHUSDT']
    
    for symbol in symbols:
        try:
            print(f"📈 Training model for {symbol}...")
            
            # Initialize trainer
            trainer = ModelTrainer(symbol)
            
            # Load data
            df = trainer.load_data(engine)
            
            if len(df) < 1000:  # Need sufficient data
                print(f"⚠️ Insufficient data for {symbol}: {len(df)} records")
                continue
            
            # Train model
            history, metrics = trainer.train_model(df)
            
            print(f"✅ Model trained for {symbol}")
            print(f"📊 RMSE: {metrics['rmse']:.2f}, Directional Accuracy: {metrics['directional_accuracy']:.1f}%")
            
        except Exception as e:
            logger.error(f"Error training model for {symbol}: {e}")
            continue
    
    print("🎉 Training completed!")


if __name__ == "__main__":
    main()