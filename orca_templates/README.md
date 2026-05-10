# ORCA templates for urea/base interaction workflow

Protocol target:
- gas phase
- B3LYP/6-31+G(d,p)
- geometry optimization + frequency
- BSSE evaluation via ghost-atom counterpoise-style single points

## Layout
- `01_monomers/` – isolated monomer optimizations
- `02_complexes/` – urea···base starter complex optimizations
- `03_counterpoise/` – ORCA ghost-atom single-point templates

## Notes
- Monomer and complex coordinates are explicit starters.
- Complexes are reasonable hydrogen-bonded starting guesses, not exact reproduced paper minima.
- For BSSE work in ORCA, use the optimized dimer geometry from the completed complex job, then run the two ghost-atom jobs in `03_counterpoise/`.
- Raw interaction energy is still `E(complex) - E(urea) - E(base)`.
