#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from openbabel import openbabel as ob
from openbabel import pybel


ROOT = Path(__file__).resolve().parents[1]
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

BASE_SCAFFOLDS = {
    "adenine": ROOT / "jobs" / "adenine" / "urea_adenine_opt_freq.inp",
    "cytosine": ROOT / "jobs" / "cytosine" / "urea_cytosine_opt_freq.inp",
    "guanine": ROOT / "jobs" / "guanine" / "urea_guanine_opt_freq.inp",
    "thymine": ROOT / "jobs" / "thymine" / "urea_thymine_opt_freq.inp",
    "uracil": ROOT / "jobs" / "uracil" / "urea_uracil_opt_freq.inp",
}


def v_add(a, b):
    return [a[i] + b[i] for i in range(3)]


def v_sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def v_scale(a, s):
    return [a[i] * s for i in range(3)]


def v_dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def v_norm(a):
    return math.sqrt(v_dot(a, a))


def v_unit(a):
    n = v_norm(a)
    if n == 0:
        return [1.0, 0.0, 0.0]
    return [a[i] / n for i in range(3)]


def v_cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def format_atom(sym, xyz):
    return f"{sym:<2}  {xyz[0]:>12.6f}  {xyz[1]:>12.6f}  {xyz[2]:>12.6f}"


def parse_atoms(path: Path):
    atoms = []
    in_geom = False
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not in_geom:
            if line.startswith("* xyz"):
                in_geom = True
            continue
        if line == "*":
            break
        parts = line.split()
        if len(parts) >= 4:
            atoms.append((parts[0], [float(parts[1]), float(parts[2]), float(parts[3])]))
    if len(atoms) < 9:
        raise ValueError(f"Could not parse geometry from {path}")
    return atoms


def as_array(vec):
    return np.array([vec[0], vec[1], vec[2]], dtype=float)


def kabsch_transform(source, target):
    source = np.asarray(source, dtype=float)
    target = np.asarray(target, dtype=float)
    source_center = source.mean(axis=0)
    target_center = target.mean(axis=0)
    x = source - source_center
    y = target - target_center
    cov = x.T @ y
    v, _, wt = np.linalg.svd(cov)
    det = np.sign(np.linalg.det(v @ wt))
    rot = v @ np.diag([1.0, 1.0, det]) @ wt
    return rot, source_center, target_center


def transform_points(points, rot, source_center, target_center):
    points = np.asarray(points, dtype=float)
    return (points - source_center) @ rot + target_center


def reference_core(ligand_atoms, base_atoms):
    base_centroid = np.mean(np.array([xyz for _, xyz in base_atoms], dtype=float), axis=0)
    n_indices = [i for i, (sym, _) in enumerate(ligand_atoms) if sym == "N"]
    c_index = next(i for i, (sym, _) in enumerate(ligand_atoms) if sym == "C")
    o_index = next(i for i, (sym, _) in enumerate(ligand_atoms) if sym == "O")
    n_sorted = sorted(
        n_indices,
        key=lambda i: np.linalg.norm(np.asarray(ligand_atoms[i][1], dtype=float) - base_centroid),
        reverse=True,
    )
    if len(n_sorted) != 2:
        raise ValueError("Expected exactly two nitrogens in the reference urea scaffold")
    return np.array(
        [
            ligand_atoms[n_sorted[0]][1],
            ligand_atoms[n_sorted[1]][1],
            ligand_atoms[c_index][1],
            ligand_atoms[o_index][1],
        ],
        dtype=float,
    )


def make_smiles_variant(smiles, ref_core):
    mol = pybel.readstring("smi", smiles)
    mol.addh()
    mol.make3D(forcefield="mmff94", steps=300)
    mol.localopt(forcefield="mmff94", steps=300)
    obmol = mol.OBMol

    def atom_vec(atom):
        vec = atom.GetVector()
        return np.array([vec.GetX(), vec.GetY(), vec.GetZ()], dtype=float)

    carbonyls = []
    for atom in ob.OBMolAtomIter(obmol):
        if atom.GetAtomicNum() != 6:
            continue
        nbrs = [nbr for nbr in ob.OBAtomAtomIter(atom)]
        if sum(nbr.GetAtomicNum() == 8 for nbr in nbrs) == 1 and sum(nbr.GetAtomicNum() == 7 for nbr in nbrs) == 2:
            carbonyls.append(atom)

    if not carbonyls:
        raise ValueError(f"Could not find a carbonyl carbon in {smiles}")

    carbonyl = carbonyls[0]
    nitrogen_neighbors = [nbr for nbr in ob.OBAtomAtomIter(carbonyl) if nbr.GetAtomicNum() == 7]

    def heavy_neighbor_count(atom):
        return sum(nbr.GetAtomicNum() != 1 and nbr.GetIdx() != carbonyl.GetIdx() for nbr in ob.OBAtomAtomIter(atom))

    n_terminal = min(nitrogen_neighbors, key=heavy_neighbor_count)
    n_amide = max(nitrogen_neighbors, key=heavy_neighbor_count)
    oxygen = next(nbr for nbr in ob.OBAtomAtomIter(carbonyl) if nbr.GetAtomicNum() == 8)

    source_core = np.array(
        [
            atom_vec(n_terminal),
            atom_vec(n_amide),
            atom_vec(carbonyl),
            atom_vec(oxygen),
        ],
        dtype=float,
    )
    rot, source_center, target_center = kabsch_transform(source_core, ref_core)

    transformed = []
    for atom in ob.OBMolAtomIter(obmol):
        xyz = transform_points(atom_vec(atom), rot, source_center, target_center)
        transformed.append((ob.GetSymbol(atom.GetAtomicNum()), xyz))
    return transformed


def methyl_hydrogens(center, axis_from_atom_to_carbon):
    axis = v_unit(axis_from_atom_to_carbon)
    ref = [1.0, 0.0, 0.0]
    if abs(v_dot(axis, ref)) > 0.85:
        ref = [0.0, 1.0, 0.0]
    u = v_unit(v_cross(axis, ref))
    v = v_cross(axis, u)

    c_h = 1.09
    cos_t = 1.0 / 3.0
    sin_t = math.sqrt(8.0 / 9.0)
    hydrogens = []
    for theta in (0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0):
        direction = [
            cos_t * axis[0] + sin_t * (math.cos(theta) * u[0] + math.sin(theta) * v[0]),
            cos_t * axis[1] + sin_t * (math.cos(theta) * u[1] + math.sin(theta) * v[1]),
            cos_t * axis[2] + sin_t * (math.cos(theta) * u[2] + math.sin(theta) * v[2]),
        ]
        hydrogens.append(v_add(center, v_scale(direction, c_h)))
    return hydrogens


def formyl_h(carbon, oxygen, nitrogen):
    uo = v_unit(v_sub(oxygen, carbon))
    un = v_unit(v_sub(nitrogen, carbon))
    direction = v_unit(v_scale(v_add(uo, un), -1.0))
    return v_add(carbon, v_scale(direction, 1.09))


def build_variants(ligand):
    o, n1, n2, c, h1, h2, h3, h4 = ligand

    thiourea = [
        ("S", o[1]),
        ("N", n1[1]),
        ("N", n2[1]),
        ("C", c[1]),
        ("H", h1[1]),
        ("H", h2[1]),
        ("H", h3[1]),
        ("H", h4[1]),
    ]

    fh = formyl_h(c[1], o[1], n1[1])
    formamide = [
        ("O", o[1]),
        ("N", n1[1]),
        ("C", c[1]),
        ("H", h1[1]),
        ("H", h2[1]),
        ("H", fh),
    ]

    # Monomethylurea: methylate the second amide nitrogen.
    c_m1 = v_add(n2[1], v_scale(v_unit(v_sub(h4[1], n2[1])), 1.47))
    m1_h = methyl_hydrogens(c_m1, v_sub(c_m1, n2[1]))
    methylurea = [
        ("O", o[1]),
        ("N", n1[1]),
        ("N", n2[1]),
        ("C", c[1]),
        ("H", h1[1]),
        ("H", h2[1]),
        ("H", h3[1]),
        ("C", c_m1),
        ("H", m1_h[0]),
        ("H", m1_h[1]),
        ("H", m1_h[2]),
    ]

    # 1,3-dimethylurea: methylate both nitrogens.
    c_m2 = v_add(n1[1], v_scale(v_unit(v_sub(h2[1], n1[1])), 1.47))
    c_m3 = v_add(n2[1], v_scale(v_unit(v_sub(h4[1], n2[1])), 1.47))
    m2_h = methyl_hydrogens(c_m2, v_sub(c_m2, n1[1]))
    m3_h = methyl_hydrogens(c_m3, v_sub(c_m3, n2[1]))
    dimethylurea = [
        ("O", o[1]),
        ("N", n1[1]),
        ("N", n2[1]),
        ("C", c[1]),
        ("H", h1[1]),
        ("H", h3[1]),
        ("C", c_m2),
        ("H", m2_h[0]),
        ("H", m2_h[1]),
        ("H", m2_h[2]),
        ("C", c_m3),
        ("H", m3_h[0]),
        ("H", m3_h[1]),
        ("H", m3_h[2]),
    ]

    return {
        "thiourea": thiourea,
        "formamide": formamide,
        "methylurea": methylurea,
        "dimethylurea": dimethylurea,
    }


def build_extended_variants(ligand, base_atoms):
    variants = build_variants(ligand)
    ref_core = reference_core(ligand, base_atoms)
    variants["biuret"] = make_smiles_variant("NC(=O)NC(=O)N", ref_core)
    variants["semicarbazide"] = make_smiles_variant("NNC(=O)N", ref_core)
    variants["phenylurea"] = make_smiles_variant("NC(=O)Nc1ccccc1", ref_core)
    return variants


def write_input(path: Path, atoms, base_atoms):
    lines = [HEADER]
    for sym, xyz in atoms + base_atoms:
        lines.append(format_atom(sym, xyz))
    lines.append("*")
    path.write_text("\n".join(lines) + "\n")


def main():
    for base_name, scaffold in BASE_SCAFFOLDS.items():
        atoms = parse_atoms(scaffold)
        ligand = atoms[:8]
        base_atoms = atoms[8:]
        variants = build_extended_variants(ligand, base_atoms)

        target_dir = scaffold.parent
        for ligand_name, ligand_atoms in variants.items():
            out = target_dir / f"{ligand_name}_{base_name}_opt_freq.inp"
            write_input(out, ligand_atoms, base_atoms)
            print(f"Wrote {out}")


if __name__ == "__main__":
    main()
