import os
import uvicorn

from .rest import app

uvicorn.run(app, host=os.environ.get("UVICORN_HOST", "0.0.0.0"), port=int(os.environ.get("UVICORN_PORT", 8000)))
