# app.py - Refactored Line
import os
import uvicorn

# Bind natively to loopback locally, while allowing cloud infrastructure string injections
uvicorn.run("api.main:app", host=os.environ.get("HOST", "127.0.0.1"), port=7860)
