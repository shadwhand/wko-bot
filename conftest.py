"""Root conftest — ensure fitenv site-packages are on the path."""
import sys
import os

# The fitenv at /tmp/fitenv has all project dependencies.
# Add it at the front of sys.path so fitenv packages take priority.
_fitenv_sp = "/tmp/fitenv/lib/python3.14/site-packages"
if os.path.isdir(_fitenv_sp) and _fitenv_sp not in sys.path:
    sys.path.insert(0, _fitenv_sp)

# Block xarray from system site-packages to avoid version conflict with fitenv numpy.
# cmdstanpy optionally imports xarray; it works fine without it.
sys.modules.setdefault("xarray", None)
