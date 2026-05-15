# DFT ORCA Queue Tools

This folder contains the small tools used to monitor, summarize, queue, and reschedule the ORCA DFT calculations for Tom's urea-derivative project.

## Project Location

Current ORCA project root:

```bash
/Users/tomvincent/Downloads/RWTH Studium/Chemie/Master 3. Semester/Trinity College Dublin/DFT/urea-derivate
```

The project root is the folder that contains:

```text
jobs/
scripts/
outputs/
```

All tools in this bundle can be run from this external folder by passing the project root as the first argument, or by setting `DFT_PROJECT_ROOT`.

## Included Tools

- `orca_queue_gui.py`: Tkinter GUI that shows running, queued, and done calculations. Select a job and press `Show Tail` to see the latest output tail.
- `export_orca_results_xlsx.py`: creates a structured Excel workbook with status, final energies, thermochemistry values, binding-energy estimates, geometry coordinates, and notes.
- `run_missing_calculations_queue.sh`: scans all `jobs/**/*_opt_freq.inp`, skips outputs that contain `ORCA TERMINATED NORMALLY`, and runs missing calculations with up to 4 concurrent ORCA jobs.
- `generate_ligand_complexes.py`: regenerates complex inputs for urea derivatives and bases.
- `generate_ligand_monomers.py`: regenerates standalone ligand optimization inputs.

## Open The GUI

```bash
python3 orca_queue_gui.py "/Users/tomvincent/Downloads/RWTH Studium/Chemie/Master 3. Semester/Trinity College Dublin/DFT/urea-derivate"
```

The GUI reads:

- `.inp` files as the list of expected jobs
- `.out` files for completion markers
- the process table for currently running ORCA jobs

Status logic:

- `done`: matching `.out` contains `ORCA TERMINATED NORMALLY`
- `running`: job name appears in the live ORCA process table
- `queued`: input exists, but no normal termination marker and not currently running

## Export The Excel Overview

```bash
python3 export_orca_results_xlsx.py "/Users/tomvincent/Downloads/RWTH Studium/Chemie/Master 3. Semester/Trinity College Dublin/DFT/urea-derivate"
```

Output:

```text
outputs/orca_calculation_results.xlsx
```

Workbook sheets:

- `Summary`
- `All Jobs`
- `Binding Energies`
- `Final Geometries`
- `Notes`

Binding energies are electronic-energy estimates:

```text
E_binding = E_complex - E_base - E_ligand
```

Units are reported in Hartree and kcal/mol.

## Queue All Missing Calculations

Use this when some `.inp` files have no `.out`, failed `.out`, or incomplete `.out`.

```bash
cd "/Users/tomvincent/Downloads/RWTH Studium/Chemie/Master 3. Semester/Trinity College Dublin/DFT/urea-derivate"
screen -L -dmS missingqueue ./scripts/run_missing_calculations_queue.sh
```

From this external bundle folder, use:

```bash
screen -L -dmS missingqueue /bin/bash run_missing_calculations_queue.sh "/Users/tomvincent/Downloads/RWTH Studium/Chemie/Master 3. Semester/Trinity College Dublin/DFT/urea-derivate"
```

Watch it:

```bash
screen -r missingqueue
```

Detach from screen:

```text
Ctrl-A, then D
```

Check screen sessions:

```bash
screen -ls
```

## Reschedule A Calculation

To rerun a calculation, keep the `.inp` file and remove files with the same job prefix. Example for `jobs/uracil/formamide_uracil_opt_freq.inp`:

```bash
cd "/Users/tomvincent/Downloads/RWTH Studium/Chemie/Master 3. Semester/Trinity College Dublin/DFT/urea-derivate"
find jobs/uracil -maxdepth 1 -type f -name "formamide_uracil_opt_freq*" ! -name "formamide_uracil_opt_freq.inp" -delete
screen -L -dmS missingqueue ./scripts/run_missing_calculations_queue.sh
```

The queue script will see that `formamide_uracil_opt_freq.out` is missing and run it again.

## Important ORCA/MPI Note

ORCA is installed here:

```bash
/Users/tomvincent/Applications/orca_6_1_1_macosx_arm64_openmpi411/orca
```

The queue script exports:

```bash
DYLD_LIBRARY_PATH=/opt/homebrew/lib
```

For standalone ligand jobs in `jobs/ligands`, ORCA previously failed because `libmpi.40.dylib` was not found from that working directory. The fix was:

```bash
ln -sf /opt/homebrew/lib/libmpi.40.dylib jobs/ligands/libmpi.40.dylib
```

If ligand jobs fail at ORCA startup with `Library not loaded: libmpi.40.dylib`, check that this symlink exists.

## Find Missing Jobs Manually

```bash
cd "/Users/tomvincent/Downloads/RWTH Studium/Chemie/Master 3. Semester/Trinity College Dublin/DFT/urea-derivate"
find jobs -type f -name '*_opt_freq.inp' | while IFS= read -r inp; do
  out="${inp%.inp}.out"
  if [ ! -s "$out" ] || ! grep -q 'ORCA TERMINATED NORMALLY' "$out"; then
    printf '%s\n' "$inp"
  fi
done | sort
```

## Check Live ORCA Jobs

```bash
ps -axo pid=,ppid=,command= | rg 'prterun -np 2|orca_6_1_1_macosx_arm64_openmpi411/orca|orca_(leanscf|scfgrad|prop|main|tools|scfresp)'
```

## Tail A Running Output

```bash
tail -f "jobs/adenine/biuret_adenine_opt_freq.out"
```

## Regenerate Inputs

Complexes:

```bash
python3 scripts/generate_ligand_complexes.py
```

Standalone ligands:

```bash
python3 scripts/generate_ligand_monomers.py
```

These scripts use OpenBabel for initial ligand geometries.

## Recommended Agent Workflow

1. Check live state with `screen -ls` and the process-table command.
2. Check missing jobs with the manual missing-job command.
3. If the machine is idle and jobs are missing, start `missingqueue`.
4. If a job must be rerun, delete only files matching that job prefix except `.inp`, then restart `missingqueue`.
5. Use the GUI for live monitoring and output tailing.
6. Use `export_orca_results_xlsx.py` after calculations finish to refresh the Excel overview.

