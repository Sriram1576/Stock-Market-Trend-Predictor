"""
Updated module1_data.py to use Angel One SmartAPI
"""

import os
import json
import urllib.request
import pandas as pd
from datetime import datetime, timedelta
import pyotp
from dotenv import load_dotenv
from SmartApi import SmartConnect

class DataIngestionPipeline:
    def __init__(self):
        load_dotenv(r'D:\Business\IIT project\.env')
        self.api = None
        self.token_map = {}
        
        self.login()
        self.load_tokens()
        
    def login(self):
        """Handle Angel One login gracefully."""
        try:
            api_key = os.getenv('ANGEL_API_KEY')
            user_id = os.getenv('ANGEL_USER_ID')
            pin = os.getenv('ANGEL_PIN')
            totp_secret = os.getenv('ANGEL_TOTP_SECRET')
            
            if not all([api_key, user_id, pin, totp_secret]):
                print("Error: Missing Angel One credentials in .env file.")
                return

            self.api = SmartConnect(api_key=api_key)
            totp = pyotp.TOTP(totp_secret).now()
            
            data = self.api.generateSession(user_id, pin, totp)
            if data['status']:
                print("Angel One Login Successful.")
            else:
                print(f"Angel One Login Failed: {data.get('message')}")
        except Exception as e:
            print(f"Exception during login: {e}")

    def load_tokens(self):
        """Download and cache the Angel One symbol tokens."""
        token_file = 'angel_tokens.json'
        
        # Download the file if it doesn't exist or is older than 1 day
        download = True
        if os.path.exists(token_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(token_file))
            if datetime.now() - file_time < timedelta(days=1):
                download = False
                
        if download:
            print("Downloading latest Angel One instrument tokens...")
            url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
            try:
                urllib.request.urlretrieve(url, token_file)
            except Exception as e:
                print(f"Failed to download tokens: {e}")
                
        # Load into dictionary for fast lookup
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        if item['exch_seg'] == 'NSE':
                            # Store by symbol (e.g., RELIANCE-EQ)
                            self.token_map[item['symbol']] = item['token']
            except Exception as e:
                print(f"Error reading token file: {e}")

    def get_token(self, symbol):
        """Map standard symbols to Angel One tokens."""
        # Convert Yahoo format (RELIANCE.NS) to Angel format (RELIANCE-EQ)
        if symbol.endswith('.NS'):
            angel_symbol = symbol.replace('.NS', '-EQ')
        else:
            angel_symbol = symbol + '-EQ' if not symbol.endswith('-EQ') else symbol
            
        return self.token_map.get(angel_symbol, None)

    def fetch_15m_data(self, symbol, days=5):
        """Fetch historical 15-minute candle data."""
        empty_df = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
        empty_df.index.name = 'Datetime'
        
        if not self.api:
            return empty_df
            
        token = self.get_token(symbol)
        if not token:
            print(f"Token not found for {symbol}")
            return empty_df
            
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Format dates for Angel API (yyyy-mm-dd hh:mm)
        from_date = start_time.strftime('%Y-%m-%d 09:00')
        to_date = end_time.strftime('%Y-%m-%d 15:30')
        
        historicParam = {
            "exchange": "NSE",
            "symboltoken": token,
            "interval": "FIFTEEN_MINUTE",
            "fromdate": from_date,
            "todate": to_date
        }
        
        try:
            res = self.api.getCandleData(historicParam)
            
            if res.get('status') and res.get('data'):
                # Data format: [timestamp, open, high, low, close, volume]
                df = pd.DataFrame(res['data'], columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
                
                # Clean up format
                df['Datetime'] = pd.to_datetime(df['Datetime'])
                df.set_index('Datetime', inplace=True)
                
                # Sort chronologically just in case
                df.sort_index(ascending=True, inplace=True)
                
                return df
            else:
                return empty_df
                
        except Exception as e:
            print(f"Error fetching 15m data for {symbol}: {e}")
            return empty_df

if __name__ == "__main__":
    pipeline = DataIngestionPipeline()
    df = pipeline.fetch_15m_data("RELIANCE.NS", days=2)
    print(df.head())
