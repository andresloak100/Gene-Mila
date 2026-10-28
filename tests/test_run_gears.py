"""tools/baselines_dl/run_gears.py without GEARS installed: the key translation to GEARS's condition names."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "baselines_dl"))

import run_gears  # noqa: E402


def test_condition_names():
    assert run_gears.condition("control") == "ctrl"
    assert run_gears.condition("ATF4") == "ATF4+ctrl"
    assert run_gears.condition("CEBPE+KLF1") == "CEBPE+KLF1"
