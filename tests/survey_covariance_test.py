"""Covariance paths for the migrated DESI and SKAO specifications."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("symbolic_pofk")

from cosmicjellyfish.fishermatrix.cosmicfish import FisherMatrix
from cosmicjellyfish.LSSsurvey.spectro_cov import SpectroCov
from cosmicjellyfish.LSSsurvey.spectro_obs import ComputeGalSpectro

FIDUCIAL = {"Omegam": 0.32, "Omegab": 0.05, "h": 0.67, "ns": 0.96, "sigma8": 0.822}


def _covariance(survey, observables, extra_options=None):
    options = {"code": "symbolic", "nonlinear": True, "feedback": 0}
    options.update(extra_options or {})
    fisher = FisherMatrix(
        options=options,
        observables=observables,
        freepars={"Omegam": 0.01},
        fiducialpars=FIDUCIAL,
        surveyName=survey,
        cosmoModel="LCDM",
    )
    spectrum = ["I", "g"] if "IM" in observables and "GCsp" in observables else None
    if spectrum is None:
        spectrum = ["I", "I"] if "IM" in observables else ["g", "g"]
    obs = ComputeGalSpectro(
        cosmopars=fisher.fiducialcosmopars,
        fiducial_cosmopars=fisher.fiducialcosmopars,
        spectrobiaspars=fisher.Spectrobiaspars,
        spectrononlinearpars=fisher.Spectrononlinpars,
        IMbiaspars=fisher.IMbiaspars,
        PShotpars=fisher.PShotpars,
        configuration=fisher,
    )
    cov = SpectroCov(
        fisher.fiducialcosmopars,
        fiducial_specobs=obs,
        bias_samples=spectrum,
        configuration=fisher,
    )
    return cov, obs


def test_desi_elg_covariance_is_positive_inside_the_bins():
    cov, _ = _covariance("DESI", ["GCsp"], {"survey_name_spectro": "DESI-ELG-SKAOPaper"})
    assert len(cov.inter_z_bin_mids) == 11
    k, mu = np.meshgrid(np.array([0.02, 0.05]), np.array([0.0, 0.5, 1.0]))
    for index, z in enumerate(cov.inter_z_bin_mids):
        volume = cov.volume_survey(index)
        density = cov.n_density(z)
        veff = cov.veff(z, k, mu)
        assert np.isfinite(volume) and volume > 0.0
        assert np.isfinite(density) and density > 0.0
        assert np.all(np.isfinite(veff)) and np.all(veff > 0.0)
    # Outside the survey redshift range the effective volume is zero.
    assert np.all(cov.veff(2.0, k, mu) == 0.0)


def test_skao_im_desi_cross_covariance_matches_the_overlap():
    cov, _ = _covariance(
        "SKAO",
        ["GCsp", "IM"],
        {
            "survey_name_spectro": "DESI-ELG-SKAOPaper",
            "survey_name_radio_IM": "SKAO-IM-Redbook-DESI-ELG",
        },
    )
    assert len(cov.inter_z_bin_mids) == 11
    k, mu = np.meshgrid(np.array([0.02]), np.array([0.5]))
    for index, z in enumerate(cov.inter_z_bin_mids):
        assert cov.volume_survey(index) > 0.0
        assert np.all(cov.veff(z, k, mu) > 0.0)
