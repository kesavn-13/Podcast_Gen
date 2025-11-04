"""Minimal EKS entrypoint that reuses the core FastAPI backend.

The container image executed in EKS should expose the exact same API surface as
the primary FastAPI application (`app.backend`).  Rather than maintaining a
second, partially duplicated web application we simply import the existing app
object and let uvicorn serve it.  This keeps the deployment behaviour aligned
with the locally validated workflow (see `scripts/test_new_pdf_paper_simplified.py`).
"""

from __future__ import annotations

import os

import uvicorn

# Importing `app.backend` performs all of the required wiring (startup hooks,
# orchestrator bootstrap, etc.) so the behaviour matches the local server.
from app.backend import app as backend_app


# Expose the FastAPI instance for uvicorn / ASGI servers.
app = backend_app


def main() -> None:
    """Run the FastAPI app when executed as `python main_eks.py`."""

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    uvicorn.run(app, host=host, port=port, log_level=log_level)


if __name__ == "__main__":
    main()