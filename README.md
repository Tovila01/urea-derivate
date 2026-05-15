# Search for urea derivate

This folder is prepared for an ORCA workflow with local editing and RWTH cluster execution.

## Goal

First reproduce the paper:
- Qiu et al. (2011)
- gas phase
- B3LYP/6-31+G(d,p)
- optimized urea/base complexes
- BSSE-corrected interaction energies

Then extend from thymine to uracil and later to the urea derivative.

## Current structure

- `orca_templates/by_base/` – ORCA templates grouped by nucleic-acid base
- `orca_templates/ligands/` – isolated ligand/urea ORCA templates
- `cluster_templates/` – cluster submission templates
- `scripts/` – helper scripts
- `jobs/` – concrete ORCA run folders grouped by base or ligand
- `outputs/` – extracted energies/tables/summaries
- `docs/` – notes and protocol details

The nucleic-acid monomers are kept with their related complexes:
- `jobs/adenine/adenine_opt_freq.*` lives beside `jobs/adenine/*_adenine_opt_freq.*`
- the same pattern is used for cytosine, guanine, thymine, and uracil

## ORCA on RWTH

RWTH's ORCA page says:
- you need to be in the `orca` user group
- you must accept the ORCA EULA first
- after access is granted, load with the exact available version, e.g. on RWTH currently:
  ```bash
  module load ORCA/5.0.4
  ```
- available versions can be checked with:
  ```bash
  module spider ORCA
  ```

The ORCA Slurm template is:
- `cluster_templates/submit_orca.slurm`

Important on RWTH: ORCA needs the full module-provided runtime environment (libraries as well as the executable).
Before submission, do:
```bash
module load ORCA/5.0.4
which orca
echo $ORCA
```
Then submit with exported environment:
```bash
sbatch --export=ALL cluster_templates/submit_orca.slurm <input.inp>
```

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
3. Create or reuse a concrete job folder under `jobs/<base>/` or `jobs/ligands/`.
4. Copy the needed `.inp` input there.
5. Submit with the cluster submit script template.
6. After completion, either:
   - commit back selected outputs/summaries, or
   - copy only the important results into `outputs/` and commit those.

## Important note on large ORCA files

Do not blindly commit everything.
Usually commit:
- `.inp`
- small `.out` files if needed
- extracted text summaries / CSV tables
- submission scripts

Usually ignore:
- scratch files
- temporary density/potential files
- very large raw scratch/output files

See `.gitignore`.
