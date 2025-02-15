import os
import time
from flask import Flask, render_template, request, redirect, url_for, flash
from zapv2 import ZAPv2

# For Selenium automation
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Ensure no proxy settings are used
os.environ["NO_PROXY"] = "*"
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supersecretkey')

# Read OWASP ZAP configuration from environment variables (or use defaults)
ZAP_API_KEY = os.environ.get("ZAP_API_KEY", "changeme")
ZAP_ADDRESS = os.environ.get("ZAP_ADDRESS", "127.0.0.1")
ZAP_PORT    = os.environ.get("ZAP_PORT", "8090")

# Initialize ZAP API client
zap = ZAPv2(
    apikey=ZAP_API_KEY,
    proxies={
        'http': f'http://{ZAP_ADDRESS}:{ZAP_PORT}',
        'https': f'http://{ZAP_ADDRESS}:{ZAP_PORT}'
    }
)

def get_chrome_options(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    # Attempt to get the Chrome binary from the environment variable
    chrome_bin = os.environ.get("GOOGLE_CHROME_BIN")
    if not chrome_bin:
        # If running on Heroku, the buildpack should set this!
        if os.environ.get("DYNO"):
            raise Exception("GOOGLE_CHROME_BIN is not set. Ensure that the Chrome for Testing buildpack is installed and configured correctly.")
        else:
            # For local testing, you can set a fallback (adjust this as needed)
            chrome_bin = "/usr/bin/google-chrome"
            print("GOOGLE_CHROME_BIN not set; falling back to:", chrome_bin)
    chrome_options.binary_location = chrome_bin
    return chrome_options

def get_webdriver(headless=True):
    chrome_options = get_chrome_options(headless)
    chrome_driver_path = os.environ.get("CHROMEDRIVER_PATH", "chromedriver")
    service = ChromeService(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def simulate_interaction(target, username, password):
    """
    Automatically logs in with provided credentials and simulates actions.
    (Simulated login mode)
    """
    driver = get_webdriver(headless=True)
    
    try:
        driver.get(target)
        wait = WebDriverWait(driver, 10)
        username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
        login_button   = wait.until(EC.element_to_be_clickable((By.ID, "login_button")))
        
        username_field.clear()
        username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(password)
        login_button.click()
        
        wait.until(EC.presence_of_element_located((By.ID, "play_button")))
        play_button = driver.find_element(By.ID, "play_button")
        play_button.click()
        time.sleep(1)
        cashout_button = wait.until(EC.element_to_be_clickable((By.ID, "cashout_button")))
        cashout_button.click()
        time.sleep(1)
        print("Simulated login and actions completed successfully.")
        
    except Exception as e:
        print(f"Simulation encountered an error: {e}")
        flash(f"Simulation error: {e}", "danger")
    finally:
        driver.quit()

def manual_login_interaction(target):
    """
    Launches a visible browser window (non-headless) for manual login.
    You are expected to log in yourself. Once the post-login element
    (e.g., 'play_button') is detected, press Enter in the console to continue.
    """
    driver = get_webdriver(headless=False)
    
    try:
        driver.get(target)
        wait = WebDriverWait(driver, 300)  # wait up to 5 minutes for manual login
        print("A browser window has been opened. Please log in manually at the target site.")
        wait.until(EC.presence_of_element_located((By.ID, "play_button")))
        input("Login detected. Press Enter in this console to continue with vulnerability scanning...")
        print("Manual login completed.")
    except Exception as e:
        print(f"Manual login interaction error: {e}")
        flash(f"Manual login interaction error: {e}", "danger")
    finally:
        driver.quit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        target_url = request.form.get('target_url')
        manual_mode = request.form.get('manual_mode')  # "on" if manual login mode is selected
        
        if not target_url:
            flash("Please provide a target URL.", "warning")
            return redirect(url_for('index'))
        
        if manual_mode == "on":
            flash("Launching browser for manual login. Please log in using your browser window.", "info")
            manual_login_interaction(target_url)
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                flash("Please provide username and password for simulated login.", "warning")
                return redirect(url_for('index'))
            flash("Starting simulated login...", "info")
            simulate_interaction(target_url, username, password)
        
        flash("Starting vulnerability scan via OWASP ZAP. Please wait...", "info")
        zap.urlopen(target_url)
        time.sleep(2)
        
        spider_id = zap.spider.scan(target_url)
        time.sleep(2)
        while int(zap.spider.status(spider_id)) < 100:
            print(f"Spider progress: {zap.spider.status(spider_id)}%")
            time.sleep(1)
        print("Spider scan completed.")
        
        scan_id = zap.ascan.scan(target_url)
        while int(zap.ascan.status(scan_id)) < 100:
            print(f"Active scan progress: {zap.ascan.status(scan_id)}%")
            time.sleep(5)
        print("Active scan completed.")
        
        alerts = zap.core.alerts(baseurl=target_url)
        flash("Scan completed.", "success")
        return render_template('results.html', target=target_url, alerts=alerts)
        
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
