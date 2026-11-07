import os
import sys

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("pyotp")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
APP_DIR = os.path.join(ROOT, "streamlit_app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from streamlit.testing.v1 import element_tree as _et  # noqa: E402

# st.pills / st.segmented_control report value None before first interaction,
# which AppTest's ButtonGroup.indices cannot handle. Test-only shim.
_orig_indices = _et.ButtonGroup.indices.fget
_et.ButtonGroup.indices = property(lambda self: [] if self.value is None else _orig_indices(self))
