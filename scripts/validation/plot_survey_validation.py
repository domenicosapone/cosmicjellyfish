#!/usr/bin/env python
"""Build the figures of the survey-validation study.

The script only reads the JSON reports produced by
``scripts/validation/validate_survey_observables.py`` and
``scripts/validation/run_survey_forecasts.py``; it never runs a forecast itself. Run the
two producers first, then::

    uv run python scripts/validation/plot_survey_validation.py

The figures are written to ``docs/source/_static/survey_validation/`` so that the
documentation page can embed them. Pass ``--output-dir`` to write them elsewhere.

Figures
-------
``survey_inputs.png``
    Number density per redshift bin for the spectroscopic and intensity-mapping
    configurations, and the analytic photometric ``dN/dz`` of the three imaging surveys.
``forecast_errors.png``
    Marginalised 1-sigma errors on the shared cosmological parameters, LCDM and w0waCDM.
``w0wa_ellipses.png``
    ``w0``-``wa`` Fisher ellipses built with the package ``fishconsumer`` machinery.
``fig1_diagnostic.png``
    Historical-versus-current SKAO Fig. 1 spectra, shown as a ratio to make the residual
    shape agreement visible (the amplitude offset is the modified-gravity fiducial).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yaml

from cosmicjellyfish.analysis.fishconsumer import make_triangle_plot
from cosmicjellyfish.analysis.fisher_matrix import fisher_matrix
from cosmicjellyfish.analysis.fisher_operations import marginalise

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIRECTORIES = (
    REPO_ROOT / "cosmicjellyfish/configs/other_survey_specifications",
    REPO_ROOT / "cosmicjellyfish/configs/default_survey_specifications",
)
SPECTRO_INPUTS = (
    ("DESI-BGS-SKAOPaper.yaml", "DESI BGS", "#1f77b4"),
    ("DESI-ELG-SKAOPaper.yaml", "DESI ELG", "#ff7f0e"),
    ("SKAO-Spectroscopic-SKAOPaper.yaml", "SKAO HI", "#2ca02c"),
)
PHOTO_INPUTS = (
    ("Euclid-Photometric-ISTF-Pessimistic.yaml", "Euclid", "#1f77b4"),
    ("Rubin-Photometric-SKAOPaper.yaml", "Rubin/LSST", "#ff7f0e"),
    ("SKAO-Photometric-SKAOPaper.yaml", "SKAO", "#2ca02c"),
)
ELLIPSE_CASES = (
    ("euclid_photo", "Euclid photo", "#1f77b4"),
    ("rubin_photo", "Rubin photo", "#ff7f0e"),
    ("euclid_spectro", "Euclid spectro", "#2ca02c"),
    ("desi_elg", "DESI ELG", "#d62728"),
    ("skao_im", "SKAO IM", "#9467bd"),
    ("planck", "Planck-like", "#7f7f7f"),
)
PARAM_LABELS = {
    "Omegam": r"$\Omega_m$",
    "Omegab": r"$\Omega_b$",
    "h": r"$h$",
    "ns": r"$n_s$",
    "sigma8": r"$\sigma_8$",
    "w0": r"$w_0$",
    "wa": r"$w_a$",
}


def load_specification(name: str) -> dict:
    """Return the YAML dictionary of a shipped survey specification."""
    for directory in SPEC_DIRECTORIES:
        path = directory / name
        if path.exists():
            with path.open() as handle:
                content = yaml.safe_load(handle)
            return content.get("specifications", content)
    raise FileNotFoundError(f"Survey specification {name!r} not found")


def load_json(path: Path) -> dict:
    """Load one of the JSON reports, with a helpful error if it is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run the producers first:\n"
            "  uv run python scripts/validation/validate_survey_observables.py\n"
            "  uv run python scripts/validation/run_survey_forecasts.py --model LCDM\n"
            "  uv run python scripts/validation/run_survey_forecasts.py --model w0waCDM"
        )
    with path.open() as handle:
        return json.load(handle)


def spectro_inputs(spec: dict) -> tuple[np.ndarray, np.ndarray]:
    """Return bin centres and ``dN/dz`` per square degree of a spectroscopic spec."""
    buckets = spec["z_bins_sp"]
    edges = np.asarray([buckets[key] for key in sorted(buckets)], dtype=float)
    density = np.asarray(
        [spec["dndOmegadz"][key] for key in sorted(spec["dndOmegadz"])], dtype=float
    )
    return edges.mean(axis=1), density


def photo_inputs(spec: dict) -> tuple[np.ndarray, np.ndarray]:
    """Return the analytic photometric ``dN/dz`` shape (normalised to unit area)."""
    edges = np.asarray(spec.get("z_bins_ph", spec.get("z_bins_GCph")), dtype=float)
    z = np.linspace(edges[0], edges[-1], 400)
    z0 = spec["zm"] / np.sqrt(2.0)
    shape = (z / z0) ** 2 * np.exp(-((z / z0) ** spec["ngamma"]))
    normalisation = np.trapezoid(shape, z)
    return z, shape / normalisation


def plot_survey_inputs(output_dir: Path) -> Path:
    """Plot the spectroscopic and photometric redshift distributions."""
    figure, (left, right) = plt.subplots(1, 2, figsize=(12, 4.5))

    for name, label, colour in SPECTRO_INPUTS:
        z, density = spectro_inputs(load_specification(name))
        left.plot(z, density, marker="o", label=label, color=colour)
    left.set_xlabel("redshift")
    left.set_ylabel(r"$dN/dz$ [deg$^{-2}$]")
    left.set_yscale("log")
    left.set_title("Spectroscopic galaxies and intensity mapping")
    left.legend()

    for name, label, colour in PHOTO_INPUTS:
        z, density = photo_inputs(load_specification(name))
        right.plot(z, density, label=label, color=colour)
    right.set_xlabel("redshift")
    right.set_ylabel(r"$dN/dz$ (normalised)")
    right.set_title("Photometric galaxies")
    right.legend()

    figure.tight_layout()
    path = output_dir / "survey_inputs.png"
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_forecast_errors(results_dir: Path, output_dir: Path) -> Path:
    """Plot the marginalised errors of the two model runs as grouped bars."""
    reports = {
        model: load_json(results_dir / f"survey_forecasts_{model}.json")
        for model in ("LCDM", "w0waCDM")
    }
    figure, (left, right) = plt.subplots(1, 2, figsize=(13, 5.5))

    panels = (
        (left, "LCDM", ("Omegam", "sigma8")),
        (right, "w0waCDM", ("w0", "wa")),
    )
    for axis, model, parameters in panels:
        results = reports[model]["results"]
        labels = [result["label"] for result in results]
        positions = np.arange(len(labels))
        width = 0.8 / len(parameters)
        for index, parameter in enumerate(parameters):
            values = [result["sigma"][parameter] for result in results]
            axis.barh(
                positions + index * width - 0.4 + width / 2,
                values,
                height=width,
                label=PARAM_LABELS[parameter],
            )
        axis.set_yticks(positions)
        axis.set_yticklabels(labels, fontsize=8)
        axis.set_xscale("log")
        axis.set_xlabel(r"marginalised $1\sigma$")
        axis.set_title(model)
        axis.legend(fontsize=9)
        axis.grid(axis="x", alpha=0.3)

    figure.tight_layout()
    path = output_dir / "forecast_errors.png"
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_w0wa_ellipses(results_dir: Path, output_dir: Path) -> Path:
    """Draw ``w0``-``wa`` Fisher ellipses with the ``fishconsumer`` machinery."""
    fishers = []
    labels = []
    for case, label, _colour in ELLIPSE_CASES:
        pattern = f"CosmicFish_*_survey_forecast_w0wacdm_{case}_*_FM.txt"
        paths = sorted((results_dir / "fishers").glob(pattern))
        if not paths:
            continue
        fishers.append(marginalise(fisher_matrix(file_name=str(paths[0])), ["w0", "wa"]))
        labels.append(label)
    if not fishers:
        raise FileNotFoundError(
            "No w0waCDM Fisher matrices found; run "
            "`uv run python scripts/validation/run_survey_forecasts.py --model w0waCDM`."
        )

    path = output_dir / "w0wa_ellipses.png"
    make_triangle_plot(
        fishers=fishers,
        fisher_labels=labels,
        params=["w0", "wa"],
        colors=[colour for _case, _label, colour in ELLIPSE_CASES][: len(fishers)],
        param_labels={"w0": r"$w_0$", "wa": r"$w_a$"},
        truth_values={"w0": -1.0, "wa": 0.0},
        file_format=".png",
        savefile=str(path),
    )
    return path


def plot_fig1(results_dir: Path, output_dir: Path) -> Path:
    """Plot the historical and current SKAO Fig. 1 spectra plus their ratio."""
    report = load_json(results_dir / "fig1_diagnostic.json")
    k = np.asarray(report["k"])
    window = np.asarray(report["k_window"])
    keys = ("P_gg(k, mu=0)", "P_II(k, mu=0)", "P_Ig(k, mu=0)", "P_gg(k, mu=1)")
    styles = ("-", "-.", ":", "--")
    window_index = np.searchsorted(k, window)

    figure, (left, right) = plt.subplots(1, 2, figsize=(12.5, 4.8))
    for key, style in zip(keys, styles):
        reference = np.asarray(report["reference"][key], dtype=float)
        current = np.asarray(report["current"][key], dtype=float)
        left.plot(k, reference, style, color="black", alpha=0.5)
        left.plot(window, current, marker="o", linestyle="none", markersize=3, label=key)
        right.plot(window, current / reference[window_index], style, marker="o", markersize=3)
    left.set_xscale("log")
    left.set_yscale("log")
    left.set_xlabel(r"$k$ [$1/\mathrm{Mpc}$]")
    left.set_ylabel(r"$P(k)$ [$(\mathrm{Mpc})^3$]")
    left.set_title("Historical (lines) and current (markers)")
    left.legend(fontsize=8)

    right.axhline(1.0, color="grey", linewidth=1)
    right.set_xscale("log")
    right.set_xlabel(r"$k$ [$1/\mathrm{Mpc}$]")
    right.set_ylabel("current / historical")
    right.set_title("Ratio in the amplitude window")

    figure.suptitle(r"SKAO Fig. 1 spectra at $z=0.6$ (GR rerun of an MG reference)", fontsize=11)
    figure.tight_layout()
    path = output_dir / "fig1_diagnostic.png"
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results/survey_validation"),
        help="directory holding the JSON reports",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/source/_static/survey_validation"),
        help="where the PNG figures are written",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    figures = [
        plot_survey_inputs(args.output_dir),
        plot_forecast_errors(args.results_dir, args.output_dir),
        plot_w0wa_ellipses(args.results_dir, args.output_dir),
        plot_fig1(args.results_dir, args.output_dir),
    ]
    for figure in figures:
        print(f"Wrote {figure}")


if __name__ == "__main__":
    main()
