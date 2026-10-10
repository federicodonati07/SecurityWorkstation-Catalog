#!/bin/sh
# Verifies catalog.json against catalog.json.sig using only OpenSSL 3 (used by CI).
set -eu
cd "$(dirname "$0")/.."
base64 -d catalog.json.sig > /tmp/catalog.sig.bin 2>/dev/null || base64 -D -i catalog.json.sig -o /tmp/catalog.sig.bin
openssl pkeyutl -verify -pubin -inkey catalog.pub.pem -rawin -in catalog.json -sigfile /tmp/catalog.sig.bin
