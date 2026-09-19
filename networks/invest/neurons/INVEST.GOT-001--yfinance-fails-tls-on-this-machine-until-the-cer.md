@neuron INVEST.GOT-001
head: yfinance fails TLS on this machine until the certifi bundle is copied to an ASCII-only path
layer: GOT
project: invest
status: active
confidence: verified
salience: 0.88
signals: certifi, certificate, curl_ca_bundle, ssl, unicode path, yfinance
description: Fetching data through yfinance on this Windows machine requires copying
  certifi.where() to C:\claude-certs\cacert.pem and exporting CURL_CA_BUNDLE and SSL_CERT_FILE
  to that path before running any command that touches Yahoo Finance.
rationale: The default certifi bundle sits under a user profile directory containing the
  non-ASCII character in MSİ, which the underlying TLS stack cannot open, so certificate
  verification fails before any request is made.
anchors: README.md, src/providers/yahoo.py
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
