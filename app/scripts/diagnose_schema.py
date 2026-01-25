from __future__ import annotations

import json
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "app"))

from lib import bq  # noqa: E402


def main() -> int:
    dataset = os.getenv("BQ_DATASET_GOLD", "gold")
    schema = bq.diagnose_schema(dataset=dataset)
    if not schema:
        print("Schema not available (check credentials / access).")
        return 1
    print(json.dumps(schema, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
