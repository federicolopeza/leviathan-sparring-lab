"""
crAPI stub — routes enough surface for basic recon until full crAPI compose is wired.
Replace with real crAPI compose for full benchmark coverage.
"""
from flask import Flask, jsonify, request

app = Flask(__name__)

# Simulated users — BOLA/IDOR surface
USERS = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com", "balance": 500.0},
    2: {"id": 2, "name": "Bob",   "email": "bob@example.com",   "balance": 200.0},
}

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "crapi-stub"})

@app.route("/identity/api/v2/user/dashboard")
def dashboard():
    # BOLA: no auth check — returns any user by query param
    uid = int(request.args.get("id", 1))
    return jsonify(USERS.get(uid, {"error": "not found"}))

@app.route("/community/api/v2/community/posts/recent")
def posts():
    return jsonify({"posts": [{"id": 1, "author": "alice@example.com", "body": "Lab post"}]})

@app.route("/workshop/api/mechanic/receive_report", methods=["POST"])
def report():
    # SSRF surface — accepts url param without validation
    data = request.json or {}
    return jsonify({"status": "received", "echo": data.get("url", "")})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True)
