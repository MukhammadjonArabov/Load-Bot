#!/bin/sh
# Simple start script for AlwaysData
cd "$(dirname "$0")"
# Activate venv if present
if [ -f venv/bin/activate ]; then
  . venv/bin/activate
fi
exec python main.py
