# dolla-avator
## Environment Variables

This app relies on a few environment variables for proper configuration. When you deploy the app (via the Heroku one‑click deploy button below), you’ll be prompted to set these variables. Below is a brief explanation of each:

- **ZAP_API_KEY**:  
  If your OWASP ZAP installation requires an API key, you can find or set it by navigating to **Tools > Options > API** within the ZAP application. If you do not use an API key, you can leave this value as `"changeme"` or blank.

- **ZAP_ADDRESS**:  
  This is the IP address or domain where your OWASP ZAP instance is running. For local testing, use `127.0.0.1`. If ZAP is running on another server, provide its address.

- **ZAP_PORT**:  
  The port on which OWASP ZAP is listening. The default is `8090` unless you have changed it in your ZAP configuration.

- **FLASK_SECRET_KEY**:  
  A secret key for managing Flask sessions. You can leave the default or change it to a more secure, random value.

When deploying on Heroku, simply click the button below and fill in the prompted values if you need to override the defaults.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/manybotts/dolla-avator)
