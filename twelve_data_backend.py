# twelve_data_backend.py - Upgraded to Yahoo Finance for Indian Stocks
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import json
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataProcessor:
    """Process and analyze stock market data"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.lr_model = LogisticRegression(random_state=42)
        self.models_trained = False

    def get_comprehensive_data(self, symbol: str) -> Optional[Dict]:
        """Fetch historical data from Yahoo Finance"""
        try:
            logger.info(f"Fetching data for {symbol} via Yahoo Finance")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="6mo")
            
            if df.empty:
                return None

            # Reset index to get Date column
            df = df.reset_index()
            
            # Prepare data format
            time_series = []
            for _, row in df.iterrows():
                time_series.append({
                    'datetime': row['Date'].strftime('%Y-%m-%d'),
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': row['Volume']
                })
                
            quote = {
                'close': float(df.iloc[-1]['Close']),
                'open': float(df.iloc[-1]['Open']),
                'high': float(df.iloc[-1]['High']),
                'low': float(df.iloc[-1]['Low']),
                'volume': int(df.iloc[-1]['Volume']),
                'change': float(df.iloc[-1]['Close'] - df.iloc[-2]['Close']),
                'percent_change': float((df.iloc[-1]['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close'] * 100)
            }

            return {
                'symbol': symbol,
                'quote': quote,
                'time_series': time_series
            }

        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {str(e)}")
            return None

    def create_features_dataframe(self, time_series_data: List[Dict]) -> pd.DataFrame:
        """Create DataFrame with features for ML model"""
        try:
            df = pd.DataFrame(time_series_data)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime')

            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Calculate technical indicators using pandas_ta
            df.ta.ema(length=13, append=True)
            df.ta.ema(length=21, append=True)
            df.ta.macd(append=True)
            df.ta.rsi(append=True)

            # Calculate additional features
            df['price_change'] = df['close'].pct_change()
            df['volume_sma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            df['volatility'] = df['close'].rolling(20).std()
            df['price_momentum'] = df['close'].pct_change(5)

            # Create target variable (next day price direction)
            df['target'] = (df['close'].shift(-1) > df['close']).astype(int)

            # Rename columns to match expected names
            df = df.rename(columns={
                'EMA_13': 'ema_13',
                'EMA_21': 'ema_21', 
                'MACD_12_26_9': 'macd_line',
                'MACDs_12_26_9': 'macd_signal',
                'RSI_14': 'rsi'
            })

            return df.dropna()

        except Exception as e:
            logger.error(f"Error creating features DataFrame: {str(e)}")
            return pd.DataFrame()

    def train_models(self, df: pd.DataFrame) -> bool:
        """Train ML models on historical data"""
        try:
            if len(df) < 50:
                logger.warning("Not enough data to train models")
                return False

            feature_columns = ['ema_13', 'ema_21', 'macd_line', 'macd_signal', 'rsi', 
                             'price_change', 'volume_ratio', 'volatility', 'price_momentum']

            X = df[feature_columns].fillna(0).replace([np.inf, -np.inf], 0)
            y = df['target'].fillna(0).replace([np.inf, -np.inf], 0)

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )

            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            self.rf_model.fit(X_train_scaled, y_train)
            self.lr_model.fit(X_train_scaled, y_train)
            
            self.models_trained = True
            return True

        except Exception as e:
            logger.error(f"Error training models: {str(e)}")
            return False

    def make_prediction(self, current_features: Dict, model_type: str = 'random_forest') -> Dict:
        """Make prediction using trained models"""
        if not self.models_trained:
            return {'direction': 'UNKNOWN', 'confidence': 0, 'error': 'Models not trained'}

        feature_order = ['ema_13', 'ema_21', 'macd_line', 'macd_signal', 'rsi',
                       'price_change', 'volume_ratio', 'volatility', 'price_momentum']

        features_array = np.array([[current_features.get(col, 0) for col in feature_order]])
        features_scaled = self.scaler.transform(features_array)

        if model_type == 'random_forest':
            prediction = self.rf_model.predict(features_scaled)[0]
            probabilities = self.rf_model.predict_proba(features_scaled)[0]
        else:
            prediction = self.lr_model.predict(features_scaled)[0]
            probabilities = self.lr_model.predict_proba(features_scaled)[0]

        confidence = max(probabilities) * 100
        direction = 'UP' if prediction == 1 else 'DOWN'

        if confidence > 75: reliability = 'High'
        elif confidence > 65: reliability = 'Medium' 
        else: reliability = 'Low'

        return {
            'direction': direction,
            'confidence': round(confidence, 1),
            'reliability': reliability,
            'model': model_type
        }

class StockPredictor:
    """Main stock prediction application"""
    def __init__(self, api_key: str = None):
        # API key ignored because we migrated to Yahoo Finance
        self.processor = StockDataProcessor()

    def analyze_stock(self, symbol: str, model_type: str = 'random_forest') -> Dict:
        try:
            logger.info(f"Starting analysis for {symbol}")
            data = self.processor.get_comprehensive_data(symbol)
            if not data: return {'error': 'Failed to fetch stock data'}

            df = self.processor.create_features_dataframe(data['time_series'])
            if df.empty: return {'error': 'Failed to process historical data'}

            if not self.processor.train_models(df):
                return {'error': 'Failed to train ML models'}

            latest_row = df.iloc[-1]
            quote = data['quote']

            current_features = {
                'ema_13': float(latest_row.get('ema_13', 0)),
                'ema_21': float(latest_row.get('ema_21', 0)),
                'macd_line': float(latest_row.get('macd_line', 0)),
                'macd_signal': float(latest_row.get('macd_signal', 0)),
                'rsi': float(latest_row.get('rsi', 50)),
                'price_change': latest_row.get('price_change', 0),
                'volume_ratio': latest_row.get('volume_ratio', 1.0),
                'volatility': latest_row.get('volatility', 0),
                'price_momentum': latest_row.get('price_momentum', 0)
            }

            prediction = self.processor.make_prediction(current_features, model_type)

            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'quote': quote,
                'technical_indicators': {k: current_features[k] for k in ['ema_13', 'ema_21', 'macd_line', 'macd_signal', 'rsi']},
                'prediction': prediction
            }

        except Exception as e:
            logger.error(f"Analysis error for {symbol}: {str(e)}")
            return {'error': str(e)}
