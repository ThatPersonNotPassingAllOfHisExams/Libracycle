<div align="center">

# ♻ Libracycle

**An open-source, composition-based recyclable waste management system**  
**Un sistem open-source de gestiune a deșeurilor reciclabile, bazat pe compoziție**

---

![Python](https://img.shields.io/badge/Python-3.13+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=flat-square)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-orange?style=flat-square)

</div>

---

## What is Libracycle? / Ce este Libracycle?

**EN:** Libracycle is a desktop app that helps schools and universities keep track of recyclable waste. It figures out your weekly stats, shows your ecological impact, and spits out reports. The whole thing runs on a modular plugin setup—kind of like Winamp’s old skins and plugins. Add what you want, and it just works.

**RO:** Libracycle este o aplicație desktop pentru evidența și analiza deșeurilor reciclabile colectate în școli sau facultăți. Calculează performanța săptămânală, impactul ecologic și generează rapoarte, totul printr-un sistem de module inspirat din arhitectura Winamp.

---

## Quick Start / Pornire rapidă

### Requirements / Cerințe

- Python 3.11 or newer / Python 3.11 sau mai nou
- `customtkinter`
- `matplotlib`

### Installation / Instalare

```bash
# Clone the project and jump in / Clonează proiectul
cd libracycle

# Set up your environment / Creează mediu virtual
python -m venv .venv --system-site-packages   # Linux/macOS
python -m venv .venv                           # Windows

# Activate it / Activează-l
source .venv/bin/activate    # Linux/macOS
.venv\Scripts\activate       # Windows

# Install dependencies / Instalează dependențe
pip install customtkinter matplotlib

# Start the app / Rulează aplicația
python main.py
```

"Extra for Linux folks:"

### Linux (Fedora/Nobara)
```bash
sudo dnf install python3-tkinter python3.13-devel
python3.13 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install customtkinter matplotlib
python main.py
```

### Linux (Ubuntu/Debian)
```bash
sudo apt install python3-tk python3-dev
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install customtkinter matplotlib
python main.py
```

---

## Project Structure / Structura proiectului

```
libracycle/
├── main.py              # App shell / Shell-ul aplicației
├── core.py              # Data, validation, analytics / Date, validare, analiză
├── module_loader.py     # Plugins loader / Încărcător de module
├── io_engine.py         # Import/export (JSON, CSV, TXT)
├── data/
│   └── records.json     # Local database (atomic writes) / Bază de date locală
├── exports/             # Generated reports / Rapoarte generate
└── modules/
    ├── charts_module.py      # Charts / Grafice
    ├── eco_module.py         # Ecological benefits / Beneficii ecologice
    ├── reports_module.py     # Reports & export / Rapoarte și export
    └── _template_module.py   # Template for new modules / Șablon pentru module noi
```

---

## Plugin System / Sistemul de module

Libracycle lets you use plugins just by dropping a .py file into the modules/ folder. The app automatically turns each one into its own tab. If you pull a module out, the app keeps running—your data stays safe.

Libracycle folosește o arhitectură de tip plugin Winamp. Pune orice fișier .py în dosarul modules/ și devine imediat un tab nou în aplicație. Scoate-l, aplicația merge mai departe—datele rămân intacte.

### Minimal module / Modul minimal

```python
NAME = "Modulul Meu / My Module"
ICON = "📈"

import customtkinter as ctk

class PANEL_CLASS(ctk.CTkFrame):
    def __init__(self, parent, app_context):
        super().__init__(parent, fg_color="transparent")
        self.ctx = app_context
        ctk.CTkLabel(self, text="Hello!").pack()

    def on_data_change(self):
        pass  # Called when records are added/deleted
```

### AppContext API

Your module gets `app_context` which come with these methods:

| Method | Returns | Description |
|--------|---------|-------------|
| `get_records(**filters)` | `list[dict]` | All records, that can be filtered |
| `add_record(user, location, date, material, qty)` | `dict` | Add a new record |
| `delete_record(id)` | — | Delete by ID |
| `get_users()` | `list[str]` | All registered users |
| `get_locations()` | `list[str]` | All registered locations |
| `total_by_material(records)` | `dict` | Sum per material |
| `weekly_totals(records)` | `dict` | Sum per week |
| `eco_benefits(records)` | `dict` | Ecological stats |

---

## Safe Mode / Modul Sigur

| Situation / Situație | Behavior / Comportament |
|---|---|
| Module `.py` has errors | Skipped, warning shown / Sărit, avertisment afișat |
| Module panel crashes on init | Isolated error card / Card de eroare izolat |
| All modules missing | Safe mode panel with reload / Panou safe mode cu reîncărcare |
| `records.json` corrupt | Boots read-only, data protected / Pornire read-only, date protejate |
| Partial import file | Per-row errors, valid rows imported / Erori per rând, rândurile valide importate |

---

## Import / Export

| Format | Use / Utilizare |
|--------|----------------|
| **JSON** | Full round-trip export/import, round-trip |
| **CSV** | Easy spreadsheet support (Excel, etc.) |
| **TXT** | Human-readable report with eco stats / Raport lizibil cu statistici eco |

---

## Ecological Equivalents / Echivalente ecologice

| Material | Metrics / Metrici |
|----------|-------------------|
| Hârtie / Paper | Trees saved, water saved, CO₂ reduced |
| Plastic | Oil saved, water saved, CO₂ reduced |
| Metal | Energy saved, water saved, CO₂ reduced |
| Sticlă / Glass | Sand saved, water saved, CO₂ reduced |

---

## License / Licență

MIT — go ahead, use it, change it, share it.
MIT — liber de utilizat, modificat și distribuit.

---

<div align="center">
Made with ♻ and Python
</div>
