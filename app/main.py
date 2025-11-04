"""Compatibility shim for legacy imports.

This module simply re-exports the FastAPI ``app`` defined in
``app.backend`` so existing deployment targets that reference
``app.main:app`` continue to function without the historical
boilerplate that relied on now-removed modules.
"""

from app.backend import app as backend_app

app = backend_app

__all__ = ["app"]