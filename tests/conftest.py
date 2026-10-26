import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))


@pytest.fixture(scope="session")
def synthetic_path(tmp_path_factory):
    import make_synthetic_data

    path = tmp_path_factory.mktemp("data") / "synthetic.xlsx"
    make_synthetic_data.write(str(path), seed=42)
    return str(path)
