#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import html
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(
    sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DFT_PROJECT_ROOT", Path(__file__).resolve().parents[1])
).expanduser().resolve()
JOBS = ROOT / "jobs"
OUT_DIR = ROOT / "outputs"
OUT_FILE = OUT_DIR / "orca_calculation_results.xlsx"
DONE_MARKER = "ORCA TERMINATED NORMALLY"
HARTREE_TO_KCAL = 627.509474

BASES = {"adenine", "cytosine", "guanine", "thymine", "uracil"}
LIGANDS = {
    "urea",
    "formamide",
    "methylurea",
    "dimethylurea",
    "thiourea",
    "biuret",
    "semicarbazide",
    "phenylurea",
}


def process_table() -> str:
    try:
        return subprocess.check_output(
            ["ps", "-axo", "pid=,ppid=,command="],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return ""


def running_names() -> set[str]:
    table = process_table()
    names: set[str] = set()
    for match in re.finditer(r"([A-Za-z0-9_]+_opt_freq)(?:\.inp|\.gbw|\.scfgrad\.inp|\b)", table):
        names.add(match.group(1))
    return names


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(errors="replace")


def last_float(pattern: str, text: str) -> float | None:
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    return float(matches[-1]) if matches else None


def first_int(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return int(match.group(1)) if match else None


def runtime_seconds(text: str) -> tuple[str | None, float | None]:
    pattern = (
        r"TOTAL RUN TIME:\s+(\d+) days\s+(\d+) hours\s+(\d+) minutes\s+"
        r"(\d+) seconds\s+(\d+) msec"
    )
    match = re.search(pattern, text)
    if not match:
        return None, None
    days, hours, minutes, seconds, msec = [int(x) for x in match.groups()]
    total = days * 86400 + hours * 3600 + minutes * 60 + seconds + msec / 1000
    label = f"{days}d {hours}h {minutes}m {seconds}.{msec:03d}s"
    return label, total


def method_line(inp_text: str) -> str | None:
    for line in inp_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("!"):
            return stripped
    return None


def block_value(pattern: str, inp_text: str) -> str | None:
    match = re.search(pattern, inp_text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def charge_mult(inp_text: str) -> tuple[int | None, int | None]:
    match = re.search(r"^\*\s+xyz\s+(-?\d+)\s+(\d+)", inp_text, flags=re.MULTILINE)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def final_frequencies(text: str) -> list[float]:
    if "VIBRATIONAL FREQUENCIES" not in text:
        return []
    tail = text.split("VIBRATIONAL FREQUENCIES")[-1]
    freqs = []
    for line in tail.splitlines():
        match = re.search(r"^\s*\d+:\s+(-?\d+(?:\.\d+)?)\s+cm\*\*-1", line)
        if match:
            freqs.append(float(match.group(1)))
    return freqs


def classify(folder: str, stem: str) -> tuple[str, str | None, str | None]:
    name = stem.removesuffix("_opt_freq")
    if folder == "ligands":
        return "standalone ligand", None, name
    if name == folder and folder in BASES:
        return "base monomer", folder, None
    if name == "urea":
        return "standalone ligand", None, "urea"
    for base in BASES:
        suffix = f"_{base}"
        if name.endswith(suffix):
            ligand = name[: -len(suffix)]
            return "complex", base, ligand
    return "other", folder if folder in BASES else None, None


def parse_job(inp: Path, running: set[str]) -> dict:
    out = inp.with_suffix(".out")
    inp_text = read(inp)
    out_text = read(out)
    folder = inp.parent.name
    stem = inp.stem
    category, base, ligand = classify(folder, stem)
    charge, mult = charge_mult(inp_text)
    freqs = final_frequencies(out_text)
    runtime_label, runtime_s = runtime_seconds(out_text)

    if DONE_MARKER in out_text:
        status = "DONE"
    elif stem in running:
        status = "RUNNING"
    elif not out.exists():
        status = "QUEUED"
    elif "ORCA finished by error termination" in out_text or "FATAL ERROR" in out_text:
        status = "FAILED"
    else:
        status = "INCOMPLETE"

    return {
        "Status": status,
        "Folder": folder,
        "Job": stem,
        "Category": category,
        "Base": base,
        "Ligand": ligand,
        "Charge": charge,
        "Multiplicity": mult,
        "Method": method_line(inp_text),
        "Basis": block_value(r'Basis\s+"([^"]+)"', inp_text),
        "NProcs": first_int(r"nprocs\s+(\d+)", inp_text),
        "Final Energy Eh": last_float(r"FINAL SINGLE POINT ENERGY\s+(-?\d+\.\d+)", out_text),
        "Total Enthalpy Eh": last_float(r"Total Enthalpy\s+\.\.\.\s+(-?\d+\.\d+)", out_text),
        "Final Gibbs Eh": last_float(r"Final Gibbs free energy\s+\.\.\.\s+(-?\d+\.\d+)", out_text),
        "G-E(el) Eh": last_float(r"G-E\(el\)\s+\.\.\.\s+(-?\d+\.\d+)\s+Eh", out_text),
        "G-E(el) kcal/mol": last_float(r"G-E\(el\)\s+\.\.\.\s+-?\d+\.\d+\s+Eh\s+(-?\d+\.\d+)\s+kcal/mol", out_text),
        "Imaginary Count": first_int(r"Total number of imaginary perturbations\s+\.\.\.\s+(\d+)", out_text),
        "Lowest Frequency cm-1": min(freqs) if freqs else None,
        "Optimization Cycles": len(re.findall(r"GEOMETRY OPTIMIZATION CYCLE", out_text)),
        "SCF Evaluations": len(re.findall(r"FINAL SINGLE POINT ENERGY", out_text)),
        "Runtime": runtime_label,
        "Runtime seconds": runtime_s,
        "Out exists": out.exists(),
        "Output file": str(out.relative_to(ROOT)),
        "Input file": str(inp.relative_to(ROOT)),
        "Last output line": next((line for line in reversed(out_text.splitlines()) if line.strip()), ""),
    }


def xyz_rows(job_rows: list[dict]) -> list[dict]:
    rows = []
    for job in job_rows:
        xyz = ROOT / job["Output file"].replace(".out", ".xyz")
        if not xyz.exists():
            continue
        lines = xyz.read_text(errors="replace").splitlines()
        atom_lines = lines[2:] if len(lines) >= 2 and lines[0].strip().isdigit() else lines
        idx = 0
        for line in atom_lines:
            parts = line.split()
            if len(parts) < 4:
                continue
            try:
                x, y, z = map(float, parts[1:4])
            except ValueError:
                continue
            idx += 1
            rows.append(
                {
                    "Job": job["Job"],
                    "Category": job["Category"],
                    "Base": job["Base"],
                    "Ligand": job["Ligand"],
                    "Atom": idx,
                    "Element": parts[0],
                    "X": x,
                    "Y": y,
                    "Z": z,
                }
            )
    return rows


def binding_rows(job_rows: list[dict]) -> list[dict]:
    energy = {row["Job"]: row["Final Energy Eh"] for row in job_rows if row["Final Energy Eh"] is not None}
    rows = []
    for row in job_rows:
        if row["Category"] != "complex" or row["Final Energy Eh"] is None:
            continue
        base = row["Base"]
        ligand = row["Ligand"]
        base_key = f"{base}_opt_freq"
        if ligand == "urea":
            ligand_keys = ["urea_opt_freq"]
        else:
            ligand_keys = [f"{ligand}_opt_freq"]
        ligand_energy = next((energy[k] for k in ligand_keys if k in energy), None)
        base_energy = energy.get(base_key)
        if base_energy is None or ligand_energy is None:
            delta = None
            delta_kcal = None
            status = "Missing component energy"
        else:
            delta = row["Final Energy Eh"] - base_energy - ligand_energy
            delta_kcal = delta * HARTREE_TO_KCAL
            status = "Calculated"
        rows.append(
            {
                "Complex": row["Job"],
                "Base": base,
                "Ligand": ligand,
                "Complex Energy Eh": row["Final Energy Eh"],
                "Base Energy Eh": base_energy,
                "Ligand Energy Eh": ligand_energy,
                "Binding Energy Eh": delta,
                "Binding Energy kcal/mol": delta_kcal,
                "Status": status,
            }
        )
    return rows


def cell_xml(value, style: int | None = None) -> str:
    style_attr = f' s="{style}"' if style is not None else ""
    if value is None:
        return f"<c{style_attr}/>"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"<c{style_attr}><v>{value}</v></c>"
    if isinstance(value, bool):
        return f'<c{style_attr} t="b"><v>{1 if value else 0}</v></c>'
    text = escape(str(value))
    return f'<c{style_attr} t="inlineStr"><is><t>{text}</t></is></c>'


def col_name(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def sheet_xml(rows: list[list], widths: list[int] | None = None) -> str:
    cols = ""
    if widths:
        cols = "<cols>" + "".join(
            f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>'
            for i, w in enumerate(widths, start=1)
        ) + "</cols>"
    body = []
    for r, row in enumerate(rows, start=1):
        cells = []
        for c, value in enumerate(row, start=1):
            style = 1 if r == 1 else None
            cells.append(f'<c r="{col_name(c)}{r}"' + cell_xml(value, style)[2:])
        body.append(f'<row r="{r}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"{cols}<sheetData>{''.join(body)}</sheetData><autoFilter ref=\"A1:{col_name(len(rows[0]))}{len(rows)}\"/>"
        '<freezePanes/><pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>'
        "</worksheet>"
    )


def rows_from_dicts(dicts: list[dict], columns: list[str]) -> list[list]:
    return [columns] + [[row.get(col) for col in columns] for row in dicts]


def workbook_xml(sheet_names: list[str]) -> str:
    sheets = "".join(
        f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>'
        for i, name in enumerate(sheet_names, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheets}</sheets></workbook>"
    )


def rels_xml(sheet_names: list[str]) -> str:
    rels = []
    for i, _ in enumerate(sheet_names, start=1):
        rels.append(
            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
        )
    rels.append(
        f'<Relationship Id="rId{len(sheet_names)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(rels)
        + "</Relationships>"
    )


def content_types_xml(sheet_count: int) -> str:
    sheets = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        f"{sheets}</Types>"
    )


def styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/><bgColor indexed="64"/></patternFill></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        "</styleSheet>"
    )


def root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def write_xlsx(sheets: list[tuple[str, list[list], list[int] | None]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT_FILE, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml(len(sheets)))
        zf.writestr("_rels/.rels", root_rels_xml())
        zf.writestr("xl/workbook.xml", workbook_xml([name for name, _, _ in sheets]))
        zf.writestr("xl/_rels/workbook.xml.rels", rels_xml([name for name, _, _ in sheets]))
        zf.writestr("xl/styles.xml", styles_xml())
        for i, (_name, rows, widths) in enumerate(sheets, start=1):
            zf.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(rows, widths))


def main() -> None:
    running = running_names()
    jobs = [parse_job(inp, running) for inp in sorted(JOBS.rglob("*_opt_freq.inp"))]
    status_counts = {status: sum(1 for row in jobs if row["Status"] == status) for status in ["DONE", "RUNNING", "QUEUED", "FAILED", "INCOMPLETE"]}
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summary = [
        ["Metric", "Value"],
        ["Generated", now],
        ["Total calculations", len(jobs)],
        ["Done", status_counts["DONE"]],
        ["Running", status_counts["RUNNING"]],
        ["Queued", status_counts["QUEUED"]],
        ["Failed", status_counts["FAILED"]],
        ["Incomplete", status_counts["INCOMPLETE"]],
        ["Completed outputs use marker", DONE_MARKER],
    ]

    job_cols = [
        "Status", "Folder", "Job", "Category", "Base", "Ligand", "Charge", "Multiplicity",
        "Method", "Basis", "NProcs", "Final Energy Eh", "Total Enthalpy Eh", "Final Gibbs Eh",
        "G-E(el) Eh", "G-E(el) kcal/mol", "Imaginary Count", "Lowest Frequency cm-1",
        "Optimization Cycles", "SCF Evaluations", "Runtime", "Runtime seconds",
        "Out exists", "Input file", "Output file", "Last output line",
    ]
    binding = binding_rows(jobs)
    binding_cols = [
        "Complex", "Base", "Ligand", "Complex Energy Eh", "Base Energy Eh", "Ligand Energy Eh",
        "Binding Energy Eh", "Binding Energy kcal/mol", "Status",
    ]
    geom = xyz_rows(jobs)
    geom_cols = ["Job", "Category", "Base", "Ligand", "Atom", "Element", "X", "Y", "Z"]

    notes = [
        ["Note", "Detail"],
        ["Status definition", "DONE means the output contains ORCA TERMINATED NORMALLY."],
        ["Binding energies", "Calculated as E(complex) - E(base) - E(ligand), using final electronic energies only."],
        ["Thermal corrections", "Thermochemistry columns are copied directly from ORCA when available."],
        ["Queued/running jobs", "These may change as calculations continue; rerun this script to refresh the workbook."],
    ]

    sheets = [
        ("Summary", summary, [28, 80]),
        ("All Jobs", rows_from_dicts(jobs, job_cols), [14, 18, 34, 20, 14, 18, 10, 12, 24, 18, 10, 18, 18, 18, 15, 18, 15, 18, 16, 14, 22, 14, 10, 42, 42, 60]),
        ("Binding Energies", rows_from_dicts(binding, binding_cols), [34, 14, 18, 18, 18, 18, 18, 22, 24]),
        ("Final Geometries", rows_from_dicts(geom, geom_cols), [34, 18, 14, 18, 8, 10, 14, 14, 14]),
        ("Notes", notes, [24, 110]),
    ]
    write_xlsx(sheets)
    print(OUT_FILE)


if __name__ == "__main__":
    main()
