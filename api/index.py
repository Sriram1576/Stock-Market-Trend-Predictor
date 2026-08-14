from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import math
from quant_engine.module1_data import DataIngestionPipeline
from quant_engine.module2_features import FeatureEngineeringEngine
from quant_engine.module3_predictive_risk import PredictiveRiskEngine

app = FastAPI()

# Allow frontend to fetch data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

data_pipeline = DataIngestionPipeline()

@app.get("/api/stock/{symbol}")
def get_stock_data(symbol: str):
    symbol = symbol.upper().strip()
    if not symbol.endswith('.NS'):
        symbol += '.NS'
        
    df = data_pipeline.fetch_15m_data(symbol, days=5)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Stock data not found on Angel One or rate limited.")
        
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
    risk_engine = PredictiveRiskEngine(engineered_df)
    latest_row = engineered_df.iloc[-1]
    
    close_price = float(latest_row.get('Close', 0))
    open_price = float(latest_row.get('Open', close_price))
    high_price = float(latest_row.get('High', close_price))
    low_price = float(latest_row.get('Low', close_price))
    volume = int(latest_row.get('Volume', 0))
    
    ema8 = float(latest_row.get('EMA_8', close_price))
    ema13 = float(latest_row.get('EMA_13', close_price))
    ema21 = float(latest_row.get('EMA_21', close_price))
    pcr = float(latest_row.get('PCR', 1.0))
    pcr_sentiment = latest_row.get('PCR_Sentiment', 'NEUTRAL')
    vol_spike = bool(latest_row.get('Volume_Spike', False))
    
    pillars_result = risk_engine.evaluate_pillars(latest_row) if hasattr(risk_engine, 'evaluate_pillars') else {}
    signal = risk_engine.generate_signal(latest_row) if hasattr(risk_engine, 'generate_signal') else "NO TRADE"
    risk_payload = risk_engine.calculate_risk(latest_row, signal) if hasattr(risk_engine, 'calculate_risk') else {}
    
    target = risk_payload.get('Target', risk_payload.get('target', 0))
    sl = risk_payload.get('Stop_Loss', risk_payload.get('stop_loss', 0))
    direction = "BULLISH" if "BUY CALL" in signal or "CE" in signal else ("BEARISH" if "BUY PUT" in signal or "PE" in signal else "NEUTRAL")
    
    def clean(val):
        if isinstance(val, float) and math.isnan(val): return 0
        return val

    # Generate historical candles for chart
    candles = []
    for idx, row in df.iterrows():
        candles.append({
            "time": str(idx),
            "open": clean(float(row['Open'])),
            "high": clean(float(row['High'])),
            "low": clean(float(row['Low'])),
            "close": clean(float(row['Close'])),
            "volume": clean(int(row['Volume']))
        })

    return {
        "name": symbol.replace('.NS', ''),
        "quote": {
            "price": clean(close_price),
            "open": clean(open_price),
            "high": clean(high_price),
            "low": clean(low_price),
            "change": round(clean(close_price) - clean(open_price), 2),
            "change_percent": round(((clean(close_price) - clean(open_price)) / clean(open_price)) * 100, 2) if clean(open_price) > 0 else 0,
            "volume": clean(volume)
        },
        "technical": {
            "ema8": clean(ema8),
            "ema13": clean(ema13),
            "ema21": clean(ema21),
            "pcr": clean(pcr),
            "pcr_sentiment": pcr_sentiment,
            "vol_spike": vol_spike,
            "trend": "Bullish" if clean(ema8) > clean(ema13) > clean(ema21) else ("Bearish" if clean(ema8) < clean(ema13) < clean(ema21) else "Sideways")
        },
        "prediction": {
            "signal_text": signal,
            "direction": direction,
            "pillars_aligned": str(pillars_result),
            "target": clean(float(target if target != 'N/A' else 0)),
            "stop_loss": clean(float(sl if sl != 'N/A' else 0))
        },
        "candles": candles
    }

if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
