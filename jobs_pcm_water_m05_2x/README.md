# PCM water + M05-2X ORCA inputs

These inputs are adapted from the existing gas-phase ORCA jobs in `jobs/`.

Target method adopted from the Blanco et al. guanidinium/nucleobase paper:
- functional: M05-2X
- basis set: 6-311+G(d,p)
- implicit solvent: water PCM

Implementation here:
- ORCA input style
- `! M05-2X TightSCF Opt Freq CPCM(Water)`
- `%basis
  Basis "6-311+G(d,p)"
end`

Notes:
- This is an ORCA-side adaptation of the paper approach, not a byte-for-byte recreation of the original program setup.
- Geometries are copied from the current gas-phase input files as starting coordinates.
- The folder structure mirrors `jobs/` so you can diff gas-phase vs PCM/M05-2X inputs easily.
