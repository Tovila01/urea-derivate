#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
from openbabel import openbabel as ob
from openbabel import pybel


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "jobs" / "ligands"
HEADER = """! B3LYP TightSCF Opt Freq
%basis
  Basis "6-31+G(d,p)"
end
%pal
  nprocs 2
end
%maxcore 1000

#
* xyz 0 1
"""

LIGANDS = {
    "formamide": "NC=O",
    "methylurea": "CNC(N)=O",
    "dimethylurea": "CN(C)C(N)=O",
    "thiourea": "NC(N)=S",
    "biuret": "NC(=O)NC(=O)N",
    "semicarbazide": "NNC(=O)N",
    "phenylurea": "NC(=O)Nc1ccccc1",
}


def format_atom(symbol, xyz):
    return f"{symbol:<2}  {xyz[0]:>12.6f}  {xyz[1]:>12.6f}  {xyz[2]:>12.6f}"


def write_input(path: Path, atoms):
    lines = [HEADER]
    for sym, xyz in atoms:
        lines.append(format_atom(sym, xyz))
    lines.append("*")
    path.write_text("\n".join(lines) + "\n")


def build_geometry(smiles):
    mol = pybel.readstring("smi", smiles)
    mol.addh()
    mol.make3D(forcefield="mmff94", steps=300)
    mol.localopt(forcefield="mmff94", steps=300)

    atoms = []
    for atom in ob.OBMolAtomIter(mol.OBMol):
        vec = atom.GetVector()
        atoms.append((ob.GetSymbol(atom.GetAtomicNum()), np.array([vec.GetX(), vec.GetY(), vec.GetZ()], dtype=float)))
    return atoms


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, smiles in LIGANDS.items():
        out = OUT_DIR / f"{name}_opt_freq.inp"
        write_input(out, build_geometry(smiles))
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
