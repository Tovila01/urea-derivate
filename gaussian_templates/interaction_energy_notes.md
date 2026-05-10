# Interaction energy notes

## Raw interaction energy

Use SCF electronic energies from the monomer and complex output files:

ΔE = E(complex) - E(urea) - E(base)

Convert Hartree to kJ/mol with:

1 Hartree = 2625.5 kJ/mol

## BSSE-corrected interaction energy

Use the Gaussian `Counterpoise=2` calculation on the optimized complex geometry.
The target value for strict paper-style comparison is the BSSE-corrected interaction energy `ΔE_CP`.

## Practical naming suggestion

- monomer: `urea.chk`, `adenine.chk`, `guanine.chk`, `cytosine.chk`, `uracil.chk`, `thymine.chk`
- complex: `urea_adenine.chk`, etc.
- counterpoise: `urea_adenine_cp.chk`, etc.
