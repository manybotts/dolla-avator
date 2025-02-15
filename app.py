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
ZAP_API_KEY = os.environ.get("ZAP_API_KEY", "changeme")  # Set in Heroku config if needed
ZAP_ADDRESS = os.environ.get("ZAP_ADDRESS", "127.0.0.1")
ZAP_PORT    = os.environ.get("ZAP_PORT", "8090")

# Initialize ZAP API client (using our own proxies configuration)
zap = ZAPv2(
    apikey=ZAP_API_KEY,
    proxies={
        'http': f'http://{ZAP_ADDRESS}:{ZAP_PORT}',
        'https': f'http://{ZAP_ADDRESS}:{ZAP_PORT}'
    }
)

def simulate_interaction(target, username, password):
    """
    Uses Selenium to open the target website, perform a login,
    and simulate playing the Aviator game.
    NOTE: Adjust element IDs and wait times according to your site's UI.
    """
    # Configure headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    # Use the CHROMEDRIVER_PATH provided by the "Chrome for Testing" buildpack.
    chrome_driver_path = os.environ.get("CHROMEDRIVER_PATH", "chromedriver")
    service = ChromeService(executable_path=chrome_driver_path)
    
    # Create the webdriver instance
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Open the target website
        driver.get(target)
        
        # Wait for login elements to appear (up to 10 seconds)
        wait = WebDriverWait(driver, 10)
        username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
        login_button = wait.until(EC.element_to_be_clickable((By.ID, "login_button")))
        
        # Enter credentials and log in
        username_field.clear()
        username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(password)
        login_button.click()
        
        # Wait for an element that appears only after login – e.g., the "play_button"
        wait.until(EC.presence_of_element_located((By.ID, "play_button")))
        
        # Simulate playing the Aviator game
        play_button = driver.find_element(By.ID, "play_button")
        play_button.click()
        time.sleep(1)  # Let the game start
        
        # Wait until the cashout button is clickable and then click it
        cashout_button = wait.until(EC.element_to_be_clickable((By.ID, "cashout_button")))
        cashout_button.click()
        time.sleep(1)  # Simulate cashing out
        
        print("Simulation completed successfully.")
        
    except Exception as e:
        print(f"Simulation encountered an error: {e}")
        flash(f"Simulation error: {e}", "danger")
    finally:
        driver.quit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        target_url = request.form.get('target_url')
        username   = request.form.get('username')
        password   = request.form.get('password')

        if not target_url or not username or not password:
            flash("Please provide all required information.", "warning")
            return redirect(url_for('index'))

        flash("Starting simulation of user interactions...", "info")
        simulate_interaction(target_url, username, password)
        
        flash("Starting vulnerability scan via OWASP ZAP. Please wait...", "info")
        # Ensure ZAP has loaded the target site by opening it via the API.
        zap.urlopen(target_url)
        time.sleep(2)

        # Start the Spider (crawling) scan.
        spider_id = zap.spider.scan(target_url)
        time.sleep(2)  # Let the spider start

        while int(zap.spider.status(spider_id)) < 100:
            print(f"Spider progress: {zap.spider.status(spider_id)}%")
            time.sleep(1)
        print("Spider scan completed.")

        # Start the Active scan.
        scan_id = zap.ascan.scan(target_url)
        while int(zap.ascan.status(scan_id)) < 100:
            print(f"Active scan progress: {zap.ascan.status(scan_id)}%")
            time.sleep(5)
        print("Active scan completed.")

        # Retrieve alerts (vulnerabilities) found by ZAP.
        alerts = zap.core.alerts(baseurl=target_url)
        flash("Scan completed.", "success")
        return render_template('results.html', target=target_url, alerts=alerts)
        
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
