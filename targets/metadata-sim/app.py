"""
metadata-sim — simulates AWS EC2 IMDSv1 at http://169.254.169.254/latest/
Intentional: IMDSv2 not enforced (no PUT /latest/api/token requirement),
fake IAM credentials available at /latest/meta-data/iam/security-credentials/lab-role
"""
import time
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

# Fake IAM credentials (intentional: lab-use simulated key format)
FAKE_CREDS = {
    "Code":            "Success",
    "LastUpdated":     "2026-04-23T00:00:00Z",
    "Type":            "AWS-HMAC",
    "AccessKeyId":     "ASIA_LAB_FAKEKEY_00001",
    "SecretAccessKey": "lab/FakeSecretKey+000000000000000000000001",
    "Token":           "lab-session-token-0000000000000000000000000000000000001",
    "Expiration":      "2099-12-31T23:59:59Z",
}

METADATA = {
    "instance-id":       "i-lab000000000001",
    "instance-type":     "t2.micro",
    "local-ipv4":        "10.0.1.100",
    "public-ipv4":       "203.0.113.1",
    "ami-id":            "ami-lab00000001",
    "hostname":          "ip-10-0-1-100.ec2.internal",
    "placement/availability-zone": "us-east-1a",
    "security-groups":   "lab-sg-allow-all",
}

@app.route("/latest/meta-data/")
def meta_root():
    keys = list(METADATA.keys()) + ["iam/"]
    return Response("\n".join(keys), content_type="text/plain")

@app.route("/latest/meta-data/<path:key>")
def meta_data(key):
    if key == "iam/" or key == "iam/security-credentials/":
        return Response("lab-role", content_type="text/plain")
    if key == "iam/security-credentials/lab-role":
        return jsonify(FAKE_CREDS)
    val = METADATA.get(key)
    if val:
        return Response(val, content_type="text/plain")
    return Response("", status=404)

@app.route("/latest/user-data")
def user_data():
    # Intentional: user-data contains a script with a hardcoded secret
    return Response(
        "#!/bin/bash\n# Startup script\nexport DB_PASSWORD=lab-prod-db-password-001\n",
        content_type="text/plain"
    )

@app.route("/latest/dynamic/instance-identity/document")
def identity():
    return jsonify({
        "accountId":    "123456789012",
        "region":       "us-east-1",
        "instanceId":   "i-lab000000000001",
        "instanceType": "t2.micro",
    })

@app.route("/")
def root():
    return Response("latest/\n", content_type="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
