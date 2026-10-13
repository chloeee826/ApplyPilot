"""Launch an isolated no-cost browser-test backend with a temporary SQLite DB."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn


if __name__ == "__main__":
    with TemporaryDirectory(prefix="applypilot-e2e-") as directory:
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(directory) / 'e2e.db'}"
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ["SERVE_FRONTEND"] = "0"
        uvicorn.run("app.main:app", host="127.0.0.1", port=8011)
