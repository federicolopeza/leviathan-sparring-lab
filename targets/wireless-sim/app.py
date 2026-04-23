"""
wireless-sim — simulated captive portal / router admin panel
Intentional flaws: default admin:admin, credential logging,
leaked PSK in /api/config, no CSRF protection
"""
from flask import Flask, request, redirect, jsonify, session, Response

app = Flask(__name__)
app.secret_key = "wireless-lab-session-key-0001"

# Intentional: default credentials
ADMIN_CREDS = {"admin": "admin", "root": "root"}
# Intentional: PSK exposed in config endpoint
WIFI_CONFIG = {
    "ssid":      "LabWifi-5G",
    "psk":       "Password1234",
    "radius_secret": "radius-shared-secret-001",
    "channel":   6,
    "encryption":"WPA2-PSK",
}
CAPTURED: list = []

LOGIN_PAGE = """
<html><head><title>WiFi Portal — Lab</title></head><body>
<h2>Network Access — Please Sign In</h2>
<form method="POST" action="/login">
  <input name="username" placeholder="Username" value="admin"><br>
  <input type="password" name="password" placeholder="Password"><br>
  <button>Connect</button>
</form>
<p style="font-size:0.8em">Default: admin/admin</p>
</body></html>"""

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "wireless-sim"})

@app.route("/")
def index():
    return Response(LOGIN_PAGE, content_type="text/html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return Response(LOGIN_PAGE, content_type="text/html")
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    CAPTURED.append({"username": username, "password": password, "ip": request.remote_addr})
    if ADMIN_CREDS.get(username) == password:
        session["user"] = username
        return redirect("/admin")
    return Response("Invalid credentials — <a href='/'>Try again</a>", content_type="text/html")

@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/")
    return jsonify({"message": "Admin panel", "config": WIFI_CONFIG, "clients": CAPTURED})

@app.route("/api/config")
def api_config():
    # Intentional: no auth — PSK and RADIUS secret exposed
    return jsonify(WIFI_CONFIG)

@app.route("/api/captured")
def api_captured():
    # Intentional: no auth — all harvested credentials exposed
    return jsonify(CAPTURED)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
