"""Application entrypoint.

The runtime entrypoint for local/dev/deploy is now ``backend/app.py`` so we can keep
``backend/main.py`` as the stable compatibility module used by existing imports/tests.
"""

from main import app  # noqa: F401

