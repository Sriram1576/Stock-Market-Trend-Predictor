import pandas as pd
import json

class PredictiveRiskEngine:
    def __init__(self, df: pd.DataFrame = None):
        """
        Initialize the engine with an optional DataFrame.
        The DataFrame is expected to have engineered features from Module 2.
        """
        self.df = df

    def evaluate_pillars(self, row: pd.Series) -> dict:
        """
        Evaluates the 4 pillars for a given row (candle):
        - Pillar 1: EMA 8 > 13 > 21 (Bullish) or 8 < 13 < 21 (Bearish).
        - Pillar 2: Volume Spike == True.
        - Pillar 3: PCR Sentiment == Bullish or Bearish.
        - Pillar 4: Close > Swing_High (Bullish) or Close < Swing_Low (Bearish).
        """
        # Pillar 1
        bullish_p1 = (row.get('EMA_8', 0) > row.get('EMA_13', 0)) and (row.get('EMA_13', 0) > row.get('EMA_21', 0))
        bearish_p1 = (row.get('EMA_8', 0) < row.get('EMA_13', 0)) and (row.get('EMA_13', 0) < row.get('EMA_21', 0))
        
        # Pillar 2
        vol_spike = bool(row.get('Volume_Spike', False))
        
        # Pillar 3
        sentiment = str(row.get('PCR_Sentiment', '')).upper()
        bullish_p3 = (sentiment == 'BULLISH')
        bearish_p3 = (sentiment == 'BEARISH')
        
        # Pillar 4
        close_price = row.get('Close', 0)
        bullish_p4 = close_price > row.get('Swing_High', float('inf'))
        bearish_p4 = close_price < row.get('Swing_Low', -float('inf'))
        
        return {
            'bullish_p1': bullish_p1,
            'bearish_p1': bearish_p1,
            'p2_vol_spike': vol_spike,
            'bullish_p3': bullish_p3,
            'bearish_p3': bearish_p3,
            'bullish_p4': bullish_p4,
            'bearish_p4': bearish_p4
        }

    def generate_signal(self, row: pd.Series) -> str:
        """
        Requires at least 3 out of 4 pillars to align. 
        Outputs "BUY CALL (CE)" or "BUY PUT (PE)". Else "NO TRADE (Choppy/Sideways Market)".
        """
        pillars = self.evaluate_pillars(row)
        
        bullish_count = sum([pillars['bullish_p1'], pillars['p2_vol_spike'], pillars['bullish_p3'], pillars['bullish_p4']])
        bearish_count = sum([pillars['bearish_p1'], pillars['p2_vol_spike'], pillars['bearish_p3'], pillars['bearish_p4']])
        
        if bullish_count >= 3:
            return "BUY CALL (CE)"
        elif bearish_count >= 3:
            return "BUY PUT (PE)"
        else:
            return "NO TRADE (Choppy/Sideways Market)"

    def calculate_risk(self, row: pd.Series, signal: str) -> dict:
        """
        - If CE: Stop Loss = min(21_EMA, Prev_Low). Target = Entry + (Entry - Stop_Loss)*2.
        - If PE: Stop Loss = max(21_EMA, Prev_High). Target = Entry - (Stop_Loss - Entry)*2.
        """
        if signal == "NO TRADE (Choppy/Sideways Market)":
            return {"Stop_Loss": None, "Target": None, "Entry": row.get('Close')}
            
        entry = row.get('Close', 0)
        ema_21 = row.get('EMA_21', 0)
        
        # Try to find Prev_Low and Prev_High
        prev_low = row.get('Low', entry)
        prev_high = row.get('High', entry)
        
        # If Prev_Low/Prev_High were engineered as columns
        if 'Prev_Low' in row:
            prev_low = row['Prev_Low']
        if 'Prev_High' in row:
            prev_high = row['Prev_High']
            
        # Fallback to dataframe lookup if available
        if self.df is not None and hasattr(row, 'name') and row.name in self.df.index:
            try:
                # Using get_loc can return a slice or array if duplicates, so we handle safely
                loc = self.df.index.get_loc(row.name)
                if isinstance(loc, int) and loc > 0:
                    prev_low = self.df.iloc[loc - 1]['Low']
                    prev_high = self.df.iloc[loc - 1]['High']
            except Exception:
                pass
                
        if signal == "BUY CALL (CE)":
            stop_loss = min(ema_21, prev_low)
            target = entry + (entry - stop_loss) * 2
        elif signal == "BUY PUT (PE)":
            stop_loss = max(ema_21, prev_high)
            target = entry - (stop_loss - entry) * 2
        else:
            stop_loss = None
            target = None
            
        return {"Stop_Loss": stop_loss, "Target": target, "Entry": entry}

    def generate_payload(self, row: pd.Series = None) -> dict:
        """
        Returns a complete JSON/Dict payload for the execution signal.
        If row is None, processes the last row of the DataFrame.
        """
        if row is None:
            if self.df is not None and not self.df.empty:
                row = self.df.iloc[-1]
            else:
                return {}
                
        signal = self.generate_signal(row)
        risk = self.calculate_risk(row, signal)
        pillars = self.evaluate_pillars(row)
        
        payload = {
            "timestamp": str(row.name) if hasattr(row, 'name') else None,
            "signal": signal,
            "entry": risk.get("Entry"),
            "stop_loss": risk.get("Stop_Loss"),
            "target": risk.get("Target"),
            "pillars_evaluated": pillars
        }
        return payload
