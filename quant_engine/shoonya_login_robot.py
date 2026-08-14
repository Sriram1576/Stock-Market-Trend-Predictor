import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse, parse_qs
import pyotp
import time
import json
from dotenv import load_dotenv

def fast_fill(driver, element, value):
    element.click()
    time.sleep(0.1)
    element.clear()
    element.send_keys(value)
    time.sleep(0.1)

def scan_network_for_code(driver):
    try:
        logs = driver.get_log("performance")
        for entry in logs:
            try:
                message = json.loads(entry["message"])["message"]
                if message.get("method") == "Network.requestWillBeSent":
                    url = message.get("params", {}).get("request", {}).get("url", "")
                    if "code=" in url:
                        parsed = urlparse(url)
                        code = parse_qs(parsed.query).get("code", [None])[0]
                        if code:
                            return code
            except Exception:
                continue
    except Exception:
        pass
    return None

def get_oauth_token():
    load_dotenv(r'D:\Business\IIT project\.env')
    
    CLIENT_ID = os.getenv('SHOONYA_USER_ID')
    PASSWORD = os.getenv('SHOONYA_PASSWORD')
    TOTP_SECRET = os.getenv('SHOONYA_TOTP_KEY')
    API_KEY = os.getenv('SHOONYA_API_KEY')
    
    LOGIN_URL = f"https://api.shoonya.com/OAuthlogin/investor-entry-level/login?api_key={API_KEY}&route_to={CLIENT_ID}"
    
    options = webdriver.EdgeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Mask webdriver to bypass bot detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    driver = webdriver.Edge(options=options)
    # Execute CDP command to remove navigator.webdriver flag
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    
    wait = WebDriverWait(driver, 30)
    
    auth_code = None
    try:
        print(f"Robot waking up (Stealth Mode) and navigating to: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']")))
        time.sleep(2)
        
        all_inputs = driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']):not([type='checkbox']):not([type='radio'])")
        visible_inputs = [inp for inp in all_inputs if inp.is_displayed()]
        
        if len(visible_inputs) < 3:
            print(f"Error: Only found {len(visible_inputs)} inputs.")
            return None

        print("Injecting credentials...")
        fast_fill(driver, visible_inputs[0], CLIENT_ID)
        fast_fill(driver, visible_inputs[1], PASSWORD)
        
        otp_value = pyotp.TOTP(TOTP_SECRET).now()
        fast_fill(driver, visible_inputs[2], otp_value)
        
        print("Submitting form...")
        visible_inputs[2].send_keys(Keys.RETURN)
        
        time.sleep(1)
        try:
            btn = driver.find_element(By.XPATH, "//button[normalize-space()='LOGIN']")
            driver.execute_script("arguments[0].click();", btn)
        except Exception:
            pass

        print("Credentials submitted. Intercepting OAuth Access Token...")
        
        start = time.time()
        while True:
            auth_code = scan_network_for_code(driver)
            if auth_code:
                print(f"Auth Code successfully hijacked: {auth_code[:5]}...")
                break
                
            if time.time() - start > 15:
                print("Robot timed out. Capturing debug screenshot...")
                driver.save_screenshot("shoonya_debug5.png")
                break
            time.sleep(0.5)
            
    except Exception as e:
        print(f"Robot encountered an error: {e}")
    finally:
        driver.quit()
        
    return auth_code

if __name__ == '__main__':
    token = get_oauth_token()
    if token:
        print("Robot finished successfully.")
