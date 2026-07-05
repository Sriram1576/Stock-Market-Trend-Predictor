# 4-Pillar Algorithmic Predictive Engine Architecture

All code must be placed in `D:\IIT project\quant_engine\`.
Use `yfinance` and `pandas` for all data handling.

## Module 1: Data Ingestion (`module1_data.py`)
**Class `DataIngestionPipeline`**
- `fetch_15m_data(symbol="^NSEI", days=5)`: Fetches 15-minute OHLCV data using `yfinance`.
- `fetch_pcr()`: Stub function returning a random float between 0.5 and 1.5 to simulate Put-Call Ratio (since live options data requires paid APIs).
- Returns a clean Pandas DataFrame containing: Open, High, Low, Close, Volume, PCR.

## Module 2: Feature Engineering (`module2_features.py`)
**Class `FeatureEngineeringEngine`**
- Inputs the DataFrame from Module 1.
- `calculate_emas()`: Adds 'EMA_8', 'EMA_13', 'EMA_21'.
- `calculate_volume_spike()`: Adds 'Vol_20_SMA' and a boolean column 'Volume_Spike' (Volume > 1.5 * Vol_20_SMA).
- `calculate_price_action()`: Adds 'Swing_High' and 'Swing_Low' columns using local rolling maximums/minimums (e.g., 5-candle window).
- `add_pcr_sentiment()`: Categorizes PCR column into 'BULLISH' (>1.2), 'BEARISH' (<0.6), or 'NEUTRAL'.

## Module 3 & 4: Predictive Voting & Risk (`module3_predictive_risk.py`)
**Class `PredictiveRiskEngine`**
- Inputs the engineered DataFrame.
- `evaluate_pillars(row)`: Evaluates the 4 pillars for a given row (candle):
  - Pillar 1: EMA 8 > 13 > 21 (Bullish) or 8 < 13 < 21 (Bearish).
  - Pillar 2: Volume Spike == True.
  - Pillar 3: PCR Sentiment == Bullish or Bearish.
  - Pillar 4: Close > Swing_High (Bullish) or Close < Swing_Low (Bearish).
- `generate_signal(row)`: Requires at least 3 out of 4 pillars to align. Outputs "BUY CALL (CE)" or "BUY PUT (PE)". Else "NO TRADE (Choppy/Sideways Market)".
- `calculate_risk(row, signal)`:
  - If CE: Stop Loss = min(21_EMA, Prev_Low). Target = Entry + (Entry - Stop_Loss)*2.
  - If PE: Stop Loss = max(21_EMA, Prev_High). Target = Entry - (Stop_Loss - Entry)*2.
- Returns a complete JSON/Dict payload for the execution signal.

## Module 5: Interface/Dashboard (`module5_dashboard.py`)
**Class `TerminalDashboard`**
- `run_live_dashboard()`: Orchestrates Modules 1, 2, and 3.
- Prints a beautiful, color-coded terminal output showing the live 15-minute candle data, the status of the 4 Pillars, and the final trade signal with Stop Loss and Target.
