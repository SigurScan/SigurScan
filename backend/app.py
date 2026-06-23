"""Application entrypoint.

The runtime entrypoint is ``backend/app.py`` so compatibility imports/tests can still
use ``backend/main.py`` as the legacy module.
"""

from main import app  # noqa: F401
