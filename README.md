# Dolla Avator Audit Tool

A user-friendly web app that simulates user interactions (login and gameplay) and performs vulnerability scanning using OWASP ZAP and Selenium.

## One-Click Heroku Deployment

Click the button below to deploy the app to Heroku. You will be prompted to configure some environment variables.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/manybotts/dolla-avator)

## Environment Variables

This app relies on a few environment variables for proper configuration. When you deploy, you’ll be prompted to set these values:

- **ZAP_API_KEY**:  
  If your OWASP ZAP installation requires an API key, you can find or set it by navigating to **Tools > Options > API** within ZAP. If not used, leave the default value (`changeme`).

- **ZAP_ADDRESS**:  
  The IP address or domain where your OWASP ZAP instance is running. For local testing, use `127.0.0.1`.

- **ZAP_PORT**:  
  The port on which OWASP ZAP is listening. The default is `8090`.

- **FLASK_SECRET_KEY**:  
  A secret key for managing Flask sessions. You can leave the default or change it to a more secure, random value.

## Running Locally

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
