"""
oauth-lab — deliberately vulnerable OAuth2 authorization server
Intentional flaws: implicit flow, no PKCE, open redirect, weak JWKS, token in URL fragment logged
"""
import time, secrets, jwt
from flask import Flask, request, redirect, jsonify, render_template_string

app = Flask(__name__)

# Weak, hardcoded signing secret (intentional)
JWT_SECRET = "lab-oauth-weak-secret-0000000001"
JWT_ALGO   = "HS256"

# Registered clients — overly broad redirect_uri (intentional)
CLIENTS = {
    "lab-client": {
        "secret":        "lab-client-secret",
        "redirect_uris": ["*"],          # intentional: wildcard — no validation
        "allowed_scopes": ["openid", "profile", "email", "admin"],
    }
}

# In-memory auth codes + access tokens
AUTH_CODES: dict = {}
TOKENS: dict     = {}

AUTHORIZE_TEMPLATE = """
<html><body>
<h2>Lab OAuth2 — Authorize</h2>
<form method="POST">
  <input type="hidden" name="client_id"     value="{{ client_id }}">
  <input type="hidden" name="redirect_uri"  value="{{ redirect_uri }}">
  <input type="hidden" name="response_type" value="{{ response_type }}">
  <input type="hidden" name="state"         value="{{ state }}">
  <input type="hidden" name="scope"         value="{{ scope }}">
  <label>Username: <input name="username" value="admin"></label><br>
  <label>Password: <input type="password" name="password" value="admin"></label><br>
  <button type="submit">Approve</button>
</form></body></html>
"""

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "oauth-lab"})

@app.route("/authorize", methods=["GET", "POST"])
def authorize():
    client_id     = request.values.get("client_id", "")
    redirect_uri  = request.values.get("redirect_uri", "")
    response_type = request.values.get("response_type", "code")
    state         = request.values.get("state", "")
    scope         = request.values.get("scope", "openid")

    # Intentional: no redirect_uri validation — open redirect
    client = CLIENTS.get(client_id)
    if not client:
        return "Unknown client", 400

    if request.method == "GET":
        return render_template_string(AUTHORIZE_TEMPLATE, **request.args.to_dict(),
                                      client_id=client_id, redirect_uri=redirect_uri,
                                      response_type=response_type, state=state, scope=scope)

    username = request.form.get("username", "")
    # Intentional: accepts any credentials
    if response_type == "token":
        # Implicit flow: token delivered in URL fragment — logged by browsers/proxies
        token = jwt.encode({"sub": username, "scope": scope, "iat": int(time.time()),
                            "exp": int(time.time()) + 3600}, JWT_SECRET, algorithm=JWT_ALGO)
        return redirect(f"{redirect_uri}#access_token={token}&token_type=bearer&state={state}")
    else:
        code = secrets.token_hex(8)
        AUTH_CODES[code] = {"username": username, "scope": scope, "client_id": client_id}
        return redirect(f"{redirect_uri}?code={code}&state={state}")

@app.route("/token", methods=["POST"])
def token():
    code      = request.form.get("code", "")
    client_id = request.form.get("client_id", "")
    # Intentional: no client_secret verification
    entry = AUTH_CODES.pop(code, None)
    if not entry:
        return jsonify({"error": "invalid_grant"}), 400
    access_token = jwt.encode({"sub": entry["username"], "scope": entry["scope"],
                               "iat": int(time.time()), "exp": int(time.time()) + 3600},
                              JWT_SECRET, algorithm=JWT_ALGO)
    return jsonify({"access_token": access_token, "token_type": "bearer", "expires_in": 3600})

@app.route("/.well-known/jwks.json")
def jwks():
    # Intentional: JWKS exposes the raw secret (symmetric — algorithm confusion attack surface)
    return jsonify({"keys": [{"kty": "oct", "k": JWT_SECRET, "alg": "HS256", "use": "sig"}]})

@app.route("/userinfo")
def userinfo():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO, "none"])
        return jsonify({"sub": payload["sub"], "email": f"{payload['sub']}@lab.local"})
    except Exception as e:
        return jsonify({"error": str(e)}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5100, debug=True)
