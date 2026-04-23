"""
saml-target — deliberately vulnerable SAML 2.0 SP
Intentional flaws: accepts unsigned assertions, no audience restriction, XXE via lxml
"""
import base64, zlib
from flask import Flask, request, redirect, jsonify, session
from lxml import etree

app = Flask(__name__)
app.secret_key = "lab-saml-session-key-weak-0000001"

SAML_SETTINGS = {
    "strict": False,                     # Intentional: strict=False skips signature check
    "debug": True,
    "sp": {
        "entityId":     "http://saml-target:5200/",
        "assertionConsumerService": {"url": "http://saml-target:5200/acs", "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"},
        "singleLogoutService":      {"url": "http://saml-target:5200/sls", "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"},
        "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
        "x509cert": "",
        "privateKey": "",
    },
    "idp": {
        "entityId":    "http://idp.lab.local/",
        "singleSignOnService": {"url": "http://idp.lab.local/sso", "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"},
        "x509cert": "",   # Intentional: no IdP cert — signature not verified
    },
    "security": {
        "authnRequestsSigned":     False,
        "wantAssertionsSigned":    False,  # Intentional: accepts unsigned assertions
        "wantMessagesSigned":      False,
        "wantAssertionsEncrypted": False,
        "signatureAlgorithm":      "http://www.w3.org/2000/09/xmldsig#rsa-sha1",
    }
}

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "saml-target"})

@app.route("/")
def index():
    user = session.get("user")
    if user:
        return jsonify({"authenticated": True, "user": user})
    return redirect("/login")

@app.route("/login")
def login():
    return jsonify({"sso_url": "http://idp.lab.local/sso?SAMLRequest=...", "note": "Use /acs with POST to bypass IdP"})

@app.route("/acs", methods=["POST"])
def acs():
    # Intentional: parse SAMLResponse with lxml without XXE protection
    saml_b64 = request.form.get("SAMLResponse", "")
    try:
        xml_bytes = base64.b64decode(saml_b64)
        # XXE: external entity expansion not disabled
        parser = etree.XMLParser(resolve_entities=True, load_dtd=True)
        root   = etree.fromstring(xml_bytes, parser)
        ns     = {"saml": "urn:oasis:names:tc:SAML:2.0:assertion"}
        nameid = root.find(".//{urn:oasis:names:tc:SAML:2.0:assertion}NameID")
        username = nameid.text if nameid is not None else "unknown"
        # Intentional: no audience / recipient / replay check
        session["user"] = username
        return redirect("/")
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5200, debug=True)
