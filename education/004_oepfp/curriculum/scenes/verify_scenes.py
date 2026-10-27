#!/usr/bin/env python3
"""Comprehensive Verification Suite for Milestone M5: Manim Animation Suite & Voiceover Pipeline.

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to sys.path if needed
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from education.education_app.use_cases.media.scene_generator import SceneVerificationUseCase


def main() -> int:
    print("=" * 72)
    print("MILESTONE M5 VERIFICATION SUITE")
    print("=" * 72)

    use_case = SceneVerificationUseCase()
    report = use_case.verify_all_scenes()

    if report.is_clean:
        print("ALL VERIFICATION CHECKS PASSED (100% GREEN)")
        print("=" * 72)
        return 0
    else:
        print(f"VERIFICATION FAILED WITH {report.issues_count} ERRORS:")
        for err in report.errors:
            print(f"  [ERROR] {err}")
        print("=" * 72)
        return 1


if __name__ == "__main__":
    sys.exit(main())
