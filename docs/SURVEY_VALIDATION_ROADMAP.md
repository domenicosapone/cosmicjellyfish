# Survey validation roadmap: DESI, Rubin/LSST, SKAO and Planck

**Status:** in progress
**Owner:** core maintainers
**Related:** [`docs/KNOWN_ISSUES.md`](KNOWN_ISSUES.md), [`docs/source/comprehensive_guide.md`](source/comprehensive_guide.md),
[`paper/paper.md`](../paper/paper.md), Casas et al. 2023 ([arXiv:2210.05705](https://arxiv.org/abs/2210.05705))

This is the living plan for validating the non-Euclid survey configurations that the
code advertises but does not currently ship or test: **DESI** (spectroscopic), **Rubin /
Vera C. Rubin Observatory / LSST** (photometric), **SKAO** (HI galaxy clustering,
intensity mapping and the photometric variant) and **Planck** (CMB). It also covers the
historical SKAO radio x optical forecast from Casas et al. 2023, restricted to its
**GR-only** content.

The roadmap is a working document. Update the status tables and the progress log at the
bottom of this file as work lands. A polished, user-facing summary will be added under
`docs/source/` once the validation results exist; this file stays as the engineering
tracker.

---

## 1. Objective and scope

**Objective.** Show that every survey configuration the package claims to support can be
configured, run end-to-end, and that its observables and Fisher matrices agree with the
historical reference implementation (the `cosmicfish_reloaded_skaproject` checkout) and
with the published SKAO forecast where a like-for-like comparison is physically
well-defined.

**In scope**

- Migrate the historical DESI, Rubin and SKAO survey inputs into the current
  `specifications` YAML schema under the packaged survey directories.
- Run photo (GCph, WL, 3x2pt) and spectro (GCsp) forecasts for each survey and compare
  them against the corresponding Euclid run.
- Validate individual observables (number densities, bias, volume, `P_gg(k, mu, z)`,
  HI brightness temperature, beam and noise) against the original project **before**
  trusting any Fisher number.
- Reproduce the **GR-only** parts of Casas et al. 2023 (Fig. 1 spectra, per-probe
  constraints, probe combinations, IM x DESI cross-correlation).
- Ship CLI scripts, one tutorial notebook, a docs page, and a compact figure + text for
  the JOSS paper.

**Out of scope**

- Modified-gravity forecasts (`mu`, `eta`, `Sigma`, `E11`, `E22`). The historical runs
  used external MGCAMB tables that are not part of this package. The SKAO paper's
  headline numbers (mu 2.7 %, Sigma 1.8 %, etc.) are MG constraints and are **not** valid
  targets for a GR-only run.
- Reproducing the historical numbers digit-for-digit. The old runs used a different
  backend (`code: 'external'` with MGCAMB), an MG fiducial and, in places, a different
  binning. The goal is to explain every difference, not to hide it.
- Full-shape / bispectrum analyses; all forecasts stay in the Gaussian Fisher
  approximation used by the rest of the package.

**Definition of done.** A reader can follow the docs page, pick a shipped survey, run a
quick forecast with one command, and see a results table that separates
(a) historical MG references, (b) matched historical observables, and (c) new GR
forecasts, with the caveats stated explicitly.

---

## 2. Current state (starting point)

Verified against `main` before this workstream:

| Area | State |
| --- | --- |
| DESI | Survey-name branch exists in `config.py`, but **no YAML is shipped**. `surveyName="DESI"` fails with a missing-file error. |
| Rubin / LSST | Same: branch exists, **no YAML shipped**. |
| SKAO photometric | `SKAO-Photometric-Redbook.yaml` shipped in `other_survey_specifications/`, but scale cuts differ from the paper-era inputs (`lmax_GCph` 750 vs 1500, `lmax_WL` 3000 vs 5000). |
| SKAO spectroscopic | `SKAO-Spectroscopic-Redbook.yaml` shipped; 5 z-bins but only `Ps_1..Ps_4` shot-noise keys (suspected bug). |
| SKAO intensity mapping | `SKAO-IM-Redbook.yaml` shipped; contains both `area_survey_IM` and `fsky_IM` with inconsistent values. |
| Planck | `Planck.yaml` shipped and selectable by `surveyName`; CMB path documented in `docs/source/cmb_benchmarks.md`. |
| Cross-spectra | `observables=['GCsp','IM']` selects the **IM x GCsp cross-spectrum only**, not auto + cross. Must be stated in the docs. |
| Historical inputs | Present only in the read-only `cosmicfish_reloaded_skaproject` checkout (`.dat` tables, old YAMLs, saved Fisher matrices, `data-for-fig1.dat`). |
| Notebooks | Old workflows survive only in `notebooks/archive/old/` (`Example_Fishers-Various_Surveys-DESI-Rubin-Euclid.ipynb`, `SKAO_presentation.ipynb`). |

---

## 3. Phases

Each phase has an explicit exit criterion. Do not start a later phase on top of an
unvalidated earlier one: the Fisher numbers are only meaningful if the inputs and the
observables already agree.

### Phase 0 - Provenance map and assumptions table

**Goal.** Before touching a single number, know exactly where every historical input lives
and what it means.

Tasks

- [ ] Inventory every historical file and map it to the current schema element
      (source path, notebook/cell, survey value, units, current equivalent).
- [ ] Trace which `vfinal/` Fisher matrices and which plot data correspond to which
      figure/table in Casas et al. 2023.
- [ ] Compare old vs new formulas for: number density `n(z)`, linear bias, photo-z
      parameters, shot noise, HI beam, system noise, survey volume.
- [ ] Establish what the old `dn3` column means in the old volume calculation before
      mapping it to `dndOmegadz` (the old code read `gc_table[:,3]` as the density and
      built the volume from the bin edges separately).
- [ ] Record the old derived conventions: `z0 = zm / sqrt(2)`, `z0_p = 1.0`,
      `binrange = range(1, len(z_bins))`, `ngalbin` from `ngal_sqarmin`.
- [ ] Keep the original data **read-only**; never modify the historical checkout.

Deliverable: the assumptions table in [section 6](#6-provenance-and-assumptions-table)
filled in, with every row marked *matched*, *different by design* or
*requires investigation*.

**Exit criterion.** Every input file has an owner row in the table and no row is left
"requires investigation" without a follow-up task.

### Phase 1 - Migrate survey configurations

**Goal.** Ship DESI, Rubin, SKAO paper-era and Planck inputs in the current schema, with
names that make the provenance obvious.

Naming convention: append `-SKAOPaper` to configurations transcribed from the historical
project so nobody confuses them with current-official specs. Keep the already-shipped
current names untouched.

Planned files (final names may shift once Phase 0 confirms the inputs):

| New file | Source | Contents |
| --- | --- | --- |
| `DESI-BGS-SKAOPaper.yaml` | `DESI_BGS_GCsp.dat`, `DESI-Optimistic.yaml` | 5 z-bins 0.0-0.5, `dndOmegadz` 1165/3074/1909/732/120, bias 1.364..1.454, area 14000 |
| `DESI-ELG-SKAOPaper.yaml` | `DESI_ELG_GCsp.dat` | z-bins 0.6-1.6+, densities and bias from the `.dat` table, area 14000 |
| `Rubin-Photometric-SKAOPaper.yaml` | `Rubin-Optimistic.yaml` | 10-bin `z_bins` 0.001-2.50, `zm` 0.156, `ngamma` 0.68, `ngal_sqarmin` 27, `lmax_GCph` 1500, `lmax_WL` 5000, fsky 0.33/0.35 |
| `SKAO-Photometric-SKAOPaper.yaml` | `SKA1-Redbook-Optimistic.yaml` | same 10-bin edges, `zm` 1.1, `lmax_GCph` 1500, `lmax_WL` 5000, fsky 0.1166 |
| `SKAO-Spectroscopic-SKAOPaper.yaml` | `SKA1_GCsp_MDB2_Redbook.dat` | 5 bins 0.0-0.5, densities 2714.82..154.353, bias 0.648..0.973, area 5000 |
| `SKAO-IM-Redbook-DESI-ELG.yaml` | `SKA1_IM_MDB1_Redbook-new-DESI_E.dat` | IM bins aligned to DESI ELG for the cross-correlation |
| `Planck.yaml` (existing) | shipped | verify, do not duplicate |

> **Open decision (Phase 1):** should the paper-era DESI/Rubin/SKAO files live in
> `default_survey_specifications/` or `other_survey_specifications/`? Proposed: the
> historical variants go to `other_survey_specifications/` (opt-in), while a minimal
> *current-best* DESI and Rubin file may be promoted to `default_survey_specifications/`
> so `surveyName="DESI"` stops failing. Confirm before writing files.

Tasks

- [ ] Transcribe bin edges, densities, fiducial bias and every nuisance parameter
      (`Ps_*`, `sigmap_*`, `sigmav_*` where relevant) for each new YAML.
- [ ] Check that per-bin arrays are complete and that every bin has a matching key
      (this is exactly the `Ps_1..Ps_4` vs 5-bin bug in the shipped SKAO spectro file).
- [ ] Confirm each YAML loads by name from an **installed** package (package data, not
      just the source tree).
- [ ] Confirm `surveyName="DESI"` and the Rubin branch resolve to a real file.

**Exit criterion.** Every new YAML loads, produces a config, and passes a schema check;
`docs/source/comprehensive_guide.md` and `docs/KNOWN_ISSUES.md` are updated to reflect
what is now shipped.

### Phase 2 - Validate individual observables

**Goal.** Agree with the historical implementation *before* running any forecast.

Tasks

- [ ] **Photo:** compare `n(z)`, bin populations and angular spectra for Rubin and SKAO
      photometric, with matched photo-z, bias, IA and scale cuts.
- [ ] **GCsp:** compare bin density, bias, survey volume and `P_gg(k, mu, z)` for DESI
      BGS, DESI ELG and SKAO HI galaxies.
- [ ] **IM:** compare `b_HI(z)`, `Omega_HI(z)`, `Tbar_b(z)`, the beam and the noise
      power for the SKAO IM configuration.
- [ ] **Fig. 1 diagnostic:** recompute the Cai/Casas-style `P_gg`, `P_II`, `P_Ig` and
      shot-noise curves at `z = 0.6` and overlay them on `data-for-fig1.dat`. The
      historical curves used the MG fiducial, so a GR comparison is *not* expected to be
      exact; isolate the contribution from fiducial cosmology, backend and modelling.

**Exit criterion.** Every observable either matches within a stated tolerance or has a
documented, quantified explanation for the difference.

### Phase 3 - Forecast comparisons

**Goal.** A common GR fiducial and parameter basis, so survey comparisons are fair.

Common setup: `Omegam 0.32, Omegab 0.05, h 0.67, ns 0.96`, massless neutrinos, flat
LCDM, the same `k`/`mu` sampling and the same derivative method.

Tasks

- [ ] **Photo:** Euclid vs Rubin, `GCph`, `WL`, and the 3x2pt combination.
- [ ] **Spectro:** Euclid vs DESI BGS and vs DESI ELG, separately first, then combined.
- [ ] **SKAO:** continuum photometric, HI galaxy clustering, intensity mapping
      individually, then the IM x DESI-ELG cross-correlation on aligned bins.
- [ ] **Planck:** rerun the shipped CMB configuration and compare against the published
      covariance where reference inputs exist.
- [ ] For every combination, state explicitly whether it is a cross-spectrum-only Fisher
      or a genuine joint auto + cross analysis. Check bin overlaps, cross-covariances and
      distinct nuisance names before adding information.

**Exit criterion.** A results table with a stable parameter set per probe, plus the
warnings that apply to each combination.

### Phase 4 - Scripts, plots, notebook, docs, paper

**Goal.** Everything above is reproducible by a reader.

Tasks

- [ ] CLI scripts under `scripts/validation/` with `--quick` / default (full) modes,
      writing the effective configuration, backend version and an output directory.
- [ ] Plots: survey coverage and inputs (n(z), bias, noise), representative spectra,
      Fisher ellipses via the existing `fishconsumer` machinery, marginal-error
      comparison panels, and the Fig. 1 historical-vs-current diagnostic.
- [ ] One tutorial notebook that runs the quick configuration end-to-end.
- [ ] Docs page under `docs/source/` with the migrated specs, commands, results,
      limitations and comparisons; link it from `user_guide.md`.
- [ ] JOSS paper: one compact figure and one paragraph, added **only** after Phase 3
      passes; revise the current "can load user specifications for DESI and LSST"
      wording to say what is actually shipped.

**Exit criterion.** Executed notebook, strict docs build (`sphinx -W`), and paper figure
regenerable from a committed script.

### Phase 5 - Verification and completion

Tasks

- [ ] Tests for every shipped survey configuration: loading, package data, bin
      consistency, parameter-name completeness and uniqueness.
- [ ] Tests for the observable and covariance paths touched by the new configurations.
- [ ] Quick end-to-end forecast per survey as a smoke test; full forecasts run separately
      with recorded timings and settings.
- [ ] Derivative-step and resolution checks; Fisher symmetry and conditioning checks;
      nuisance-marginalisation checks.
- [ ] Results table separating historical MG references, matched historical observables
      and new GR forecasts.
- [ ] CHANGELOG entry.
- [ ] Final review pass and PR.

**Exit criterion.** Green CI, strict docs build, and a reviewer can reproduce at least
one number per survey from the docs page alone.

---

## 4. Known issues to resolve along the way

| # | Issue | Where | Phase | Status |
| --- | --- | --- | --- | --- |
| 1 | SKAO photometric scale cuts differ between historical (`lmax_GCph` 1500, `lmax_WL` 5000) and shipped (750/3000) | `SKAO-Photometric-Redbook.yaml` | 1 | open |
| 2 | SKAO spectro defines 5 z-bins but only `Ps_1..Ps_4` shot-noise keys | `SKAO-Spectroscopic-Redbook.yaml` | 1 | open |
| 3 | IM config has both `area_survey_IM: 5000` and `fsky_IM: 0.48`; the config prefers `fsky_IM`, the IM noise uses `fsky_IM`, but `SpectroCov.volume_survey` uses `fsky_spectro` | `SKAO-IM-Redbook.yaml`, `spectro_cov.py` | 1-2 | open |
| 4 | Historical IM x DESI-ELG cross used bins aligned to DESI ELG; current covariance uses `intersect1d` on bins/mids | `spectro_cov.py` | 2-3 | open |
| 5 | `observables=['GCsp','IM']` selects the cross-spectrum only, not auto + cross | `fishermatrix/cosmicfish.py` | 3 | open |
| 6 | Old runs used external MGCAMB tables, unavailable here | historical project | n/a | documented |
| 7 | `surveyName="DESI"` fails with a missing-file error | `config.py` | 1 | open |
| 8 | Rubin and DESI have code branches but no shipped YAML | `config.py`, docs | 1 | open |
| 9 | `kmax_IM` units unconfirmed | `docs/KNOWN_ISSUES.md` | 2 | open |
| 10 | Survey-table numbers in the docs have not been re-checked against the YAMLs | docs | 1 | open |

---

## 5. Historical reference material (read-only)

Path: `/home/santiago/CosmoProjects/CosmicFish-Projects/cosmicfish_reloaded_skaproject`
(remote `git@gitlab.com:matmartinelli/cosmicfish_reloaded.git`, HEAD `76f4892`).
**Do not modify this checkout.** It contains locally modified notebooks and untracked
Overleaf files.

Key inputs in `survey_specifications/`:

- `DESI_BGS_GCsp.dat`, `DESI_ELG_GCsp.dat` - `zmin zm zmax dn3 bias`, area in a header
  comment.
- `SKA1_GCsp_MDB2_Redbook.dat` - same format, SKAO HI galaxies.
- `SKA1_IM_MDB1_Redbook*.dat` - IM bins, including the DESI-ELG-aligned variant.
- `Rubin-Optimistic.yaml`, `DESI-Optimistic.yaml`, `SKA1-Redbook-Optimistic.yaml` -
  old-schema survey specs.
- `nofz_ska1_5000.dat`, `SKA1_THI_sys_noise.txt`, `SKA1-IM-z_Pnoise.txt`,
  `lumratio_file.dat` - auxiliary tables.
- `data-for-fig1.dat` - the spectra behind the paper's Fig. 1 at `z = 0.6`.
- `vfinal/`, `v2results/`, `results/`, `raw_results/`, `benchmark_results/` - saved
  Fisher matrices and plot data.

Reference parameter basis in the saved matrices:
`Omegam, Omegab, h, ns, sigma8, E11, E22, lnbgs8_1..N, Ps_1..N` with fiducial
`0.32, 0.05, 0.67, 0.96, 0.822246, 0.1007, 0.8293`.

---

## 6. Provenance and assumptions table

Fill this in during Phase 0. One row per historical input or convention.

| Historical input | Source path / notebook | Unit | Current schema element | Match | Notes |
| --- | --- | --- | --- | --- | --- |
| DESI BGS n(z), bias | `DESI_BGS_GCsp.dat` | Mpc^-3 (assumed) | `dndOmegadz`, `bHg_*` | TBD | area 14000 |
| DESI ELG n(z), bias | `DESI_ELG_GCsp.dat` | Mpc^-3 (assumed) | `dndOmegadz`, `bHg_*` | TBD | bins 0.6-1.6+ |
| SKAO HI galaxy n(z), bias | `SKA1_GCsp_MDB2_Redbook.dat` | Mpc^-3 (assumed) | `dndOmegadz`, `bHg_*` | TBD | matches shipped SKAO spectro numbers |
| SKAO IM bins | `SKA1_IM_MDB1_Redbook.dat` | - | `z_bins_IM` | TBD | many variants exist |
| IM x DESI-ELG bins | `SKA1_IM_MDB1_Redbook-new-DESI_E.dat` | - | `z_bins_IM` | TBD | aligned to DESI ELG |
| Rubin photo-z / n(z) | `Rubin-Optimistic.yaml`, `nofz_ska1_5000.dat` | - | `z_bins_ph`, `photo_z_params` | TBD | `zm` 0.156 -> `z0 = zm/sqrt(2)` |
| SKAO photo-z / n(z) | `SKA1-Redbook-Optimistic.yaml` | - | `z_bins_ph`, `photo_z_params` | TBD | `zm` 1.1 |
| Old `dn3` meaning | `bckpcosmicfishpie/cosmology/nuisance.py` | - | `dndOmegadz` | TBD | read as column 3 |
| Old volume formula | old `SpectroCov` | Mpc^3 | `d_volume`, `volume_survey` | TBD | bin edges vs `dn3` |
| Old shot noise | old configs | - | `shot_noise_parametrization` | TBD | `Ps_*` all zero in saved matrices |
| Old FoG / `sigmap` | old configs | - | `nonlinear_parametrization` | TBD | `bfs8terms: True`, `AP_effect: True` |
| Fig. 1 spectra | `data-for-fig1.dat` | Mpc^3 | new `P_gg`, `P_II`, `P_Ig` at `z=0.6` | TBD | MG fiducial |

---

## 7. Results tables

### 7.1 Observable validation (Phase 2)

| Observable | Survey | Reference | Max relative difference | Verdict | Notes |
| --- | --- | --- | --- | --- | --- |
| n(z) | DESI BGS | `DESI_BGS_GCsp.dat` | TBD | TBD | |
| n(z) | DESI ELG | `DESI_ELG_GCsp.dat` | TBD | TBD | |
| n(z) | SKAO HI | `SKA1_GCsp_MDB2_Redbook.dat` | TBD | TBD | |
| n(z) | Rubin | `Rubin-Optimistic.yaml` | TBD | TBD | |
| P_gg(k, mu, z) | DESI / SKAO | Fig. 1 data | TBD | TBD | GR vs MG fiducial |
| P_II, P_Ig | SKAO IM | Fig. 1 data | TBD | TBD | |
| Tbar_b, b_HI | SKAO IM | paper Eqs. 19-22 | TBD | TBD | |
| Noise power | SKAO IM | paper Eq. 27 | TBD | TBD | |

### 7.2 GR forecast comparison (Phase 3)

Parameter set: `10^9As, Omegam, Omegab, h, ns` (add `w0, wa` only if the backend
supports it), bias and shot noise marginalised.

| Survey | Probe(s) | sigma(Omegam) | sigma(h) | sigma(ns) | sigma(10^9As) | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Euclid | GCph+WL | TBD | TBD | TBD | TBD | reference |
| Rubin | GCph+WL | TBD | TBD | TBD | TBD | |
| Euclid | GCsp | TBD | TBD | TBD | TBD | reference |
| DESI BGS | GCsp | TBD | TBD | TBD | TBD | |
| DESI ELG | GCsp | TBD | TBD | TBD | TBD | |
| SKAO HI | GCsp | TBD | TBD | TBD | TBD | |
| SKAO | IM | TBD | TBD | TBD | TBD | |
| SKAO x DESI | IM x ELG | TBD | TBD | TBD | TBD | cross-spectrum only |
| Planck | CMB | TBD | TBD | TBD | TBD | |

### 7.3 SKAO paper cross-check (GR-only)

State clearly which paper numbers can and cannot be reproduced. The published headline
numbers are MG constraints and are **not** targets here.

| Quantity | Paper (MG) | This work (GR) | Comparable? | Comment |
| --- | --- | --- | --- | --- |
| sigma(mu) from SKAO radio | 2.7 % | n/a | no | MG parameter |
| sigma(Sigma) from SKAO radio | 1.8 % | n/a | no | MG parameter |
| Fig. 1 spectra | yes | TBD | qualitatively | different fiducial |

---

## 8. Deliverables checklist

- [ ] `docs/SURVEY_VALIDATION_ROADMAP.md` (this file), kept up to date
- [ ] New survey YAMLs under `cosmicjellyfish/configs/other_survey_specifications/`
      (and/or `default_survey_specifications/` after the Phase 1 decision)
- [ ] `scripts/validation/run_survey_validation.py` and friends (quick/full)
- [ ] `notebooks/NN-survey-validation.ipynb` (executed)
- [ ] `docs/source/survey_validation.md` + `user_guide.md` link
- [ ] Figures committed under `docs/source/_static/survey_validation/`
- [ ] Tests under `tests/` for configs and observables
- [ ] CHANGELOG entry
- [ ] `paper/` figure + paragraph
- [ ] PR

---

## 9. Progress log

Append one line per landed step. Keep it factual: what changed, what was verified, what
is next.

| Date | Step | Result |
| --- | --- | --- |
| 2026-11-13 | Wrote this roadmap | Plan recorded; next is Phase 0 provenance audit |
