"""pydicom_background_editor package.

Exports a small, convenient surface for tests and CLI.
"""

from .editor import Operation
from .path import parse, traverse

__all__ = ["Operation", "parse", "traverse"]
