#!/usr/bin/env bash
set -e
cd /openplc
exec python3 webserver/flask_server.py
