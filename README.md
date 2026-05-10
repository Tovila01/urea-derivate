# Search for urea derivate

This folder is prepared for a Git-based Gaussian workflow with local editing and RWTH cluster execution.

## Goal

First reproduce the paper:
- Qiu et al. (2011)
- gas phase
- B3LYP/6-31+G(d,p)
- optimized urea/base complexes
- BSSE-corrected interaction energies

Then extend from thymine to uracil and later to the urea derivative.

## Current structure

- `gaussian_templates/` – Gaussian input templates
- `cluster_templates/` – cluster submission templates
- `scripts/` – helper scripts
- `jobs/` – concrete run folders for submitted calculations
- `results/` – extracted energies/tables/summaries
- `docs/` – notes and protocol details

## Recommended Git workflow

### On your normal machine
1. Commit changes in this project.
2. Push to your remote Git repo.

### On the RWTH cluster
1. Clone once:
   ```bash
   git clone <YOUR-REPO-URL> urea-derivate
   ```
2. Later update with:
   ```bash
   cd urea-derivate
   git pull
   ```
3. Create a concrete job folder under `jobs/`.
4. Copy the needed `.gjf` input there.
5. Submit with the cluster submit script template.
6. After completion, either:
   - commit back selected outputs/summaries, or
   - copy only the important results into `results/` and commit those.

## Important note on large Gaussian files

Do not blindly commit everything.
Usually commit:
- `.gjf`
- small `.log` files if needed
- extracted text summaries / CSV tables
- submission scripts

Usually ignore:
- `.chk`
- `.rwf`
- `.scr`
- very large raw scratch/output files

See `.gitignore`.
