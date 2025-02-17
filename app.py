import os
import time
from flask import Flask, render_template, request, redirect, url_for, flash
from zapv2 import ZAPv2
from playwright.sync_api import sync_playwright  # We'll still use Playwright for browser automation in this version

# Clear both uppercase and lowercase proxy environment variables.
os.environ["NO_PROXY"] = "*"
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supersecretkey')

# OWASP ZAP configuration from environment variables (or use defaults)
ZAP_API_KEY = os.environ.get("ZAP_API_KEY", "changeme")
ZAP_ADDRESS = os.environ.get("ZAP_ADDRESS", "127.0.0.1")
ZAP_PORT    = os.environ.get("ZAP_PORT", "8090")

# Initialize ZAP API client without any extra proxy settings.
zap = ZAPv2(
    apikey=ZAP_API_KEY,
    # We remove the explicit proxy configuration here so that the requests library doesn't force a proxy.
    # If your ZAP instance is running on localhost:8090 (the default), you can omit proxies.
)

def simulate_interaction(target, username, password):
    """
    Uses Playwright to automatically log in with provided credentials and simulate user actions.
    (Simulated login mode)
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(target)
            
            # Fill in the login form.
            page.fill("#username", username)
            page.fill("#password", password)
            page.click("#login_button")
            
            # Wait for an element that indicates successful login (adjust selector as needed).
            page.wait_for_selector("#play_button", timeout=10000)
            page.click("#play_button")
            time.sleep(1)  # Let the game start.
            page.click("#cashout_button")
            time.sleep(1)
            
            print("Simulated login and actions completed successfully.")
            browser.close()
    except Exception as e:
        print(f"Simulation encountered an error: {e}")
        flash(f"Simulation error: {e}", "danger")

def manual_login_interaction(target):
    """
    Uses Playwright to launch a non-headless browser window for manual login.
    After login is detected, the process waits for console input.
    (This mode is best for local testing.)
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto(target)
            
            print("A browser window has been opened. Please log in manually at the target site.")
            page.wait_for_selector("#play_button", timeout=300000)  # wait up to 5 minutes for login.
            input("Login detected. Press Enter in this console to continue with vulnerability scanning...")
            print("Manual login completed.")
            browser.close()
    except Exception as e:
        print(f"Manual login interaction error: {e}")
        flash(f"Manual login interaction error: {e}", "danger")

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
        try:
            zap.urlopen(target_url)
        except Exception as e:
            print(f"Error during zap.urlopen: {e}")
            flash(f"Error during zap.urlopen: {e}", "danger")
        
        time.sleep(2)
        
        # Spider scan
        try:
            spider_id = zap.spider.scan(target_url)
            time.sleep(2)
            while int(zap.spider.status(spider_id)) < 100:
                print(f"Spider progress: {zap.spider.status(spider_id)}%")
                time.sleep(1)
            print("Spider scan completed.")
        except Exception as e:
            print(f"Error during spider scan: {e}")
            flash(f"Error during spider scan: {e}", "danger")
        
        # Active scan
        try:
            scan_id = zap.ascan.scan(target_url)
            while int(zap.ascan.status(scan_id)) < 100:
                print(f"Active scan progress: {zap.ascan.status(scan_id)}%")
                time.sleep(5)
            print("Active scan completed.")
        except Exception as e:
            print(f"Error during active scan: {e}")
            flash(f"Error during active scan: {e}", "danger")
        
        try:
            alerts = zap.core.alerts(baseurl=target_url)
        except Exception as e:
            print(f"Error retrieving alerts: {e}")
            alerts = []
            flash(f"Error retrieving alerts: {e}", "danger")
        
        flash("Scan completed.", "success")
        return render_template('results.html', target=target_url, alerts=alerts)
        
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
