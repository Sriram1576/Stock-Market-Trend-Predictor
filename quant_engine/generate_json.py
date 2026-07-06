import os
import sys
import json
from datetime import datetime
import pandas as pd

# Add current dir to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from module1_data import DataIngestionPipeline
from module2_features import FeatureEngineeringEngine
from module3_predictive_risk import PredictiveRiskEngine

def generate_predictions():
    stocks = {
        'RELIANCE.NS': 'Reliance Industries',
        'TCS.NS': 'Tata Consultancy Services',
        'INFY.NS': 'Infosys Limited',
        'HDFCBANK.NS': 'HDFC Bank Limited',
        'ICICIBANK.NS': 'ICICI Bank Limited',
        'SBIN.NS': 'State Bank of India',
        'BHARTIARTL.NS': 'Bharti Airtel',
        'ITC.NS': 'ITC Limited'
    }

    results = {}
    data_pipeline = DataIngestionPipeline()

    for symbol in stocks.keys():
        print(f"Processing {symbol}...")
        try:
            df = data_pipeline.fetch_15m_data(symbol=symbol, days=5)
            if df is None or df.empty:
                continue

            # Feature Engineering
            feature_engine = FeatureEngineeringEngine(df)
            try: feature_engine.calculate_emas()
            except: feature_engine.calculate_emas(df)
            try: feature_engine.calculate_volume_spike()
            except: feature_engine.calculate_volume_spike(df)
            try: feature_engine.calculate_price_action()
            except: feature_engine.calculate_price_action(df)
            try: feature_engine.add_pcr_sentiment()
            except: feature_engine.add_pcr_sentiment(df)

            engineered_df = getattr(feature_engine, 'df', df)
            
            # Predictive Risk
            risk_engine = PredictiveRiskEngine(engineered_df)
            latest_row = engineered_df.iloc[-1]
            
            # Format outputs for frontend JSON schema
            close_price = float(latest_row.get('Close', 0))
            open_price = float(latest_row.get('Open', close_price))
            high_price = float(latest_row.get('High', close_price))
            low_price = float(latest_row.get('Low', close_price))
            volume = int(latest_row.get('Volume', 0))
            
            # EMA calculations
            ema8 = float(latest_row.get('EMA_8', close_price))
            ema13 = float(latest_row.get('EMA_13', close_price))
            ema21 = float(latest_row.get('EMA_21', close_price))
            
            # PCR & Volume Spikes
            pcr = float(latest_row.get('PCR', 1.0))
            pcr_sentiment = latest_row.get('PCR_Sentiment', 'NEUTRAL')
            vol_spike = bool(latest_row.get('Volume_Spike', False))

            # Final Signals
            pillars_result = risk_engine.evaluate_pillars(latest_row) if hasattr(risk_engine, 'evaluate_pillars') else {}
            signal = risk_engine.generate_signal(latest_row) if hasattr(risk_engine, 'generate_signal') else "NO TRADE"
            risk_payload = risk_engine.calculate_risk(latest_row, signal) if hasattr(risk_engine, 'calculate_risk') else {}

            target = risk_payload.get('Target', risk_payload.get('target', 'N/A'))
            sl = risk_payload.get('Stop_Loss', risk_payload.get('stop_loss', 'N/A'))
            if target == 'N/A' or target is None: target = 0
            if sl == 'N/A' or sl is None: sl = 0

            # Map signal string back to direction
            direction = "BULLISH" if "BUY CALL" in signal or "CE" in signal else ("BEARISH" if "BUY PUT" in signal or "PE" in signal else "NEUTRAL")

            results[symbol] = {
                "quote": {
                    "price": close_price,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "change": round(close_price - open_price, 2),
                    "change_percent": round(((close_price - open_price) / open_price) * 100, 2) if open_price > 0 else 0,
                    "volume": volume
                },
                "technical": {
                    "ema8": ema8,
                    "ema13": ema13,
                    "ema21": ema21,
                    "pcr": pcr,
                    "pcr_sentiment": pcr_sentiment,
                    "vol_spike": vol_spike,
                    "trend": "Bullish" if ema8 > ema13 > ema21 else ("Bearish" if ema8 < ema13 < ema21 else "Sideways")
                },
                "prediction": {
                    "signal_text": signal,
                    "direction": direction,
                    "pillars_aligned": str(pillars_result),
                    "target": float(target),
                    "stop_loss": float(sl)
                }
            }
        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    # Ensure parent dir exists
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Save results
    output_file = os.path.join(data_dir, 'daily_predictions.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✅ Generated predictions for {len(results)} stocks and saved to {output_file}")

if __name__ == "__main__":
    generate_predictions()
