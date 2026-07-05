import sys
import pandas as pd

class TerminalColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TerminalDashboard:
    """
    Module 5: Interface/Dashboard
    Orchestrates Modules 1, 2, and 3, printing a live, color-coded terminal dashboard.
    """
    def __init__(self):
        pass

    def run_live_dashboard(self):
        print(f"{TerminalColors.HEADER}{TerminalColors.BOLD}============================================================{TerminalColors.ENDC}")
        print(f"{TerminalColors.HEADER}{TerminalColors.BOLD}   4-PILLAR ALGORITHMIC PREDICTIVE ENGINE LIVE DASHBOARD    {TerminalColors.ENDC}")
        print(f"{TerminalColors.HEADER}{TerminalColors.BOLD}============================================================{TerminalColors.ENDC}")
        print(f"{TerminalColors.OKCYAN}[*] Starting Modules...{TerminalColors.ENDC}\n")

        # Dynamic imports to ensure dependencies are loaded at runtime
        try:
            from module1_data import DataIngestionPipeline
            from module2_features import FeatureEngineeringEngine
            from module3_predictive_risk import PredictiveRiskEngine
        except ImportError as e:
            print(f"{TerminalColors.FAIL}[!] Error importing modules: {e}{TerminalColors.ENDC}")
            print(f"{TerminalColors.FAIL}[!] Ensure module1_data.py, module2_features.py, and module3_predictive_risk.py are implemented.{TerminalColors.ENDC}")
            return

        # ---------------------------------------------------------
        # MODULE 1: Data Ingestion
        # ---------------------------------------------------------
        print(f"{TerminalColors.OKBLUE}[1] Running Data Ingestion (Module 1)...{TerminalColors.ENDC}")
        data_pipeline = DataIngestionPipeline()
        
        try:
            df = data_pipeline.fetch_15m_data(symbol="^NSEI", days=5)
        except Exception as e:
            print(f"{TerminalColors.FAIL}[!] Exception during fetch_15m_data: {e}{TerminalColors.ENDC}")
            return
        
        if df is None or df.empty:
            print(f"{TerminalColors.FAIL}[!] Failed to fetch data. DataFrame is empty.{TerminalColors.ENDC}")
            return
            
        print(f"{TerminalColors.OKGREEN}[+] Data Ingestion Successful. Fetched {len(df)} candles.{TerminalColors.ENDC}\n")
        
        # ---------------------------------------------------------
        # MODULE 2: Feature Engineering
        # ---------------------------------------------------------
        print(f"{TerminalColors.OKBLUE}[2] Running Feature Engineering (Module 2)...{TerminalColors.ENDC}")
        try:
            # Try initializing with the dataframe as per object-oriented design 
            feature_engine = FeatureEngineeringEngine(df)
        except TypeError:
            # Fallback if engine does not take df in constructor
            feature_engine = FeatureEngineeringEngine()
            if hasattr(feature_engine, 'df'):
                feature_engine.df = df
                
        # Execute feature calculations
        if hasattr(feature_engine, 'calculate_emas'):
            try:
                feature_engine.calculate_emas()
            except TypeError:
                feature_engine.calculate_emas(df)
                
        if hasattr(feature_engine, 'calculate_volume_spike'):
            try:
                feature_engine.calculate_volume_spike()
            except TypeError:
                feature_engine.calculate_volume_spike(df)
                
        if hasattr(feature_engine, 'calculate_price_action'):
            try:
                feature_engine.calculate_price_action()
            except TypeError:
                feature_engine.calculate_price_action(df)
                
        if hasattr(feature_engine, 'add_pcr_sentiment'):
            try:
                feature_engine.add_pcr_sentiment()
            except TypeError:
                feature_engine.add_pcr_sentiment(df)
            
        # Retrieve engineered df
        if hasattr(feature_engine, 'df'):
            engineered_df = feature_engine.df
        else:
            engineered_df = df

        print(f"{TerminalColors.OKGREEN}[+] Feature Engineering Complete.{TerminalColors.ENDC}\n")

        # ---------------------------------------------------------
        # MODULE 3 & 4: Predictive Risk Engine
        # ---------------------------------------------------------
        print(f"{TerminalColors.OKBLUE}[3] Running Predictive Risk Engine (Module 3 & 4)...{TerminalColors.ENDC}")
        try:
            risk_engine = PredictiveRiskEngine(engineered_df)
        except TypeError:
            risk_engine = PredictiveRiskEngine()
            if hasattr(risk_engine, 'df'):
                risk_engine.df = engineered_df

        # Evaluate the most recent 15-minute candle
        latest_row = engineered_df.iloc[-1]
        
        # Display the live candle data
        print(f"{TerminalColors.HEADER}--- LIVE 15-MINUTE CANDLE DATA ---{TerminalColors.ENDC}")
        close_price = latest_row.get('Close', 0.0)
        volume = latest_row.get('Volume', 0)
        pcr = latest_row.get('PCR', 0.0)
        
        close_str = f"{close_price:.2f}" if isinstance(close_price, (int, float)) else str(close_price)
        pcr_str = f"{pcr:.2f}" if isinstance(pcr, (int, float)) else str(pcr)
        
        print(f"Close: {TerminalColors.BOLD}{close_str}{TerminalColors.ENDC} | Volume: {TerminalColors.BOLD}{volume}{TerminalColors.ENDC} | PCR: {TerminalColors.BOLD}{pcr_str}{TerminalColors.ENDC}\n")

        # Evaluate 4 Pillars
        pillars_result = {}
        if hasattr(risk_engine, 'evaluate_pillars'):
            pillars_result = risk_engine.evaluate_pillars(latest_row)

        # Generate final trade signal
        signal = "NO TRADE (Choppy/Sideways Market)"
        if hasattr(risk_engine, 'generate_signal'):
            signal = risk_engine.generate_signal(latest_row)

        # Calculate Risk payload
        risk_payload = {}
        if hasattr(risk_engine, 'calculate_risk'):
            risk_payload = risk_engine.calculate_risk(latest_row, signal)
            
        # ---------------------------------------------------------
        # DISPLAY DASHBOARD RESULTS
        # ---------------------------------------------------------
        print(f"{TerminalColors.HEADER}--- 4 PILLARS STATUS ---{TerminalColors.ENDC}")
        if isinstance(pillars_result, dict) and pillars_result:
            for pillar_name, status in pillars_result.items():
                print(f"{pillar_name}: {TerminalColors.OKCYAN}{status}{TerminalColors.ENDC}")
        else:
            # Fallback if pillars are evaluated silently or returned as a non-dict
            print(f"{TerminalColors.WARNING}Pillars evaluated internally.{TerminalColors.ENDC}")
        print()

        print(f"{TerminalColors.HEADER}--- FINAL TRADE SIGNAL ---{TerminalColors.ENDC}")
        
        # Color coding logic for trade signal
        signal_upper = str(signal).upper()
        if "BUY CALL" in signal_upper or "CE" in signal_upper:
            signal_color = TerminalColors.OKGREEN
        elif "BUY PUT" in signal_upper or "PE" in signal_upper:
            signal_color = TerminalColors.FAIL
        else:
            signal_color = TerminalColors.WARNING

        print(f"Signal: {signal_color}{TerminalColors.BOLD}{signal}{TerminalColors.ENDC}")
        
        # Display Risk Output
        if isinstance(risk_payload, dict) and risk_payload:
            sl = risk_payload.get('Stop_Loss', risk_payload.get('stop_loss', 'N/A'))
            tg = risk_payload.get('Target', risk_payload.get('target', 'N/A'))
            
            if sl != 'N/A' and tg != 'N/A':
                sl_str = f"{sl:.2f}" if isinstance(sl, (int, float)) else str(sl)
                tg_str = f"{tg:.2f}" if isinstance(tg, (int, float)) else str(tg)
                print(f"Stop Loss: {TerminalColors.FAIL}{sl_str}{TerminalColors.ENDC}")
                print(f"Target:    {TerminalColors.OKGREEN}{tg_str}{TerminalColors.ENDC}")
            else:
                for k, v in risk_payload.items():
                    print(f"{k}: {v}")
                    
        print(f"\n{TerminalColors.HEADER}{TerminalColors.BOLD}============================================================{TerminalColors.ENDC}")


if __name__ == "__main__":
    try:
        dashboard = TerminalDashboard()
        dashboard.run_live_dashboard()
    except KeyboardInterrupt:
        print(f"\n{TerminalColors.WARNING}[!] Dashboard interrupted by user. Exiting.{TerminalColors.ENDC}")
        sys.exit(0)
