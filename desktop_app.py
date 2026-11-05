import webview
import base64
from pathlib import Path

APP_URL = "https://shopmobi-ei0e.onrender.com"

# Load the existing Shopmobi logo
logo_path = Path(__file__).parent / "FullLogo.png"

logo_html = ""

if logo_path.exists():
    logo_data = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
    logo_html = f'<img src="data:image/png;base64,{logo_data}" class="logo">'

SPLASH_SCREEN = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Shopmobi</title>

<style>
* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #071c19, #123d2c);
    color: white;
    font-family: Arial, sans-serif;
    text-align: center;
}}

.container {{
    width: 90%;
    max-width: 500px;
}}

.logo {{
    width: 130px;
    height: 130px;
    object-fit: contain;
    border-radius: 25px;
    margin-bottom: 20px;
}}

h1 {{
    font-size: 38px;
    margin: 5px;
}}

.tagline {{
    color: #b8d9c5;
    font-size: 17px;
    letter-spacing: 2px;
}}

.spinner {{
    width: 42px;
    height: 42px;
    border: 4px solid #ffffff30;
    border-top: 4px solid #40d98b;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 35px auto 20px;
}}

@keyframes spin {{
    to {{ transform: rotate(360deg); }}
}}

#status {{
    color: #d5e8dc;
    font-size: 15px;
}}

button {{
    display: none;
    margin: 25px auto;
    padding: 13px 35px;
    border: none;
    border-radius: 25px;
    background: #40d98b;
    color: #07301e;
    font-weight: bold;
    font-size: 15px;
    cursor: pointer;
}}
</style>
</head>

<body>
<div class="container">
    {logo_html}

    <h1>Shopmobi</h1>
    <div class="tagline">SHOPPING MADE EASY</div>

    <div class="spinner" id="spinner"></div>

    <p id="status">Connecting to Shopmobi...</p>

    <button id="retry" onclick="connect()">Try Again</button>
</div>

<script>
const appUrl = "{APP_URL}";

async function connect() {{
    const status = document.getElementById("status");
    const retry = document.getElementById("retry");
    const spinner = document.getElementById("spinner");

    retry.style.display = "none";
    spinner.style.display = "block";
    status.textContent = "Connecting to Shopmobi...";

    try {{
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 120000);

        await fetch(appUrl, {{
            method: "GET",
            mode: "no-cors",
            cache: "no-store",
            signal: controller.signal
        }});

        clearTimeout(timeout);

        status.textContent = "Opening your marketplace...";

        window.location.replace(appUrl);

    }} catch (error) {{
        spinner.style.display = "none";
        status.textContent =
            "Unable to connect. Please check your internet connection.";

        retry.style.display = "block";
    }}
}}

connect();
</script>
</body>
</html>
"""

if __name__ == "__main__":

    window = webview.create_window(
        title="Shopmobi - Shopping Made Easy",
        html=SPLASH_SCREEN,
        width=1400,
        height=900,
        min_size=(1000, 650),
        resizable=True,
        background_color="#071c19"
    )

    webview.start()


