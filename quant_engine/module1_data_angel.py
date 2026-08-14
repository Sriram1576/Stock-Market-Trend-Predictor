import os
import pyotp
import pandas as pd
from dotenv import load_dotenv
from SmartApi import SmartConnect

def connect_angel_one():
    # Load credentials from .env
    load_dotenv(r'D:\Business\IIT project\.env')
    
    API_KEY = os.getenv('ANGEL_API_KEY')
    USER_ID = os.getenv('ANGEL_USER_ID')
    PIN = os.getenv('ANGEL_PIN')
    TOTP_SECRET = os.getenv('ANGEL_TOTP_SECRET')
    
    if not all([API_KEY, USER_ID, PIN, TOTP_SECRET]):
        print("Error: Missing Angel One credentials in .env file.")
        print("Please ensure ANGEL_API_KEY, ANGEL_USER_ID, ANGEL_PIN, and ANGEL_TOTP_SECRET are set.")
        return None
        
    print(f"Connecting to Angel One SmartAPI as user {USER_ID}...")
    
    try:
        # Initialize SmartAPI
        smartApi = SmartConnect(api_key=API_KEY)
        
        # Generate current TOTP code
        totp = pyotp.TOTP(TOTP_SECRET).now()
        
        # Log in
        data = smartApi.generateSession(USER_ID, PIN, totp)
        
        if data['status']:
            print("Successfully connected to Angel One!")
            return smartApi
        else:
            print(f"Login Failed: {data.get('message', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"Connection error: {e}")
        return None

if __name__ == "__main__":
    api = connect_angel_one()
    if api:
        print("Ready to pull historical data!")
