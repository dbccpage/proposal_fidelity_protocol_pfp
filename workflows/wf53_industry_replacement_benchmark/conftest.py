import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
import pfp_core  # noqa: E402,F401  (adds ops/ and workflows/wf52_finite_qm_benchmark to sys.path)
