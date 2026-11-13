"""Unit tests for the Phase 3 survey-forecast harness.

These tests exercise the bookkeeping (parameter sets, combination of independent blocks
and table rendering) without running a Fisher matrix. The full runs are recorded in
``docs/SURVEY_VALIDATION_ROADMAP.md``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validation" / "run_survey_forecasts.py"


def _load_module():
    sys.path.insert(0, str(REPO_ROOT))
    spec = importlib.util.spec_from_file_location("run_survey_forecasts", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


module = _load_module()


def test_free_parameters_follow_the_model():
    lcdm = module._free_parameters("LCDM")
    w0wa = module._free_parameters("w0waCDM")
    assert list(lcdm) == ["Omegam", "Omegab", "h", "ns", "sigma8"]
    assert list(w0wa) == ["Omegam", "Omegab", "h", "ns", "sigma8", "w0", "wa"]
    with pytest.raises(ValueError):
        module._free_parameters("nuoCDM")


def test_combination_matches_inverse_variance_addition():
    names = list(module._free_parameters("LCDM"))
    sigmas = {
        "first": {name: 0.01 for name in names},
        "second": {name: 0.02 for name in names},
    }
    results = {
        name: {
            "label": name,
            "observables": ["GCsp"],
            "note": "",
            "elapsed_s": 1.0,
            "sigma": sigma,
        }
        for name, sigma in sigmas.items()
    }
    combined = module.combine(results, ("first", "second"), "LCDM")
    expected = 1.0 / np.sqrt(1.0 / 0.01**2 + 1.0 / 0.02**2)
    for name in names:
        assert combined["sigma"][name] == pytest.approx(expected, rel=1e-12)
    assert combined["elapsed_s"] == pytest.approx(2.0)


def test_format_table_has_one_row_per_case():
    results = [
        {
            "label": "Euclid",
            "elapsed_s": 1.5,
            "sigma": {name: 0.1 for name in module._free_parameters("LCDM")},
        },
        {
            "label": "Rubin",
            "elapsed_s": 2.5,
            "sigma": {name: 0.2 for name in module._free_parameters("LCDM")},
        },
    ]
    table = module.format_table(results, "LCDM")
    lines = [line for line in table.splitlines() if line.startswith("|")]
    assert len(lines) == 4  # header, separator, two cases
    assert "Euclid" in table and "Rubin" in table
