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
| DESI | Survey-name branch exists in `config.py`. Paper-era `DESI-BGS-SKAOPaper` and `DESI-ELG-SKAOPaper` files are now shipped, opt-in via `survey_name_spectro`. |
| Rubin / LSST | Paper-era `Rubin-Photometric-SKAOPaper` is now shipped, opt-in via `survey_name_photo`. |
| SKAO photometric | `SKAO-Photometric-Redbook.yaml` shipped; paper-era cuts (`lmax_GCph` 1500, `lmax_WL` 5000) live in `SKAO-Photometric-SKAOPaper.yaml`. |
| SKAO spectroscopic | `SKAO-Spectroscopic-Redbook.yaml` shipped; the missing `Ps_5` key is fixed, and `SKAO-Spectroscopic-SKAOPaper.yaml` holds the paper-era transcription. |
| SKAO intensity mapping | `SKAO-IM-Redbook.yaml` shipped; `SKAO-IM-Redbook-DESI-ELG.yaml` adds the DESI-ELG-aligned bins. The dual `area_survey_IM`/`fsky_IM` values remain and are documented (issue 3). |
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

- [x] Inventory every historical file and map it to the current schema element
      (source path, notebook/cell, survey value, units, current equivalent).
- [ ] Trace which `vfinal/` Fisher matrices and which plot data correspond to which
      figure/table in Casas et al. 2023. (Started; `vfinal/` inventory recorded in
      section 5, per-figure mapping still open.)
- [x] Compare old vs new formulas for: number density `n(z)`, linear bias, photo-z
      parameters, shot noise, HI beam, system noise, survey volume.
- [x] Establish what the old `dn3` column means in the old volume calculation before
      mapping it to `dndOmegadz`. Result: `dn3` is `dN/dz` per deg^2, and the old volume
      formula is algebraically identical to the current one.
- [x] Record the old derived conventions: `z0 = zm / sqrt(2)`, `z0_p = 1.0` for
      non-Euclid (cancels in normalization), `binrange = range(1, len(z_bins))`,
      `ngalbin` from `ngal_sqarmin`.
- [x] Keep the original data **read-only**; never modify the historical checkout.

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

- [x] Transcribe bin edges, densities, fiducial bias and every nuisance parameter
      (`Ps_*`, `sigmap_*`, `sigmav_*` where relevant) for each new YAML.
- [x] Check that per-bin arrays are complete and that every bin has a matching key
      (this is exactly the `Ps_1..Ps_4` vs 5-bin bug in the shipped SKAO spectro file).
- [x] Confirm each YAML loads by name from an **installed** package (package data, not
      just the source tree).
- [ ] Confirm `surveyName="DESI"` and the Rubin branch resolve to a real file without an
      explicit `survey_name_*` option. (Currently they still need the option; see the
      Phase 1 decision below.)
- [x] Update `docs/source/comprehensive_guide.md` and `docs/KNOWN_ISSUES.md`.

**Decision taken:** historical variants live in `other_survey_specifications/` and stay
opt-in. The `DESI`/`Rubin` branches keep loading whatever `survey_name_photo` /
`survey_name_spectro` names, so the docs show the explicit option form. Promoting a
*current-best* DESI/Rubin file to the defaults is deferred until an up-to-date
specification is agreed.

**Exit criterion.** Every new YAML loads, produces a config, and passes a schema check;
`docs/source/comprehensive_guide.md` and `docs/KNOWN_ISSUES.md` are updated to reflect
what is now shipped. **Met:** `tests/survey_specs_test.py` covers parsing and
per-bin consistency; `FisherMatrix` construction was verified for DESI BGS, DESI ELG,
Rubin, SKAO photometric, SKAO spectroscopic and the IM x DESI-ELG cross.

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
- [x] CHANGELOG entry (updated per step).
- [ ] Final review pass and PR.

**Exit criterion.** Green CI, strict docs build, and a reviewer can reproduce at least
one number per survey from the docs page alone.

---

## 4. Known issues to resolve along the way

| # | Issue | Where | Phase | Status |
| --- | --- | --- | --- | --- |
| 1 | SKAO photometric scale cuts differ between historical (`lmax_GCph` 1500, `lmax_WL` 5000) and shipped (750/3000) | `SKAO-Photometric-Redbook.yaml` | 1 | **resolved** - paper-era cuts kept in `SKAO-Photometric-SKAOPaper.yaml` |
| 2 | SKAO spectro defines 5 z-bins but only `Ps_1..Ps_4` shot-noise keys | `SKAO-Spectroscopic-Redbook.yaml` | 1 | **fixed** - added `Ps_5`; covered by `tests/survey_specs_test.py` |
| 3 | IM config has both `area_survey_IM: 5000` and `fsky_IM: 0.48`; the config prefers `fsky_IM`, the IM noise uses `fsky_IM`, but `SpectroCov.volume_survey` uses `fsky_spectro` | `SKAO-IM-Redbook.yaml`, `spectro_cov.py` | 1-2 | open |
| 4 | Historical IM x DESI-ELG cross used bins aligned to DESI ELG; current covariance uses `intersect1d` on bins/mids | `spectro_cov.py` | 2-3 | open |
| 5 | `observables=['GCsp','IM']` selects the cross-spectrum only, not auto + cross | `fishermatrix/cosmicfish.py` | 3 | open |
| 6 | Old runs used external MGCAMB tables, unavailable here | historical project | n/a | documented |
| 7 | `surveyName="DESI"` fails with a missing-file error | `config.py` | 1 | **documented** - requires an explicit `survey_name_spectro` option |
| 8 | Rubin and DESI have code branches but no shipped YAML | `config.py`, docs | 1 | **resolved** - `-SKAOPaper` files shipped |
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

Filled in during Phase 0. One row per historical input or convention.

| Historical input | Source path / notebook | Unit | Current schema element | Match | Notes |
| --- | --- | --- | --- | --- | --- |
| `dn3` column | `*.dat` files, read as `gc_table[:,3]` | dN/dz per deg^2 | `dndOmegadz` | **matched** | Old `n_density = dn3*dz/d_volume_per_deg2`; current `n_density = dnz*dz/d_volume*areasky`. Since `d_volume_per_deg2 = d_volume/areasky`, the two expressions are algebraically identical. Copy `dn3` verbatim into `dndOmegadz`. |
| DESI BGS n(z), bias | `DESI_BGS_GCsp.dat` | dN/dz/deg^2 | `dndOmegadz`, `bHg_*` | **matched** | 5 bins 0.00-0.50, densities 1165/3074/1909/732/120, bias 1.36436..1.45367, area 14000 deg^2 |
| DESI ELG n(z), bias | `DESI_ELG_GCsp.dat` | dN/dz/deg^2 | `dndOmegadz`, `bHg_*` | **matched** | 11 bins 0.60-1.70, densities 309/2269/1923/2094/1441/1353/1337/523/466/329/126, bias 1.01916..1.36020 |
| SKAO HI galaxy n(z), bias | `SKA1_GCsp_MDB2_Redbook.dat` | dN/dz/deg^2 | `dndOmegadz`, `bHg_*` | **matched** | Identical to the shipped `SKAO-Spectroscopic-Redbook.yaml` (2714.82..154.353, 0.64813..0.97350) |
| SKAO IM bins | `SKA1_IM_MDB1_Redbook.dat` | - | `z_bins_IM` | **matched by design** | Multiple variants exist; shipped `SKAO-IM-Redbook.yaml` uses 10 bins 0.5-2.6 |
| IM x DESI-ELG bins | `SKA1_IM_MDB1_Redbook-new-DESI_E.dat` | - | `z_bins_IM` | **different by design** | Historical cross used IM bins aligned to DESI ELG. Needs a dedicated YAML; current `intersect1d` path must be tested (issue 4). |
| Photo `dNdz(z)` shape | `photo_window.py` | - | `dNdz` | **matched** | Both old and new use `(z/z0_p)^2 exp(-(z/z0)^ngamma)`. Old set `z0_p=1.0` for non-Euclid, new sets `z0_p=z0`; the difference is a constant factor that cancels in the bin normalization. |
| Photo `z0` | old/new config | - | `z0` | **matched** | `z0 = zm/sqrt(2)` in both. Rubin `zm=0.156`, SKAO `zm=1.1`, DESI-photo `zm=0.9`. |
| `ngal_per_bin` | old/new config | count | `ngalbin_GCph`, `ngalbin_WL` | **matched** | Both compute `(ngal_sqarmin*3600/nbins)*sr` with `sr` the sky area in deg^2. |
| Photo bias | old/new config | - | `photobiaspars` | **matched** | `binned` model generates `b_i = sqrt(1 + 0.5*(z_i+z_{i-1}))` in both. |
| Survey area | old `area_survey` | deg^2 | `area_survey_GCph`, `area_survey_WL`, `area_survey_spectro`, `area_survey_IM` | **different by design** | Current schema is per-probe and an explicit `fsky_*` overrides the area. When migrating, convert a single historical area into the per-probe keys and do not also copy a conflicting `fsky_*`. |
| Old volume formula | old `SpectroCov.volume_bin` | Mpc^3 per deg^2 | `d_volume`, `volume_survey` | **matched** | Old `volume_bin` divides the spherical shell by `4*pi*(180/pi)^2` and `volume_survey` multiplies by `area_survey`; current uses the full shell times `fsky`. Equivalent. |
| Shot noise | old configs | - | `shot_noise_parametrization` | **matched** | `Ps_*` all `0.0` in the saved matrices; still add every key for every bin (see issue 2). |
| FoG / `sigmap` | old configs | - | `nonlinear_parametrization` | **different by design** | Old defaults had `bfs8terms: True`; the JAX GCsp observable requires `False`. The two are algebraically identical at the fiducial (see `docs/source/gcsp_intermediate.md`), so this does not change the Fisher. |
| AP effect | old configs | - | `AP_effect` | **matched** | `True` in both. |
| Fig. 1 spectra | `data-for-fig1.dat` | Mpc^3 | new `P_gg`, `P_II`, `P_Ig` at `z=0.6` | **requires investigation** | Historical curves use the MG fiducial (`E11`, `E22`) and a different backend; expect a non-zero offset. Quantify, do not expect a match. |
| Old MG parameter basis | `vfinal/*.paramnames` | - | - | **out of scope** | `E11`/`E22`/`mu`/`eta` cannot be reproduced; GR runs only. |

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

- [x] `docs/SURVEY_VALIDATION_ROADMAP.md` (this file), kept up to date
- [x] New survey YAMLs under `cosmicjellyfish/configs/other_survey_specifications/`
- [ ] `scripts/validation/run_survey_validation.py` and friends (quick/full)
- [ ] `notebooks/NN-survey-validation.ipynb` (executed)
- [ ] `docs/source/survey_validation.md` + `user_guide.md` link
- [ ] Figures committed under `docs/source/_static/survey_validation/`
- [ ] Tests under `tests/` for configs and observables
      (configs done: `tests/survey_specs_test.py`; observables pending)
- [x] CHANGELOG entry (updated per step)
- [ ] `paper/` figure + paragraph
- [ ] PR

---

## 9. Progress log

Append one line per landed step. Keep it factual: what changed, what was verified, what
is next.

| Date | Step | Result |
| --- | --- | --- |
| 2026-11-13 | Wrote this roadmap | Plan recorded; next is Phase 0 provenance audit |
| 2026-11-13 | Phase 0: read historical `Nuisance`, `GalaxyPhotoDist`, `SpectroCov`, `config.py`, `.dat` tables and old YAMLs | `dn3` identified as dN/dz per deg^2; old and new `n_density`, `volume_survey`, `ngal_per_bin`, photo `dNdz` and photo bias all shown equivalent; assumptions table filled. Remaining Phase 0 item: per-figure mapping of `vfinal/` matrices |
| 2026-11-13 | Phase 1: migrated DESI BGS/ELG, Rubin, SKAO photo/spectro and IM x DESI-ELG specs; fixed the missing `Ps_5`; added `tests/survey_specs_test.py` | Six YAMLs parse, are per-bin consistent, load through `FisherMatrix`, and a DESI BGS `GCsp` forecast runs end-to-end. Next: Phase 2 observable validation |
