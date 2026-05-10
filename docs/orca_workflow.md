# ORCA workflow for the urea/base reproduction project

## Method target
- gas phase
- B3LYP
- 6-31+G(d,p)
- full optimization
- harmonic frequencies

## Files
- `orca_templates/01_monomers/` – monomer opt/freq jobs
- `orca_templates/02_complexes/` – starter dimer opt/freq jobs
- `orca_templates/03_counterpoise/` – ghost-atom single-point templates for BSSE-style correction

## Recommended sequence
1. Run monomer optimizations:
   - urea
   - base
2. Run complex optimization.
3. Extract electronic energies from monomer and complex outputs.
4. Compute raw interaction energy:
   - `ΔE = E(complex) - E(urea) - E(base)`
5. For a counterpoise-style BSSE correction in ORCA:
   - replace the coordinates in the ghost-atom templates with the optimized dimer geometry
   - run:
     - `*_frag1_in_dimer_basis.inp`
     - `*_frag2_in_dimer_basis.inp`
   - combine those with the isolated monomer and dimer energies according to the Boys-Bernardi expression

## RWTH note
RWTH's ORCA help page says you need membership in the `orca` group after accepting the ORCA EULA.
