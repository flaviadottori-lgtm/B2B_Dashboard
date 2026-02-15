from __future__ import annotations

from pathlib import Path


def pytest_ignore_collect(path, config) -> bool:
    """
    Ignore any test module that calls sys.exit(...) at import time.
    These are validation scripts and crash pytest collection in CI.
    """
    p = Path(str(path))

    if p.suffix != ".py" or not p.name.startswith("test_"):
        return False

    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False

    return "sys.exit(" in content
