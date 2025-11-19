import pytest
from mwa_core.orchestrator import Orchestrator
from mwa_core.scraper import ScraperEngine, Listing
from datetime import datetime


def test_orchestrator_runs_providers():
    orch = Orchestrator()
    config = {
        "immoscout": {"headless": True},
        "wg_gesucht": {"headless": True},
    }
    new = orch.run(["immoscout", "wg_gesucht"], config)
    assert isinstance(new, int)