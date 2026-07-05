import pandas as pd

class FeatureEngineeringEngine:
    def __init__(self, df: pd.DataFrame):
        """
        Inputs the DataFrame from Module 1.
        """
        self.df = df.copy()

    def calculate_emas(self):
        """
        Adds 'EMA_8', 'EMA_13', 'EMA_21'.
        """
        self.df['EMA_8'] = self.df['Close'].ewm(span=8, adjust=False).mean()
        self.df['EMA_13'] = self.df['Close'].ewm(span=13, adjust=False).mean()
        self.df['EMA_21'] = self.df['Close'].ewm(span=21, adjust=False).mean()
        return self.df

    def calculate_volume_spike(self):
        """
        Adds 'Vol_20_SMA' and a boolean column 'Volume_Spike' (Volume > 1.5 * Vol_20_SMA).
        """
        self.df['Vol_20_SMA'] = self.df['Volume'].rolling(window=20).mean()
        self.df['Volume_Spike'] = self.df['Volume'] > 1.5 * self.df['Vol_20_SMA']
        return self.df

    def calculate_price_action(self):
        """
        Adds 'Swing_High' and 'Swing_Low' columns using local rolling maximums/minimums (5-candle window).
        """
        self.df['Swing_High'] = self.df['High'].rolling(window=5).max()
        self.df['Swing_Low'] = self.df['Low'].rolling(window=5).min()
        return self.df

    def add_pcr_sentiment(self):
        """
        Categorizes PCR column into 'BULLISH' (>1.2), 'BEARISH' (<0.6), or 'NEUTRAL'.
        """
        def get_sentiment(pcr):
            if pd.isna(pcr):
                return 'NEUTRAL'
            if pcr > 1.2:
                return 'BULLISH'
            elif pcr < 0.6:
                return 'BEARISH'
            else:
                return 'NEUTRAL'

        if 'PCR' in self.df.columns:
            self.df['PCR_Sentiment'] = self.df['PCR'].apply(get_sentiment)
        return self.df

    def process_all_features(self):
        """
        Runs all feature engineering methods and returns the updated DataFrame.
        """
        self.calculate_emas()
        self.calculate_volume_spike()
        self.calculate_price_action()
        self.add_pcr_sentiment()
        return self.df
