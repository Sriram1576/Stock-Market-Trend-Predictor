import yfinance as yf
import pandas as pd
import random

class DataIngestionPipeline:
    def __init__(self):
        pass

    def fetch_pcr(self):
        """
        Stub function returning a random float between 0.5 and 1.5 
        to simulate Put-Call Ratio (since live options data requires paid APIs).
        """
        return random.uniform(0.5, 1.5)

    def fetch_15m_data(self, symbol="^NSEI", days=5):
        """
        Fetches 15-minute OHLCV data using yfinance.
        Returns a clean Pandas DataFrame containing: Open, High, Low, Close, Volume, PCR.
        """
        period_str = f"{days}d"
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period_str, interval="15m")
        
        if df.empty:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume", "PCR"])
            
        # Select required columns (yfinance includes Dividends and Stock Splits by default)
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        
        # Add PCR column by calling the stub function for each row
        df["PCR"] = [self.fetch_pcr() for _ in range(len(df))]
        
        return df
