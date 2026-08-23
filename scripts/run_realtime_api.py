"""Local launcher for the Tahlil realtime JSON API."""
from __future__ import annotations

import os
import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "realtime_api:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
