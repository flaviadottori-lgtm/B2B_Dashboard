from unittest.mock import MagicMock

import pytest

from src.pipelines.caged.watermark import WatermarkController


class DummyConfig:
    GCP_PROJECT = "test-proj"
    BQ_DATASET_META = "meta"


class DummyClient:
    def __init__(self):
        self.inserted = []

    def query(self, *a, **k):
        class Job:
            __iter__ = lambda s: iter([])

        return Job()

    def insert_rows_json(self, table, rows):
        self.inserted.append((table, rows))
        return []


def test_idempotencia():
    ctrl = WatermarkController(DummyConfig())
    ctrl.client = DummyClient()
    assert not ctrl.is_processed("2022-01")
    ctrl.mark_success("2022-01", "runid")
    assert ctrl.client.inserted
