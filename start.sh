#!/bin/bash
set -e

export PYTHONUNBUFFERED=1

if [ -z "$PORT" ]; then
  PORT=8000
fi

echo "Starting SLH_Wallet_2.0 on port $PORT ..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
