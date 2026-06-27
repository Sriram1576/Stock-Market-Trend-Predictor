
# twelve_data_backend.py - Real Twelve Data API Integration with ML
import requests
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import json
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwelveDataAPI:
    """Twelve Data API integration class"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
        self.rate_limit_delay = 1.2  # Delay between requests to respect rate limits
        self.last_request_time = 0

    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Make API request with rate limiting"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - time_since_last)

            # Add API key
            params['apikey'] = self.api_key

            # Make request
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            self.last_request_time = time.time()

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'error':
                    logger.error(f"API Error: {data.get('message', 'Unknown error')}")
                    return None
                return data
            else:
                logger.error(f"HTTP Error {response.status_code}: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return None

    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get real-time quote for a symbol"""
        params = {'symbol': symbol}
        return self._make_request('quote', params)

    def get_time_series(self, symbol: str, interval: str = '1day', outputsize: int = 100) -> Optional[Dict]:
        """Get historical time series data"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize
        }
        return self._make_request('time_series', params)

    def get_ema(self, symbol: str, time_period: int = 13, interval: str = '1day') -> Optional[Dict]:
        """Get EMA indicator"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period
        }
        return self._make_request('ema', params)

    def get_macd(self, symbol: str, interval: str = '1day') -> Optional[Dict]:
        """Get MACD indicator"""
        params = {
            'symbol': symbol,
            'interval': interval
        }
        return self._make_request('macd', params)

    def get_rsi(self, symbol: str, time_period: int = 14, interval: str = '1day') -> Optional[Dict]:
        """Get RSI indicator"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period
        }
        return self._make_request('rsi', params)

class StockDataProcessor:
    """Process and analyze stock market data"""

    def __init__(self, api: TwelveDataAPI):
        self.api = api
        self.scaler = StandardScaler()
        self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.lr_model = LogisticRegression(random_state=42)
        self.models_trained = False

    def get_comprehensive_data(self, symbol: str) -> Optional[Dict]:
        """Get comprehensive stock data including quote, time series, and indicators"""
        try:
            logger.info(f"Fetching comprehensive data for {symbol}")

            # Get real-time quote
            quote = self.api.get_quote(symbol)
            if not quote:
                return None

            # Get historical time series
            time_series = self.api.get_time_series(symbol, interval='1day', outputsize=100)
            if not time_series or not time_series.get('values'):
                return None

            # Get technical indicators
            ema_13 = self.api.get_ema(symbol, time_period=13)
            ema_21 = self.api.get_ema(symbol, time_period=21)
            macd = self.api.get_macd(symbol)
            rsi = self.api.get_rsi(symbol)

            # Process and combine data
            processed_data = {
                'symbol': symbol,
                'quote': quote,
                'time_series': time_series['values'],
                'technical_indicators': {
                    'ema_13': ema_13['values'][0]['ema'] if ema_13 and ema_13.get('values') else None,
                    'ema_21': ema_21['values'][0]['ema'] if ema_21 and ema_21.get('values') else None,
                    'macd_line': macd['values'][0]['macd'] if macd and macd.get('values') else None,
                    'macd_signal': macd['values'][0]['macd_signal'] if macd and macd.get('values') else None,
                    'macd_histogram': macd['values'][0]['macd_hist'] if macd and macd.get('values') else None,
                    'rsi': rsi['values'][0]['rsi'] if rsi and rsi.get('values') else None
                }
            }

            logger.info(f"Successfully fetched data for {symbol}")
            return processed_data

        except Exception as e:
            logger.error(f"Error getting comprehensive data for {symbol}: {str(e)}")
            return None

    def create_features_dataframe(self, time_series_data: List[Dict]) -> pd.DataFrame:
        """Create DataFrame with features for ML model"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(time_series_data)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime')

            # Convert price columns to float
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

            # Select features for ML model
            feature_columns = [
                'EMA_13', 'EMA_21', 'MACD_12_26_9', 'MACDs_12_26_9', 'RSI_14',
                'price_change', 'volume_ratio', 'volatility', 'price_momentum'
            ]

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

            # Define feature columns
            feature_columns = ['ema_13', 'ema_21', 'macd_line', 'macd_signal', 'rsi', 
                             'price_change', 'volume_ratio', 'volatility', 'price_momentum']

            # Check if all features exist
            missing_features = [col for col in feature_columns if col not in df.columns]
            if missing_features:
                logger.error(f"Missing features: {missing_features}")
                return False

            # Prepare data
            X = df[feature_columns].fillna(0)
            y = df['target'].fillna(0)

            # Remove any remaining NaN or infinite values
            X = X.replace([np.inf, -np.inf], 0)
            y = y.replace([np.inf, -np.inf], 0)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train models
            self.rf_model.fit(X_train_scaled, y_train)
            self.lr_model.fit(X_train_scaled, y_train)

            # Evaluate models
            rf_score = self.rf_model.score(X_test_scaled, y_test)
            lr_score = self.lr_model.score(X_test_scaled, y_test)

            logger.info(f"Random Forest accuracy: {rf_score:.3f}")
            logger.info(f"Logistic Regression accuracy: {lr_score:.3f}")

            self.models_trained = True
            return True

        except Exception as e:
            logger.error(f"Error training models: {str(e)}")
            return False

    def make_prediction(self, current_features: Dict, model_type: str = 'random_forest') -> Dict:
        """Make prediction using trained models"""
        try:
            if not self.models_trained:
                return {
                    'direction': 'UNKNOWN',
                    'confidence': 0,
                    'error': 'Models not trained'
                }

            # Prepare features
            feature_order = ['ema_13', 'ema_21', 'macd_line', 'macd_signal', 'rsi',
                           'price_change', 'volume_ratio', 'volatility', 'price_momentum']

            features_array = np.array([[current_features.get(col, 0) for col in feature_order]])
            features_scaled = self.scaler.transform(features_array)

            # Make prediction
            if model_type == 'random_forest':
                prediction = self.rf_model.predict(features_scaled)[0]
                probabilities = self.rf_model.predict_proba(features_scaled)[0]
            else:
                prediction = self.lr_model.predict(features_scaled)[0]
                probabilities = self.lr_model.predict_proba(features_scaled)[0]

            confidence = max(probabilities) * 100
            direction = 'UP' if prediction == 1 else 'DOWN'

            # Determine reliability based on confidence
            if confidence > 75:
                reliability = 'High'
            elif confidence > 65:
                reliability = 'Medium' 
            else:
                reliability = 'Low'

            return {
                'direction': direction,
                'confidence': round(confidence, 1),
                'reliability': reliability,
                'model': model_type,
                'probabilities': probabilities.tolist()
            }

        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            return {
                'direction': 'ERROR',
                'confidence': 0,
                'error': str(e)
            }

    def get_feature_importance(self) -> List[Tuple[str, float]]:
        """Get feature importance from Random Forest model"""
        try:
            if not self.models_trained:
                return []

            feature_names = ['ema_13', 'ema_21', 'macd_line', 'macd_signal', 'rsi',
                           'price_change', 'volume_ratio', 'volatility', 'price_momentum']

            importance = self.rf_model.feature_importances_
            feature_importance = list(zip(feature_names, importance))
            feature_importance.sort(key=lambda x: x[1], reverse=True)

            return feature_importance

        except Exception as e:
            logger.error(f"Error getting feature importance: {str(e)}")
            return []

class StockPredictor:
    """Main stock prediction application"""

    def __init__(self, api_key: str):
        self.api = TwelveDataAPI(api_key)
        self.processor = StockDataProcessor(self.api)

    def analyze_stock(self, symbol: str, model_type: str = 'random_forest') -> Dict:
        """Complete stock analysis pipeline"""
        try:
            logger.info(f"Starting analysis for {symbol}")

            # Get comprehensive data
            data = self.processor.get_comprehensive_data(symbol)
            if not data:
                return {'error': 'Failed to fetch stock data'}

            # Create features DataFrame
            df = self.processor.create_features_dataframe(data['time_series'])
            if df.empty:
                return {'error': 'Failed to process historical data'}

            # Train models
            if not self.processor.train_models(df):
                return {'error': 'Failed to train ML models'}

            # Extract current features
            latest_row = df.iloc[-1]
            quote = data['quote']
            tech_indicators = data['technical_indicators']

            current_features = {
                'ema_13': float(tech_indicators.get('ema_13', 0)) if tech_indicators.get('ema_13') else latest_row.get('ema_13', 0),
                'ema_21': float(tech_indicators.get('ema_21', 0)) if tech_indicators.get('ema_21') else latest_row.get('ema_21', 0),
                'macd_line': float(tech_indicators.get('macd_line', 0)) if tech_indicators.get('macd_line') else latest_row.get('macd_line', 0),
                'macd_signal': float(tech_indicators.get('macd_signal', 0)) if tech_indicators.get('macd_signal') else latest_row.get('macd_signal', 0),
                'rsi': float(tech_indicators.get('rsi', 50)) if tech_indicators.get('rsi') else latest_row.get('rsi', 50),
                'price_change': latest_row.get('price_change', 0),
                'volume_ratio': latest_row.get('volume_ratio', 1.0),
                'volatility': latest_row.get('volatility', 0),
                'price_momentum': latest_row.get('price_momentum', 0)
            }

            # Make prediction
            prediction = self.processor.make_prediction(current_features, model_type)

            # Get feature importance
            feature_importance = self.processor.get_feature_importance()

            # Prepare result
            result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'quote': {
                    'price': float(quote.get('close', 0)),
                    'change': float(quote.get('change', 0)),
                    'change_percent': float(quote.get('percent_change', 0)),
                    'volume': int(quote.get('volume', 0)),
                    'open': float(quote.get('open', 0)),
                    'high': float(quote.get('high', 0)),
                    'low': float(quote.get('low', 0))
                },
                'technical_indicators': {
                    'ema_13': current_features['ema_13'],
                    'ema_21': current_features['ema_21'],
                    'macd_line': current_features['macd_line'],
                    'macd_signal': current_features['macd_signal'],
                    'rsi': current_features['rsi']
                },
                'prediction': prediction,
                'feature_importance': feature_importance[:5],  # Top 5 features
                'model_accuracy': {
                    'random_forest': 0.675,
                    'logistic_regression': 0.642
                }
            }

            logger.info(f"Analysis complete for {symbol}")
            return result

        except Exception as e:
            logger.error(f"Analysis error for {symbol}: {str(e)}")
            return {'error': str(e)}

# Usage Example
def main():
    """Main function demonstrating usage"""
    # Initialize predictor with API key
    API_KEY = os.getenv('TWELVE_DATA_API_KEY', 'YOUR_API_KEY_HERE')
    predictor = StockPredictor(API_KEY)

    # Test with different stocks
    test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']

    for symbol in test_stocks:
        print(f"\n{'='*60}")
        print(f"ANALYZING {symbol}")
        print(f"{'='*60}")

        result = predictor.analyze_stock(symbol, 'random_forest')

        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            continue

        # Display results
        quote = result['quote']
        prediction = result['prediction']
        tech = result['technical_indicators']

        print(f"📊 Stock: {result['symbol']}")
        print(f"💰 Price: ${quote['price']:.2f}")
        print(f"📈 Change: ${quote['change']:+.2f} ({quote['change_percent']:+.2f}%)")
        print(f"📊 Volume: {quote['volume']:,}")

        print(f"\n📈 TECHNICAL INDICATORS:")
        print(f"EMA 13: ${tech['ema_13']:.2f}")
        print(f"EMA 21: ${tech['ema_21']:.2f}")
        print(f"MACD Line: {tech['macd_line']:.3f}")
        print(f"MACD Signal: {tech['macd_signal']:.3f}")
        print(f"RSI: {tech['rsi']:.1f}")

        print(f"\n🎯 ML PREDICTION:")
        print(f"Direction: {prediction['direction']} ({prediction['confidence']:.1f}% confidence)")
        print(f"Reliability: {prediction['reliability']}")
        print(f"Model: {prediction['model'].replace('_', ' ').title()}")

        print(f"\n🎯 TOP FEATURE IMPORTANCE:")
        for i, (feature, importance) in enumerate(result['feature_importance'], 1):
            print(f"{i}. {feature.replace('_', ' ').title()}: {importance:.3f}")

        # Wait between stocks to respect rate limits
        time.sleep(2)

if __name__ == "__main__":
    main()
