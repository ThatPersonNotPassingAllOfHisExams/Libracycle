"""
module_loader.py - Libracycle plugin system
Scans modules/ for .py files and loads them at runtime.
A broken module gets skipped — it never takes down the app.
Think Winamp skins: drop a file in, it shows up. Remove it, it's gone.
"""

import importlib.util
import traceback
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

MODULES_DIR = Path(__file__).parent / "modules"
MODULES_DIR.mkdir(exist_ok=True)


@dataclass
class LoadedModule:
    name:        str
    description: str
    panel_class: Any
    icon:        str = "🔌"
    version:     str = "1.0"
    source_file: str = ""
    failed:      bool = False
    error:       str = ""


@dataclass
class FailedModule:
    source_file: str
    error:       str
    name:        str  = "Modul Corupt"
    failed:      bool = True


def load_modules(silent: bool = False) -> tuple[list[LoadedModule], list[FailedModule]]:
    """
    Walk modules/ and attempt to import each .py file.
    Files starting with _ are skipped (templates, helpers).
    Returns two lists: what loaded fine and what didn't.
    """
    loaded = []
    failed = []

    for path in sorted(MODULES_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue

        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            # Duck-type check — we need at minimum NAME and PANEL_CLASS
            if not hasattr(mod, "NAME"):
                raise AttributeError("Module is missing required attribute: NAME")
            if not hasattr(mod, "PANEL_CLASS"):
                raise AttributeError("Module is missing required attribute: PANEL_CLASS")

            loaded.append(LoadedModule(
                name        = getattr(mod, "NAME",        path.stem),
                description = getattr(mod, "DESCRIPTION", ""),
                panel_class = mod.PANEL_CLASS,
                icon        = getattr(mod, "ICON",        "🔌"),
                version     = getattr(mod, "VERSION",     "1.0"),
                source_file = str(path),
            ))

            if not silent:
                print(f"[modules] ✓ {mod.NAME}  ({path.name})")

        except Exception:
            err = traceback.format_exc()
            failed.append(FailedModule(source_file=str(path), error=err, name=path.stem))
            if not silent:
                print(f"[modules] ✗ {path.name}\n{err}")

    return loaded, failed


def reload_modules() -> tuple[list[LoadedModule], list[FailedModule]]:
    return load_modules()


# ---------------------------------------------------------------------------
# Template written to modules/ on first run so developers have a starting point
# ---------------------------------------------------------------------------

MODULE_TEMPLATE = '''\
"""
_template_module.py - Libracycle module template
Copy this to modules/my_module.py and customize.

Required: NAME, PANEL_CLASS
Optional: DESCRIPTION, ICON, VERSION
"""

NAME        = "Modul Exemplu / Example Module"
DESCRIPTION = "Un modul demonstrativ / A demo module"
ICON        = "🧩"
VERSION     = "1.0"

import customtkinter as ctk


class PANEL_CLASS(ctk.CTkFrame):
    """
    Instantiated with (parent, app_context).
    app_context exposes the full data API — see README for the method list.
    """
    def __init__(self, parent, app_context):
        super().__init__(parent, fg_color="transparent")
        self.ctx = app_context
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self,
            text=f"👋 {NAME}",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=40)

        ctk.CTkLabel(
            self,
            text="Editează acest fișier pentru a crea modulul tău.\\nEdit this file to build your module.",
            wraplength=400,
            justify="center",
        ).pack()

    def on_data_change(self):
        """
        Called automatically when a record is added or deleted.
        Use this to refresh your UI. Completely optional to implement.
        """
        pass
'''


def write_template():
    dest = MODULES_DIR / "_template_module.py"
    if not dest.exists():
        dest.write_text(MODULE_TEMPLATE, encoding="utf-8")
