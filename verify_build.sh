#!/usr/bin/env bash
set -euo pipefail
curl -fsS http://localhost:8080/healthz && echo OK
