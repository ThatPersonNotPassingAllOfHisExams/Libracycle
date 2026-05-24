"""
io_engine.py - Libracycle import/export
Handles JSON (full round-trip), CSV (flat table), and TXT (human report).
Every import validates row by row — bad rows are collected and reported,
good rows still go through. Nothing here touches the GUI.
"""

import json
import csv
from datetime import datetime
from pathlib import Path

EXPORTS_DIR = Path(__file__).parent / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_json(records: list[dict], path: str = None) -> str:
    if path is None:
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(EXPORTS_DIR / f"libracycle_export_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "exported_at": datetime.now().isoformat(),
            "records":     records,
        }, f, ensure_ascii=False, indent=2)
    return path


def export_csv(records: list[dict], path: str = None) -> str:
    if path is None:
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(EXPORTS_DIR / f"libracycle_export_{ts}.csv")
    if not records:
        open(path, "w").close()
        return path
    fieldnames = ["id", "date", "user", "location", "material", "quantity_kg", "created_at"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    return path


def export_txt_report(records: list[dict], path: str = None,
                      title: str = "Raport Libracycle", lang: str = "ro") -> str:
    import core
    if path is None:
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(EXPORTS_DIR / f"libracycle_report_{ts}.txt")

    totals      = core.total_by_material(records)
    grand_total = sum(totals.values())
    weeks       = core.weekly_totals(records)
    eco         = core.eco_benefits(records)
    best_w, best_kg = core.best_week(records)
    materials   = core.get_materials()

    sep = "=" * 60
    lines = [sep, f"  {title}", f"  {datetime.now().strftime('%d.%m.%Y %H:%M')}", sep, ""]

    lines += [
        "SUMAR / SUMMARY:",
        f"  Înregistrări / Records: {len(records)}",
        f"  Total colectat / Total collected: {grand_total:.2f} kg",
        "",
    ]

    lines += ["CANTITĂȚI PE MATERIAL / QUANTITIES BY MATERIAL:"]
    for mat, kg in totals.items():
        pct   = (kg / grand_total * 100) if grand_total else 0
        bar   = "█" * int(pct / 5)
        label = materials.get(mat, {}).get(f"label_{lang}", mat)
        lines.append(f"  {label:<14} {kg:>8.2f} kg  {pct:5.1f}%  {bar}")
    lines.append("")

    if best_w:
        lines += [f"CEA MAI BUNĂ SĂPTĂMÂNĂ / BEST WEEK: {best_w}  ({best_kg:.2f} kg)", ""]

    lines += ["EVOLUȚIE SĂPTĂMÂNALĂ / WEEKLY EVOLUTION:"]
    for week, mats in weeks.items():
        week_total = sum(mats.values())
        lines.append(f"  {week}: {week_total:.2f} kg")
        for mat, kg in mats.items():
            if kg > 0:
                label = materials.get(mat, {}).get(f"label_{lang}", mat)
                lines.append(f"    ├─ {label}: {kg:.2f} kg")
    lines.append("")

    lines += ["BENEFICII ECOLOGICE / ECOLOGICAL BENEFITS:"]
    for mat, benefits in eco.items():
        if totals.get(mat, 0) > 0:
            label  = materials.get(mat, {}).get(f"label_{lang}", mat)
            labels = core.eco_labels(mat, lang)
            lines.append(f"  {label.upper()} ({totals[mat]:.2f} kg):")
            for key, val in benefits.items():
                lines.append(f"    • {val:.3f} {labels.get(key, key)}")

    lines += ["", sep, "  Libracycle — open-source waste tracking", sep]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


# ---------------------------------------------------------------------------
# Import
# Rows that fail validation are collected in an errors list.
# Valid rows are returned separately — caller decides what to do with each.
# ---------------------------------------------------------------------------

def _validate_row(row: dict, index: int) -> tuple[dict | None, list[str]]:
    """
    Validate a single record dict coming from an import file.
    Returns (clean_record, []) on success or (None, [error_strings]) on failure.
    """
    import core
    errors = []

    try:
        user = core.validate_name(row.get("user", ""), "Utilizator")
    except core.ValidationError as e:
        errors.append(str(e)); user = None

    try:
        location = core.validate_name(row.get("location", ""), "Locație")
    except core.ValidationError as e:
        errors.append(str(e)); location = None

    try:
        date_str = core.validate_date(row.get("date", ""))
    except core.ValidationError as e:
        errors.append(str(e)); date_str = None

    material = row.get("material", "")
    if material not in core.get_material_keys():
        errors.append(f"Material necunoscut: '{material}'")

    try:
        qty = core.validate_quantity(row.get("quantity_kg", 0))
    except core.ValidationError as e:
        errors.append(str(e)); qty = None

    if errors:
        return None, [f"Rând {index}: {'; '.join(errors)}"]

    return {
        "user":        user,
        "location":    location,
        "date":        date_str,
        "material":    material,
        "quantity_kg": qty,
    }, []


def import_json(path: str) -> tuple[list[dict], list[str]]:
    errors = []
    valid  = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return [], [f"Fișier JSON invalid: {e}"]

    raw = data if isinstance(data, list) else data.get("records", [])
    for i, row in enumerate(raw, 1):
        record, row_errors = _validate_row(row, i)
        if record:
            valid.append(record)
        else:
            errors.extend(row_errors)
    return valid, errors


def import_csv(path: str) -> tuple[list[dict], list[str]]:
    errors = []
    valid  = []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                record, row_errors = _validate_row(row, i)
                if record:
                    valid.append(record)
                else:
                    errors.extend(row_errors)
    except OSError as e:
        return [], [f"Nu se poate citi fișierul: {e}"]
    return valid, errors
