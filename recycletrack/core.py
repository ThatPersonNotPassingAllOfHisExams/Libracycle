"""
core.py - Libracycle data layer
Handles storage, validation, analytics, materials config, and i18n string loading.
All GUI-free. Nothing here should ever import tkinter.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Materials config
# Stored in data/materials.json so users can add their own without touching code.
# Each material has ecological benefit multipliers per kg collected.
# ---------------------------------------------------------------------------

DEFAULT_MATERIALS = {
    "hârtie": {
        "label_ro": "Hârtie",
        "label_en": "Paper",
        "color": "#4CAF84",
        "eco": {
            "trees_saved":   {"value": 0.017, "label_ro": "copaci salvați",          "label_en": "trees saved"},
            "water_liters":  {"value": 26.0,  "label_ro": "litri apă economisiți",   "label_en": "liters of water saved"},
            "co2_kg":        {"value": 1.1,   "label_ro": "kg CO₂ redus",            "label_en": "kg CO₂ reduced"},
        }
    },
    "plastic": {
        "label_ro": "Plastic",
        "label_en": "Plastic",
        "color": "#2196B5",
        "eco": {
            "oil_liters":   {"value": 0.75, "label_ro": "litri petrol economisiți", "label_en": "liters of oil saved"},
            "water_liters": {"value": 5.0,  "label_ro": "litri apă economisiți",    "label_en": "liters of water saved"},
            "co2_kg":       {"value": 2.5,  "label_ro": "kg CO₂ redus",             "label_en": "kg CO₂ reduced"},
        }
    },
    "metal": {
        "label_ro": "Metal",
        "label_en": "Metal",
        "color": "#E07C3A",
        "eco": {
            "energy_kwh":   {"value": 14.0, "label_ro": "kWh energie economisită",  "label_en": "kWh energy saved"},
            "water_liters": {"value": 40.0, "label_ro": "litri apă economisiți",    "label_en": "liters of water saved"},
            "co2_kg":       {"value": 4.0,  "label_ro": "kg CO₂ redus",             "label_en": "kg CO₂ reduced"},
        }
    },
    "sticlă": {
        "label_ro": "Sticlă",
        "label_en": "Glass",
        "color": "#9C6DB5",
        "eco": {
            "sand_kg":      {"value": 1.2, "label_ro": "kg nisip economisit",       "label_en": "kg of sand saved"},
            "water_liters": {"value": 2.0, "label_ro": "litri apă economisiți",     "label_en": "liters of water saved"},
            "co2_kg":       {"value": 0.3, "label_ro": "kg CO₂ redus",              "label_en": "kg CO₂ reduced"},
        }
    },
}

_MATERIALS_PATH = DATA_DIR / "materials.json"


def _load_materials() -> dict:
    if not _MATERIALS_PATH.exists():
        _save_materials(DEFAULT_MATERIALS)
        return DEFAULT_MATERIALS
    try:
        with open(_MATERIALS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return DEFAULT_MATERIALS


def _save_materials(materials: dict):
    tmp = _MATERIALS_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(materials, f, ensure_ascii=False, indent=2)
    tmp.replace(_MATERIALS_PATH)


def get_materials() -> dict:
    return _load_materials()


def get_material_keys() -> list[str]:
    return list(_load_materials().keys())


def get_material_color(key: str) -> str:
    return _load_materials().get(key, {}).get("color", "#888888")


def get_material_label(key: str, lang: str = "ro") -> str:
    mat = _load_materials().get(key, {})
    return mat.get(f"label_{lang}", key)


def add_material(key: str, label_ro: str, label_en: str,
                 color: str = "#888888", eco: dict = None) -> str:
    key = key.strip().lower()
    if not key:
        raise ValidationError("Cheia materialului nu poate fi goală.")
    if len(key) > 40:
        raise ValidationError("Cheie prea lungă (max 40 caractere).")
    materials = _load_materials()
    if key in materials:
        raise ValidationError(f"Materialul '{key}' există deja.")
    materials[key] = {
        "label_ro": label_ro or key,
        "label_en": label_en or key,
        "color": color,
        "eco": eco or {
            "co2_kg": {"value": 1.0, "label_ro": "kg CO₂ redus", "label_en": "kg CO₂ reduced"}
        }
    }
    _save_materials(materials)
    return key


def remove_material(key: str):
    materials = _load_materials()
    if key not in materials:
        raise ValidationError(f"Materialul '{key}' nu există.")
    del materials[key]
    _save_materials(materials)


# Backwards-compatible alias used by modules
MATERIAL_TYPES = property(get_material_keys)


# ---------------------------------------------------------------------------
# i18n - string tables
# Stored in data/lang/ as JSON files. Falls back to Romanian if key missing.
# ---------------------------------------------------------------------------

_LANG_DIR = APP_DIR / "lang"
_LANG_DIR.mkdir(exist_ok=True)

_STRINGS_RO = {
    "app_title": "Libracycle",
    "add_record": "Adaugă Înregistrare",
    "user": "Utilizator",
    "location": "Locație",
    "date_label": "Dată (YYYY-MM-DD)",
    "material": "Material",
    "quantity_kg": "Cantitate (kg)",
    "btn_add": "＋ Adaugă",
    "manage": "Gestionare",
    "btn_users_locs": "👥 Utilizatori & Locații",
    "btn_delete": "🗑 Șterge Înregistrare",
    "btn_import": "📂 Import",
    "btn_reload": "↻ Reîncarcă Module",
    "status_records": "înregistrări",
    "status_total": "kg total colectat",
    "safe_mode": "⚠ SAFE MODE — date corupte detectate",
    "modules_failed": "modul(e) eșuat(e)",
    "no_data": "Nu există date",
    "settings": "Setări",
    "language": "Limbă",
    "theme": "Temă",
    "save": "Salvează",
    "cancel": "Anulează",
    "confirm_delete": "Șterge înregistrarea #{}?",
    "delete_confirm_title": "Confirmare",
    "import_success": "Import reușit",
    "import_records": "Înregistrări importate: {}",
    "import_rejected": "Respinse: {}",
    "error": "Eroare",
    "validation": "Validare",
    "exported": "Salvat:\n{}",
    "materials_title": "Materiale",
    "add_material": "Adaugă Material",
    "remove_material": "Șterge Material",
    "material_key": "Cheie (ex: carton)",
    "material_label_ro": "Etichetă RO",
    "material_label_en": "Etichetă EN",
    "material_color": "Culoare hex",
}

_STRINGS_EN = {
    "app_title": "Libracycle",
    "add_record": "Add Record",
    "user": "User",
    "location": "Location",
    "date_label": "Date (YYYY-MM-DD)",
    "material": "Material",
    "quantity_kg": "Quantity (kg)",
    "btn_add": "＋ Add",
    "manage": "Manage",
    "btn_users_locs": "👥 Users & Locations",
    "btn_delete": "🗑 Delete Record",
    "btn_import": "📂 Import",
    "btn_reload": "↻ Reload Modules",
    "status_records": "records",
    "status_total": "kg total collected",
    "safe_mode": "⚠ SAFE MODE — corrupt data detected",
    "modules_failed": "module(s) failed",
    "no_data": "No data",
    "settings": "Settings",
    "language": "Language",
    "theme": "Theme",
    "save": "Save",
    "cancel": "Cancel",
    "confirm_delete": "Delete record #{}?",
    "delete_confirm_title": "Confirm",
    "import_success": "Import successful",
    "import_records": "Records imported: {}",
    "import_rejected": "Rejected: {}",
    "error": "Error",
    "validation": "Validation",
    "exported": "Saved:\n{}",
    "materials_title": "Materials",
    "add_material": "Add Material",
    "remove_material": "Remove Material",
    "material_key": "Key (e.g. cardboard)",
    "material_label_ro": "Label RO",
    "material_label_en": "Label EN",
    "material_color": "Hex color",
}

_BUILTIN_LANGS = {"ro": _STRINGS_RO, "en": _STRINGS_EN}
_active_lang = "ro"


def _write_default_lang_files():
    for code, strings in _BUILTIN_LANGS.items():
        p = _LANG_DIR / f"{code}.json"
        if not p.exists():
            with open(p, "w", encoding="utf-8") as f:
                json.dump(strings, f, ensure_ascii=False, indent=2)


_write_default_lang_files()


def set_language(lang_code: str):
    global _active_lang
    _active_lang = lang_code


def get_language() -> str:
    return _active_lang


def available_languages() -> list[str]:
    # Built-ins plus any extra .json files dropped in lang/
    found = {p.stem for p in _LANG_DIR.glob("*.json")}
    return sorted(found | set(_BUILTIN_LANGS.keys()))


def t(key: str, *args) -> str:
    lang_file = _LANG_DIR / f"{_active_lang}.json"
    try:
        with open(lang_file, "r", encoding="utf-8") as f:
            strings = json.load(f)
    except Exception:
        strings = _BUILTIN_LANGS.get(_active_lang, _STRINGS_RO)

    text = strings.get(key) or _STRINGS_RO.get(key, key)
    if args:
        try:
            text = text.format(*args)
        except Exception:
            pass
    return text


# ---------------------------------------------------------------------------
# Config - theme colors and UI preferences saved to data/config.json
# ---------------------------------------------------------------------------

_CONFIG_PATH = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "language": "ro",
    "theme": {
        "bg_main":      "#0d0d1a",
        "bg_panel":     "#16213e",
        "bg_input":     "#0f3460",
        "accent":       "#4CAF84",
        "danger":       "#e94560",
        "text_primary": "#e8e8f0",
        "text_muted":   "#6080a0",
    },
    "window": {
        "width": 1200,
        "height": 750,
    },
    "logo_path": "",
}


def load_config() -> dict:
    if not _CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Merge missing keys from defaults so old configs still work
        for k, v in DEFAULT_CONFIG.items():
            if k not in cfg:
                cfg[k] = v
            elif isinstance(v, dict):
                for k2, v2 in v.items():
                    cfg[k].setdefault(k2, v2)
        return cfg
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG


def save_config(cfg: dict):
    tmp = _CONFIG_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    tmp.replace(_CONFIG_PATH)


def get_theme() -> dict:
    return load_config().get("theme", DEFAULT_CONFIG["theme"])


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    pass


def validate_quantity(value: Any) -> float:
    try:
        v = float(str(value).replace(",", ".").strip())
    except (ValueError, TypeError):
        raise ValidationError(f"Valoare invalidă: '{value}'. Introduceți un număr (ex: 3.5)")
    if v < 0:
        raise ValidationError("Cantitatea nu poate fi negativă.")
    if v > 10000:
        raise ValidationError("Cantitate prea mare (max 10000 kg).")
    return round(v, 3)


def validate_name(value: str, label: str = "Câmp") -> str:
    value = value.strip()
    if not value:
        raise ValidationError(f"{label} nu poate fi gol.")
    if len(value) > 80:
        raise ValidationError(f"{label} prea lung (max 80 caractere).")
    if re.search(r'[<>{}\\]', value):
        raise ValidationError(f"{label} conține caractere interzise.")
    return value


def validate_date(value: str) -> str:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValidationError(f"Dată invalidă: '{value}'. Format: YYYY-MM-DD sau DD.MM.YYYY")


# ---------------------------------------------------------------------------
# Storage - atomic JSON writes, safe-mode detection on corrupt files
# ---------------------------------------------------------------------------

def _db_path() -> Path:
    return DATA_DIR / "records.json"


def _load_raw() -> dict:
    p = _db_path()
    if not p.exists():
        return {"records": [], "users": [], "locations": []}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in ("records", "users", "locations"):
            data.setdefault(key, [])
        return data
    except (json.JSONDecodeError, OSError):
        # File is corrupt. Return empty state, do NOT overwrite.
        return {"records": [], "users": [], "locations": [], "_safe_mode": True}


def _save_raw(data: dict):
    p = _db_path()
    tmp = p.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(p)


def get_db() -> dict:
    return _load_raw()


def is_safe_mode() -> bool:
    return _load_raw().get("_safe_mode", False)


# ---------------------------------------------------------------------------
# Users and locations
# ---------------------------------------------------------------------------

def get_users() -> list[str]:
    return sorted(set(_load_raw()["users"]))


def add_user(name: str) -> str:
    name = validate_name(name, "Utilizator")
    db = _load_raw()
    if name not in db["users"]:
        db["users"].append(name)
        _save_raw(db)
    return name


def remove_user(name: str):
    db = _load_raw()
    db["users"] = [u for u in db["users"] if u != name]
    _save_raw(db)


def get_locations() -> list[str]:
    return sorted(set(_load_raw()["locations"]))


def add_location(name: str) -> str:
    name = validate_name(name, "Locație")
    db = _load_raw()
    if name not in db["locations"]:
        db["locations"].append(name)
        _save_raw(db)
    return name


def remove_location(name: str):
    db = _load_raw()
    db["locations"] = [l for l in db["locations"] if l != name]
    _save_raw(db)


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

def _next_id() -> int:
    db = _load_raw()
    if not db["records"]:
        return 1
    return max(r["id"] for r in db["records"]) + 1


def add_record(user: str, location: str, date_str: str,
               material: str, quantity_kg: Any) -> dict:
    user        = validate_name(user, "Utilizator")
    location    = validate_name(location, "Locație")
    date_str    = validate_date(date_str)
    quantity_kg = validate_quantity(quantity_kg)

    known = get_material_keys()
    if material not in known:
        raise ValidationError(f"Material necunoscut: '{material}'. Materiale valide: {', '.join(known)}")

    record = {
        "id":          _next_id(),
        "user":        user,
        "location":    location,
        "date":        date_str,
        "material":    material,
        "quantity_kg": quantity_kg,
        "created_at":  datetime.now().isoformat(timespec="seconds"),
    }
    db = _load_raw()
    db["records"].append(record)
    if user not in db["users"]:
        db["users"].append(user)
    if location not in db["locations"]:
        db["locations"].append(location)
    _save_raw(db)
    return record


def get_records(user: str = None, location: str = None,
                date_from: str = None, date_to: str = None,
                material: str = None) -> list[dict]:
    records = _load_raw()["records"]
    if user:
        records = [r for r in records if r["user"] == user]
    if location:
        records = [r for r in records if r["location"] == location]
    if material:
        records = [r for r in records if r["material"] == material]
    if date_from:
        records = [r for r in records if r["date"] >= date_from]
    if date_to:
        records = [r for r in records if r["date"] <= date_to]
    return sorted(records, key=lambda r: r["date"])


def delete_record(record_id: int):
    db = _load_raw()
    db["records"] = [r for r in db["records"] if r["id"] != record_id]
    _save_raw(db)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def total_by_material(records: list[dict]) -> dict[str, float]:
    keys = get_material_keys()
    totals = {m: 0.0 for m in keys}
    for r in records:
        if r["material"] in totals:
            totals[r["material"]] = round(totals[r["material"]] + r["quantity_kg"], 3)
    return totals


def weekly_totals(records: list[dict]) -> dict[str, dict[str, float]]:
    keys = get_material_keys()
    weeks: dict[str, dict[str, float]] = {}
    for r in records:
        d    = datetime.strptime(r["date"], "%Y-%m-%d")
        week = d.strftime("%Y-W%W")
        weeks.setdefault(week, {m: 0.0 for m in keys})
        if r["material"] in weeks[week]:
            weeks[week][r["material"]] = round(weeks[week][r["material"]] + r["quantity_kg"], 3)
    return dict(sorted(weeks.items()))


def eco_benefits(records: list[dict]) -> dict[str, dict[str, float]]:
    materials = get_materials()
    totals    = total_by_material(records)
    result    = {}
    for mat_key, kg in totals.items():
        mat_def = materials.get(mat_key, {})
        eco     = mat_def.get("eco", {})
        result[mat_key] = {k: round(v["value"] * kg, 3) for k, v in eco.items()}
    return result


def eco_labels(material_key: str, lang: str = "ro") -> dict[str, str]:
    mat = get_materials().get(material_key, {})
    eco = mat.get("eco", {})
    label_key = f"label_{lang}"
    return {k: v.get(label_key, k) for k, v in eco.items()}


def best_week(records: list[dict]) -> tuple:
    weeks = weekly_totals(records)
    if not weeks:
        return None, None
    totals = {w: sum(v.values()) for w, v in weeks.items()}
    best   = max(totals, key=totals.get)
    return best, totals[best]


def performance_trend(records: list[dict]) -> list[tuple]:
    weeks = weekly_totals(records)
    return [(w, sum(v.values())) for w, v in weeks.items()]
