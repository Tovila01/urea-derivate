# Reproduction protocol: Qiu et al. 2011

## Method
- Gaussian 03
- gas phase
- B3LYP/6-31+G(d,p)
- full optimization
- harmonic frequencies for stationary point verification
- BSSE correction included for hydrogen-bonding energies

## First reproduction target
DNA bases:
- adenine
- thymine
- guanine
- cytosine

Then RNA extension:
- uracil

## Main comparison targets from the paper
BSSE-corrected interaction energies `ΔE_CP` in kJ/mol:
- A1 -19.9
- A2 -20.3
- A3 -48.1
- A4 -45.0
- A5 -29.9
- T1 -45.6
- T2 -47.7
- T3 -25.7
- G1 -74.0
- G2 -41.2
- G3 -38.4
- G4 -45.2
- C1 -43.0
- C2 -62.5

## Notes
- No PCM in the reproduction setup
- No evidence that ZPE/thermal corrections were included in the reported interaction energies
- Use `ΔE_CP` as the main comparison quantity
