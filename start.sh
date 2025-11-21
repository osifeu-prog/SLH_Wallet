#!/usr/bin/env bash
set -e

export PORT="${PORT:-8000}"

echo "Starting SLH_Wallet_2.0 on port ${PORT} ..."
uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
