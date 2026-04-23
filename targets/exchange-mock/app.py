"""
exchange-mock — simulates Exchange Autodiscover + EWS + OWA endpoints
Intentional flaws: NTLM banner exposed, Basic auth over HTTP, credential logging,
  Autodiscover leaks internal hostnames, EWS accepts any NTLM token
"""
import base64
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

CREDENTIALS = {"admin": "Admin1234!", "operator": "Password123"}
CAPTURED: list = []

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "exchange-mock"})

# Autodiscover — leaks internal FQDN and EWS URL
@app.route("/autodiscover/autodiscover.xml", methods=["GET", "POST"])
@app.route("/Autodiscover/Autodiscover.xml", methods=["GET", "POST"])
def autodiscover():
    xml = """<?xml version="1.0" encoding="utf-8"?>
<Autodiscover xmlns="http://schemas.microsoft.com/exchange/autodiscover/responseschema/2006">
  <Response>
    <User><DisplayName>Lab Exchange</DisplayName></User>
    <Account>
      <AccountType>email</AccountType>
      <Action>settings</Action>
      <Protocol>
        <Type>EXCH</Type>
        <Server>exchange-mock.lab.local</Server>
        <SSL>Off</SSL>
        <EwsUrl>http://exchange-mock/EWS/Exchange.asmx</EwsUrl>
        <OWAUrl>http://exchange-mock/owa</OWAUrl>
      </Protocol>
    </Account>
  </Response>
</Autodiscover>"""
    return Response(xml, content_type="application/xml")

# EWS — weak Basic auth, logs credentials
@app.route("/EWS/Exchange.asmx", methods=["GET", "POST"])
def ews():
    auth = request.headers.get("Authorization", "")
    if not auth:
        return Response("Unauthorized", status=401,
                        headers={"WWW-Authenticate": 'Basic realm="Exchange", NTLM'})
    if auth.startswith("Basic "):
        decoded = base64.b64decode(auth[6:]).decode("utf-8", errors="replace")
        CAPTURED.append({"endpoint": "EWS", "credential": decoded})
    return Response("<soap:Envelope/>", content_type="text/xml")

# OWA — credential harvest page
@app.route("/owa", methods=["GET"])
def owa_get():
    return Response("""
<html><body>
<form method="POST" action="/owa">
  <input name="username" placeholder="Domain\\Username">
  <input type="password" name="password">
  <button>Sign in</button>
</form></body></html>""", content_type="text/html")

@app.route("/owa", methods=["POST"])
def owa_post():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    CAPTURED.append({"endpoint": "OWA", "username": username, "password": password})
    expected = CREDENTIALS.get(username.split("\\")[-1])
    if expected and expected == password:
        return jsonify({"status": "authenticated", "user": username})
    return Response("Invalid credentials", status=401)

# Debug: dump captured credentials — intentional lab surface
@app.route("/debug/captured")
def captured():
    return jsonify(CAPTURED)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
