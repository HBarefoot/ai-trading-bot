"""
LSTM model for cryptocurrency price prediction
"""
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import logging
from typing import Tuple, Optional
import joblib
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CryptoPriceLSTM:
    """LSTM model for cryptocurrency price prediction"""
    
    def __init__(
        self,
        sequence_length: int = 60,
        n_features: int = 5,
        lstm_units: list = [50, 50],
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001
    ):
        """
        Initialize LSTM model
        
        Args:
            sequence_length: Number of time steps to look back
            n_features: Number of input features (OHLCV = 5)
            lstm_units: List of LSTM layer units
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for optimizer
        """
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        
        self.model = None
        self.scaler = None
        self.is_trained = False
        
    def build_model(self) -> tf.keras.Model:
        """Build LSTM model architecture"""
        model = Sequential()
        
        # First LSTM layer
        model.add(LSTM(
            self.lstm_units[0],
            return_sequences=True if len(self.lstm_units) > 1 else False,
            input_shape=(self.sequence_length, self.n_features)
        ))
        model.add(BatchNormalization())
        model.add(Dropout(self.dropout_rate))
        
        # Additional LSTM layers
        for i, units in enumerate(self.lstm_units[1:], 1):
            return_sequences = i < len(self.lstm_units) - 1
            model.add(LSTM(units, return_sequences=return_sequences))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout_rate))
        
        # Dense layers
        model.add(Dense(25, activation='relu'))
        model.add(Dropout(self.dropout_rate))
        model.add(Dense(1))  # Single output for price prediction
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        logger.info(f"Built LSTM model with {model.count_params()} parameters")
        return model
    
    def prepare_data(self, df: pd.DataFrame, target_column: str = 'close_price') -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for training
        
        Args:
            df: DataFrame with OHLCV data
            target_column: Column to predict
            
        Returns:
            Tuple of (X, y) arrays
        """
        # Select features (OHLCV)
        feature_columns = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
        data = df[feature_columns].values
        
        # Scale features
        if self.scaler is None:
            self.scaler = MinMaxScaler()
            scaled_data = self.scaler.fit_transform(data)
        else:
            scaled_data = self.scaler.transform(data)
        
        # Create sequences
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i])
            # Target is next close price (index 3 = close_price)
            y.append(scaled_data[i, 3])
        
        return np.array(X), np.array(y)
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 100,
        batch_size: int = 32,
        verbose: int = 1
    ) -> tf.keras.callbacks.History:
        """
        Train the LSTM model
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            epochs: Number of training epochs
            batch_size: Batch size
            verbose: Verbosity level
            
        Returns:
            Training history
        """
        if self.model is None:
            self.build_model()
        
        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=15,
                restore_best_weights=True
            ),
            ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=10,
                min_lr=1e-7
            )
        ]
        
        # Add model checkpoint
        model_path = f"data/models/lstm_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h5"
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        callbacks.append(ModelCheckpoint(
            model_path,
            monitor='val_loss' if X_val is not None else 'loss',
            save_best_only=True,
            verbose=1
        ))
        
        # Train model
        validation_data = (X_val, y_val) if X_val is not None and y_val is not None else None
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
        
        self.is_trained = True
        logger.info("Model training completed")
        return history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained or self.model is None:
            raise ValueError("Model must be trained before making predictions")
        
        predictions = self.model.predict(X)
        
        # Inverse transform predictions to original scale
        if self.scaler is not None:
            # Create dummy array with same shape as original features
            dummy = np.zeros((predictions.shape[0], self.n_features))
            dummy[:, 3] = predictions.flatten()  # Put predictions in close_price position
            predictions_scaled = self.scaler.inverse_transform(dummy)[:, 3]
            return predictions_scaled
        
        return predictions.flatten()
    
    def predict_next_price(self, recent_data: np.ndarray) -> float:
        """
        Predict next price given recent data
        
        Args:
            recent_data: Array of shape (sequence_length, n_features)
            
        Returns:
            Predicted next price
        """
        if recent_data.shape != (self.sequence_length, self.n_features):
            raise ValueError(f"Input shape must be ({self.sequence_length}, {self.n_features})")
        
        # Scale input data
        scaled_data = self.scaler.transform(recent_data)
        
        # Reshape for prediction
        X = scaled_data.reshape(1, self.sequence_length, self.n_features)
        
        # Make prediction
        prediction = self.predict(X)
        return float(prediction[0])
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """Evaluate model performance"""
        predictions = self.predict(X_test)
        
        # Inverse transform actual values
        dummy = np.zeros((y_test.shape[0], self.n_features))
        dummy[:, 3] = y_test
        y_test_scaled = self.scaler.inverse_transform(dummy)[:, 3]
        
        # Calculate metrics
        mse = mean_squared_error(y_test_scaled, predictions)
        mae = mean_absolute_error(y_test_scaled, predictions)
        rmse = np.sqrt(mse)
        
        # Calculate directional accuracy
        actual_direction = np.sign(np.diff(y_test_scaled))
        pred_direction = np.sign(np.diff(predictions))
        directional_accuracy = np.mean(actual_direction == pred_direction) * 100
        
        metrics = {
            'mse': mse,
            'mae': mae,
            'rmse': rmse,
            'directional_accuracy': directional_accuracy
        }
        
        logger.info(f"Model evaluation - RMSE: {rmse:.2f}, MAE: {mae:.2f}, Dir. Acc: {directional_accuracy:.1f}%")
        return metrics
    
    def save_model(self, filepath: str):
        """Save model and scaler"""
        if self.model is None:
            raise ValueError("No model to save")
        
        # Save model
        self.model.save(filepath)
        
        # Save scaler
        scaler_path = filepath.replace('.h5', '_scaler.pkl')
        joblib.dump(self.scaler, scaler_path)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load model and scaler"""
        # Load model
        self.model = tf.keras.models.load_model(filepath)
        
        # Load scaler
        scaler_path = filepath.replace('.h5', '_scaler.pkl')
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
        
        self.is_trained = True
        logger.info(f"Model loaded from {filepath}")


class ModelTrainer:
    """Model training pipeline"""
    
    def __init__(self, symbol: str = 'BTCUSDT'):
        self.symbol = symbol
        self.model = None
        
    def load_data(self, db_connection) -> pd.DataFrame:
        """Load data from database"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from data.models import MarketData
        from sqlalchemy.orm import sessionmaker
        
        Session = sessionmaker(bind=db_connection)
        session = Session()
        
        try:
            # Query data
            data = session.query(MarketData).filter(
                MarketData.symbol == self.symbol.replace('/', '')
            ).order_by(MarketData.timestamp.asc()).all()
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': d.timestamp,
                'open_price': float(d.open_price),
                'high_price': float(d.high_price),
                'low_price': float(d.low_price),
                'close_price': float(d.close_price),
                'volume': float(d.volume)
            } for d in data])
            
            logger.info(f"Loaded {len(df)} records for {self.symbol}")
            return df
            
        finally:
            session.close()
    
    def train_model(self, df: pd.DataFrame, test_size: float = 0.2, val_size: float = 0.1):
        """Train LSTM model on data"""
        # Initialize model
        self.model = CryptoPriceLSTM()
        
        # Prepare data
        X, y = self.model.prepare_data(df)
        
        # Split data
        n_total = len(X)
        n_test = int(n_total * test_size)
        n_val = int(n_total * val_size)
        n_train = n_total - n_test - n_val
        
        X_train = X[:n_train]
        y_train = y[:n_train]
        X_val = X[n_train:n_train + n_val]
        y_val = y[n_train:n_train + n_val]
        X_test = X[n_train + n_val:]
        y_test = y[n_train + n_val:]
        
        logger.info(f"Training set: {len(X_train)}, Validation: {len(X_val)}, Test: {len(X_test)}")
        
        # Train model
        history = self.model.train(X_train, y_train, X_val, y_val, epochs=50)
        
        # Evaluate model
        metrics = self.model.evaluate(X_test, y_test)
        
        # Save model
        model_path = f"data/models/lstm_{self.symbol}_{datetime.now().strftime('%Y%m%d')}.h5"
        self.model.save_model(model_path)
        
        return history, metrics