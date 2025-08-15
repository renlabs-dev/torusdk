"""
Official Torus SDK library for Python.

Submodules:
    * `torus.client`: A lightweight client for the Torus Network.
    * `.types`: Torus common types.
    * `.key`: Key related functions.
    * `.compat`: Compatibility layer for the classic library.

.. include:: ../../README.md
"""

import importlib.metadata

if not __package__:
    __version__ = "0.0.0"
else:
    __version__ = importlib.metadata.version(__package__)
