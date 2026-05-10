# Gaussian templates for urea/base interaction workflow

Protocol aligned to:
- gas phase
- B3LYP/6-31+G(d,p)
- geometry optimization + frequency
- BSSE-corrected interaction energies via Counterpoise

## Folder structure

- `01_monomers/` → isolated urea and base optimizations
- `02_complexes/` → urea···base complex optimizations
- `03_counterpoise/` → BSSE-corrected single-point jobs on optimized complexes

## Intended workflow

1. Optimize monomers:
   - urea
   - adenine
   - guanine
   - cytosine
   - uracil
   - thymine
2. Build starting complex geometries from optimized monomers.
3. Optimize each complex.
4. Run counterpoise calculations on the optimized complex geometries.
5. Compute interaction energies:

   - Raw:
     `ΔE = E(complex) - E(urea) - E(base)`
   - BSSE-corrected:
     use Gaussian Counterpoise output (`ΔE_CP` target)

## Notes

- Monomer coordinates are now filled with PubChem 3D starter geometries.
- Complex coordinates are filled with approximate hydrogen-bonded starter arrangements intended for optimization, not exact reproductions of the paper's final motifs.
- For strict paper reproduction, include thymine.
- For RNA extension, include uracil.
- Use the optimized complex geometry for the counterpoise job.
