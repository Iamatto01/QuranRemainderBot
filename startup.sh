#!/bin/bash

# Start the Python application
gunicorn --bind 0.0.0.0:$PORT --worker-class aiohttp.GunicornWebWorker --timeout 600 index:server