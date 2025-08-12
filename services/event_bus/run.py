#!/usr/bin/env python
"""
Run the Event Bus API server.
"""

import uvicorn

from services.event_bus.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
