"""
Test suite for ML models and predictions
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

# Mock ML imports for testing without dependencies
try:
    from ml.lstm_model import CryptoPriceLSTM
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


@pytest.mark.skipif(not ML_AVAILABLE, reason="ML dependencies not available")
class TestLSTMModel:
    """Test LSTM model functionality"""
    
    def test_model_initialization(self):
        """Test LSTM model initialization"""
        model = CryptoPriceLSTM(
            sequence_length=60,
            n_features=5,
            lstm_units=[50, 50],
            dropout_rate=0.2
        )
        
        assert model.sequence_length == 60
        assert model.n_features == 5
        assert model.lstm_units == [50, 50]
        assert model.dropout_rate == 0.2
        assert model.model is None
        assert model.scaler is None
        assert not model.is_trained
    
    def test_model_building(self):
        """Test model architecture building"""
        model = CryptoPriceLSTM()
        keras_model = model.build_model()
        
        assert keras_model is not None
        assert model.model is not None
        assert keras_model.count_params() > 0
    
    def test_data_preparation(self):
        """Test data preparation for training"""
        # Create sample data
        dates = pd.date_range('2025-01-01', periods=200, freq='1H')
        data = {
            'open_price': np.random.uniform(49000, 51000, 200),
            'high_price': np.random.uniform(50000, 52000, 200),
            'low_price': np.random.uniform(48000, 50000, 200),
            'close_price': np.random.uniform(49500, 51500, 200),
            'volume': np.random.uniform(500, 1500, 200)
        }
        df = pd.DataFrame(data)
        
        model = CryptoPriceLSTM(sequence_length=60)
        X, y = model.prepare_data(df)
        
        assert X.shape[0] == len(df) - model.sequence_length
        assert X.shape[1] == model.sequence_length
        assert X.shape[2] == model.n_features
        assert len(y) == len(X)
        assert model.scaler is not None
    
    @pytest.mark.slow
    def test_model_training(self):
        """Test model training (marked as slow)"""
        # Create sample data
        dates = pd.date_range('2025-01-01', periods=1000, freq='1H')
        data = {
            'open_price': np.random.uniform(49000, 51000, 1000),
            'high_price': np.random.uniform(50000, 52000, 1000),
            'low_price': np.random.uniform(48000, 50000, 1000),
            'close_price': np.random.uniform(49500, 51500, 1000),
            'volume': np.random.uniform(500, 1500, 1000)
        }
        df = pd.DataFrame(data)
        
        model = CryptoPriceLSTM(sequence_length=60)
        X, y = model.prepare_data(df)
        
        # Split data
        split_idx = int(0.8 * len(X))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Train model (minimal epochs for testing)
        history = model.train(X_train, y_train, X_val, y_val, epochs=1, verbose=0)
        
        assert model.is_trained
        assert history is not None
    
    def test_prediction_shape(self):
        """Test prediction output shape"""
        model = CryptoPriceLSTM(sequence_length=60)
        
        # Create mock input
        X_test = np.random.random((10, 60, 5))
        
        # Mock a trained model for testing
        model.build_model()
        model.is_trained = True
        model.scaler = MockScaler()
        
        predictions = model.predict(X_test)
        
        assert len(predictions) == 10
        assert isinstance(predictions, np.ndarray)


class MockScaler:
    """Mock scaler for testing"""
    
    def inverse_transform(self, data):
        """Mock inverse transform"""
        if len(data.shape) == 2:
            return data
        return data.reshape(-1, 1)


class TestMLPipeline:
    """Test ML pipeline components"""
    
    def test_feature_engineering(self):
        """Test feature engineering functions"""
        # Create sample price data
        prices = np.random.uniform(50000, 51000, 100)
        
        # Test moving averages
        ma_20 = pd.Series(prices).rolling(20).mean()
        assert len(ma_20) == 100
        assert not ma_20.iloc[19:].isna().any()  # Should have values after window
        
        # Test RSI calculation (simplified)
        gains = pd.Series(prices).diff().clip(lower=0)
        losses = -pd.Series(prices).diff().clip(upper=0)
        
        assert len(gains) == 100
        assert len(losses) == 100
        assert (gains >= 0).all()
        assert (losses >= 0).all()
    
    def test_data_validation(self):
        """Test data validation for ML"""
        # Valid data
        data = {
            'open_price': [50000, 51000, 49000],
            'high_price': [51000, 52000, 50000],
            'low_price': [49500, 50500, 48500],
            'close_price': [50500, 51500, 49500],
            'volume': [1000, 1100, 900]
        }
        df = pd.DataFrame(data)
        
        # Validate OHLC relationships
        for i, row in df.iterrows():
            assert row['high_price'] >= row['open_price']
            assert row['high_price'] >= row['close_price']
            assert row['low_price'] <= row['open_price']
            assert row['low_price'] <= row['close_price']
            assert row['volume'] > 0
    
    def test_prediction_confidence(self):
        """Test prediction confidence calculation"""
        # Mock predictions
        predictions = np.array([50000, 51000, 49000])
        actual = np.array([50100, 50900, 49100])
        
        # Calculate mean absolute percentage error
        mape = np.mean(np.abs((actual - predictions) / actual)) * 100
        confidence = max(0, 100 - mape) / 100
        
        assert 0 <= confidence <= 1
        assert isinstance(confidence, (int, float))


class TestPerformanceMetrics:
    """Test performance metrics calculation"""
    
    def test_directional_accuracy(self):
        """Test directional accuracy calculation"""
        actual_prices = np.array([50000, 51000, 50500, 52000, 51500])
        predicted_prices = np.array([50100, 51200, 50300, 52100, 51200])
        
        # Calculate direction changes
        actual_direction = np.sign(np.diff(actual_prices))
        pred_direction = np.sign(np.diff(predicted_prices))
        
        # Calculate accuracy
        directional_accuracy = np.mean(actual_direction == pred_direction) * 100
        
        assert 0 <= directional_accuracy <= 100
        assert isinstance(directional_accuracy, (int, float))
    
    def test_profit_loss_calculation(self):
        """Test P&L calculation"""
        entry_price = 50000
        exit_price = 51000
        quantity = 0.1
        
        # Long position P&L
        pnl_long = (exit_price - entry_price) * quantity
        assert pnl_long == 100
        
        # Short position P&L
        pnl_short = (entry_price - exit_price) * quantity
        assert pnl_short == -100
    
    def test_risk_metrics(self):
        """Test risk metrics calculation"""
        returns = np.array([0.02, -0.01, 0.03, -0.02, 0.01])
        
        # Calculate volatility (standard deviation)
        volatility = np.std(returns)
        assert volatility > 0
        
        # Calculate Sharpe ratio (simplified)
        mean_return = np.mean(returns)
        sharpe_ratio = mean_return / volatility if volatility > 0 else 0
        
        assert isinstance(sharpe_ratio, (int, float))
        
        # Calculate maximum drawdown
        cumulative_returns = (1 + pd.Series(returns)).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        assert max_drawdown <= 0  # Drawdown should be negative or zero