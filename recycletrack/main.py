"""
main.py - Libracycle application shell
Loads config, builds the window, drops in whatever modules are in modules/.
If a module breaks, the rest of the app keeps running.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, colorchooser
import sys
import os
from pathlib import Path
from datetime import date

APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

import core
import module_loader
import io_engine

# Apply saved language before anything renders
_cfg = core.load_config()
core.set_language(_cfg.get("language", "ro"))

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


# ---------------------------------------------------------------------------
# AppContext - the interface modules talk to instead of importing core directly
# Keeps modules from depending on internals that might change
# ---------------------------------------------------------------------------

class AppContext:
    def get_records(self, **kwargs):
        return core.get_records(**kwargs)

    def add_record(self, user, location, date_str, material, quantity_kg):
        return core.add_record(user, location, date_str, material, quantity_kg)

    def delete_record(self, record_id):
        core.delete_record(record_id)

    def get_users(self):
        return core.get_users()

    def get_locations(self):
        return core.get_locations()

    def add_user(self, name):
        return core.add_user(name)

    def add_location(self, name):
        return core.add_location(name)

    def get_material_keys(self):
        return core.get_material_keys()

    def get_materials(self):
        return core.get_materials()

    def total_by_material(self, records):
        return core.total_by_material(records)

    def weekly_totals(self, records):
        return core.weekly_totals(records)

    def eco_benefits(self, records):
        return core.eco_benefits(records)

    def t(self, key, *args):
        return core.t(key, *args)

    def get_theme(self):
        return core.get_theme()


# ---------------------------------------------------------------------------
# Settings dialog - theme colors, language, logo
# ---------------------------------------------------------------------------

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title(core.t("settings"))
        self.geometry("520x600")
        self.resizable(False, False)
        self._on_save = on_save
        cfg = core.load_config()
        self._theme = dict(cfg.get("theme", core.DEFAULT_CONFIG["theme"]))
        self._lang  = ctk.StringVar(value=cfg.get("language", "ro"))
        self._logo  = ctk.StringVar(value=cfg.get("logo_path", ""))
        self._build()

    def _build(self):
        th = self._theme

        # Header
        ctk.CTkLabel(self, text=f"⚙ {core.t('settings')}",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=th["accent"]).pack(pady=(18, 6))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=4)

        # Language picker
        lang_frame = ctk.CTkFrame(scroll, fg_color=th["bg_panel"], corner_radius=10)
        lang_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(lang_frame, text=core.t("language"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10,4))
        langs = core.available_languages()
        ctk.CTkOptionMenu(lang_frame, variable=self._lang, values=langs,
                          width=160, fg_color=th["bg_input"]).pack(anchor="w", padx=12, pady=(0,10))

        # Logo picker
        logo_frame = ctk.CTkFrame(scroll, fg_color=th["bg_panel"], corner_radius=10)
        logo_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(logo_frame, text="Logo / Imagine header",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10,4))
        logo_row = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_row.pack(fill="x", padx=12, pady=(0,10))
        ctk.CTkEntry(logo_row, textvariable=self._logo, width=280,
                     placeholder_text="Calea către imagine (PNG, JPG)").pack(side="left", padx=(0,6))
        ctk.CTkButton(logo_row, text="Alege...", width=80,
                      command=self._pick_logo,
                      fg_color=th["bg_input"]).pack(side="left")

        # Theme colors
        color_frame = ctk.CTkFrame(scroll, fg_color=th["bg_panel"], corner_radius=10)
        color_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(color_frame, text=core.t("theme"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10,4))

        color_labels = {
            "bg_main":      "Fundal principal / Main background",
            "bg_panel":     "Fundal panouri / Panel background",
            "bg_input":     "Fundal câmpuri / Input background",
            "accent":       "Culoare accent / Accent color",
            "danger":       "Culoare pericol / Danger color",
            "text_primary": "Text principal / Primary text",
            "text_muted":   "Text secundar / Muted text",
        }

        self._color_buttons = {}
        for key, label in color_labels.items():
            row = ctk.CTkFrame(color_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(row, text=label, width=280,
                         font=ctk.CTkFont(size=11), anchor="w").pack(side="left")
            btn = ctk.CTkButton(row, text=self._theme[key], width=120,
                                fg_color=self._theme[key],
                                hover_color=self._theme[key],
                                command=lambda k=key: self._pick_color(k))
            btn.pack(side="right")
            self._color_buttons[key] = btn

        # Reset to defaults button
        ctk.CTkButton(color_frame, text="↺ Reset culori / Reset colors",
                      command=self._reset_colors,
                      fg_color=th["bg_input"], hover_color=th["danger"],
                      height=28).pack(padx=12, pady=(4,10))

        # Save / Cancel
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=12)
        ctk.CTkButton(btn_row, text=core.t("cancel"), width=110,
                      command=self.destroy,
                      fg_color=th["bg_panel"]).pack(side="right", padx=(6,0))
        ctk.CTkButton(btn_row, text=core.t("save"), width=110,
                      command=self._save,
                      fg_color=th["accent"], hover_color="#2a9a64",
                      text_color="#000000").pack(side="right")

    def _pick_logo(self):
        path = filedialog.askopenfilename(
            title="Alege imagine logo",
            filetypes=[("Imagini", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Toate", "*.*")]
        )
        if path:
            self._logo.set(path)

    def _pick_color(self, key: str):
        current = self._theme.get(key, "#ffffff")
        result  = colorchooser.askcolor(color=current, title=f"Alege culoare: {key}")
        if result and result[1]:
            hex_color = result[1]
            self._theme[key] = hex_color
            btn = self._color_buttons[key]
            btn.configure(text=hex_color, fg_color=hex_color, hover_color=hex_color)

    def _reset_colors(self):
        for key, val in core.DEFAULT_CONFIG["theme"].items():
            self._theme[key] = val
            if key in self._color_buttons:
                self._color_buttons[key].configure(
                    text=val, fg_color=val, hover_color=val)

    def _save(self):
        cfg = core.load_config()
        cfg["language"]  = self._lang.get()
        cfg["theme"]     = self._theme
        cfg["logo_path"] = self._logo.get().strip()
        core.save_config(cfg)
        core.set_language(cfg["language"])
        if self._on_save:
            self._on_save()
        self.destroy()
        messagebox.showinfo(core.t("settings"),
                            "Setările au fost salvate.\nRepornește aplicația pentru tema completă.\n\nSettings saved. Restart for full theme.")


# ---------------------------------------------------------------------------
# Materials manager dialog
# ---------------------------------------------------------------------------

class MaterialsDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_change=None):
        super().__init__(parent)
        self.title(core.t("materials_title"))
        self.geometry("560x520")
        self._on_change = on_change
        th = core.get_theme()
        self._th = th
        self._build()

    def _build(self):
        th = self._th
        ctk.CTkLabel(self, text=f"🗂 {core.t('materials_title')}",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=th["accent"]).pack(pady=(16,6))

        # Current materials list
        list_frame = ctk.CTkFrame(self, fg_color=th["bg_panel"], corner_radius=10)
        list_frame.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(list_frame, text="Materiale curente / Current materials",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(8,4))

        self._list_box = ctk.CTkTextbox(list_frame, height=120, fg_color=th["bg_main"],
                                         font=("Courier New", 11))
        self._list_box.pack(fill="x", padx=12, pady=(0,8))
        self._refresh_list()

        # Remove material
        del_row = ctk.CTkFrame(list_frame, fg_color="transparent")
        del_row.pack(fill="x", padx=12, pady=(0,10))
        self._del_var = ctk.StringVar()
        ctk.CTkEntry(del_row, textvariable=self._del_var, width=160,
                     placeholder_text="Cheie material").pack(side="left", padx=(0,6))
        ctk.CTkButton(del_row, text=core.t("remove_material"), width=140,
                      command=self._remove,
                      fg_color="#3a1a1a", hover_color=th["danger"]).pack(side="left")

        # Add material
        add_frame = ctk.CTkFrame(self, fg_color=th["bg_panel"], corner_radius=10)
        add_frame.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(add_frame, text=core.t("add_material"),
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(8,4))

        fields = [
            ("_key_var",      core.t("material_key"),      "ex: carton"),
            ("_lro_var",      core.t("material_label_ro"), "ex: Carton"),
            ("_len_var",      core.t("material_label_en"), "ex: Cardboard"),
            ("_color_var",    core.t("material_color"),    "#888888"),
        ]
        for attr, label, placeholder in fields:
            row = ctk.CTkFrame(add_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(row, text=label, width=160,
                         font=ctk.CTkFont(size=11), anchor="w").pack(side="left")
            var = ctk.StringVar()
            setattr(self, attr, var)
            ctk.CTkEntry(row, textvariable=var, width=200,
                         placeholder_text=placeholder,
                         fg_color=th["bg_input"]).pack(side="left")

        self._err_label = ctk.CTkLabel(add_frame, text="",
                                        font=ctk.CTkFont(size=10),
                                        text_color=th["danger"])
        self._err_label.pack(padx=12)

        ctk.CTkButton(add_frame, text=core.t("add_material"),
                      command=self._add,
                      fg_color="#1a3a2a", hover_color=th["accent"],
                      height=32).pack(padx=12, pady=(2,10))

        ctk.CTkLabel(self,
                     text="Notă: eco-multiplierele pentru materiale noi pot fi editate în\ndata/materials.json\n\nNote: eco multipliers for new materials can be edited in data/materials.json",
                     font=ctk.CTkFont(size=10), text_color=th["text_muted"],
                     justify="center").pack(pady=6)

    def _refresh_list(self):
        self._list_box.configure(state="normal")
        self._list_box.delete("1.0", "end")
        for key, mat in core.get_materials().items():
            self._list_box.insert("end",
                f"  {key:<15} RO: {mat['label_ro']:<15} EN: {mat['label_en']:<15} {mat['color']}\n")
        self._list_box.configure(state="disabled")

    def _add(self):
        self._err_label.configure(text="")
        try:
            core.add_material(
                key=self._key_var.get(),
                label_ro=self._lro_var.get().strip() or self._key_var.get(),
                label_en=self._len_var.get().strip() or self._key_var.get(),
                color=self._color_var.get().strip() or "#888888",
            )
            for attr in ("_key_var", "_lro_var", "_len_var", "_color_var"):
                getattr(self, attr).set("")
            self._refresh_list()
            if self._on_change:
                self._on_change()
        except core.ValidationError as e:
            self._err_label.configure(text=str(e))

    def _remove(self):
        key = self._del_var.get().strip()
        if not key:
            return
        if messagebox.askyesno("Confirmare", f"Șterge materialul '{key}'?", parent=self):
            try:
                core.remove_material(key)
                self._del_var.set("")
                self._refresh_list()
                if self._on_change:
                    self._on_change()
            except core.ValidationError as e:
                messagebox.showerror(core.t("error"), str(e), parent=self)


# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------

class LibracycleApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._cfg = core.load_config()
        self._th  = self._cfg.get("theme", core.DEFAULT_CONFIG["theme"])

        self.title(core.t("app_title"))
        self.geometry(f"{self._cfg['window']['width']}x{self._cfg['window']['height']}")
        self.minsize(900, 600)
        self.configure(fg_color=self._th["bg_main"])

        self._ctx            = AppContext()
        self._module_panels  = []
        self._logo_image     = None

        module_loader.write_template()
        self._load_and_build()

    # -- startup -------------------------------------------------------------

    def _load_and_build(self):
        loaded, failed = module_loader.load_modules()
        self._loaded_modules = loaded
        self._failed_modules = failed
        self._build_ui(loaded, failed)

    def _build_ui(self, loaded, failed):
        th = self._th
        self._build_header(failed)

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)

        sidebar = ctk.CTkFrame(main, fg_color=th["bg_panel"], width=225, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._sidebar = sidebar
        self._build_sidebar(sidebar)

        self._content = ctk.CTkFrame(main, fg_color="transparent")
        self._content.pack(side="left", fill="both", expand=True)

        if not loaded:
            self._build_safe_mode_panel(self._content)
            return

        self._build_tabview(loaded)

        self._status = ctk.CTkLabel(self._content, text="",
                                     font=ctk.CTkFont(size=11),
                                     text_color=th["text_muted"], anchor="w")
        self._status.pack(fill="x", padx=12, pady=(0, 4))
        self._update_status()

    def _build_header(self, failed):
        th = self._th
        header = ctk.CTkFrame(self, fg_color=th["bg_panel"], height=54, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Logo image if configured
        logo_path = self._cfg.get("logo_path", "")
        if logo_path and Path(logo_path).exists():
            try:
                from PIL import Image
                img = Image.open(logo_path).resize((36, 36))
                self._logo_image = ctk.CTkImage(img, size=(36, 36))
                ctk.CTkLabel(header, image=self._logo_image, text="").pack(side="left", padx=(12,4), pady=9)
            except Exception:
                pass  # PIL not installed or image broken — just skip the logo

        ctk.CTkLabel(header, text=f"♻ {core.t('app_title')}",
                     font=ctk.CTkFont(family="Courier New", size=20, weight="bold"),
                     text_color=th["accent"]).pack(side="left", padx=12, pady=10)

        if core.is_safe_mode():
            ctk.CTkLabel(header, text=core.t("safe_mode"),
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=th["danger"]).pack(side="left", padx=12)

        if failed:
            ctk.CTkButton(header,
                          text=f"⚠ {len(failed)} {core.t('modules_failed')}",
                          fg_color="#3a1a1a", hover_color="#6a2a2a",
                          text_color=th["danger"], font=ctk.CTkFont(size=11),
                          command=self._show_failed_modules, width=180).pack(side="left", padx=8)

        # Right-side buttons
        for text, cmd, color in [
            (f"↻ {core.t('btn_reload')}", self._reload_modules, th["bg_input"]),
            (f"📂 {core.t('btn_import')}", self._import_data,   "#1a2a1a"),
            ("⚙",                          self._open_settings,  th["bg_panel"]),
        ]:
            ctk.CTkButton(header, text=text, command=cmd,
                          fg_color=color, hover_color=th["danger"],
                          width=40 if text == "⚙" else 130).pack(side="right", padx=4)

    def _build_tabview(self, loaded):
        th = self._th
        self._tabview = ctk.CTkTabview(
            self._content,
            fg_color=th["bg_main"],
            segmented_button_fg_color=th["bg_panel"],
            segmented_button_selected_color=th["bg_input"],
            segmented_button_selected_hover_color=th["danger"],
            segmented_button_unselected_hover_color="#1a2a4a",
        )
        self._tabview.pack(fill="both", expand=True, padx=6, pady=6)

        self._module_panels = []
        for mod in loaded:
            tab_name = f"{mod.icon} {mod.name}"
            self._tabview.add(tab_name)
            tab_frame = self._tabview.tab(tab_name)
            try:
                panel = mod.panel_class(tab_frame, self._ctx)
                panel.pack(fill="both", expand=True)
                self._module_panels.append(panel)
            except Exception as e:
                err = ctk.CTkFrame(tab_frame, fg_color="#2a0a0a", corner_radius=10)
                err.pack(fill="both", expand=True, padx=20, pady=20)
                ctk.CTkLabel(err,
                             text=f"⚠ '{mod.name}' — eroare la afișare",
                             font=ctk.CTkFont(size=14, weight="bold"),
                             text_color=th["danger"]).pack(pady=(30, 8))
                ctk.CTkLabel(err, text=str(e),
                             font=ctk.CTkFont(family="Courier New", size=11),
                             text_color="#a06060", wraplength=600).pack(pady=4)
                self._module_panels.append(None)

    def _build_sidebar(self, sidebar):
        th = self._th

        ctk.CTkLabel(sidebar, text=core.t("add_record"),
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=th["accent"]).pack(padx=12, pady=(14,6), anchor="w")

        fields = ctk.CTkFrame(sidebar, fg_color="transparent")
        fields.pack(fill="x", padx=10)

        def field_label(text):
            ctk.CTkLabel(fields, text=text, font=ctk.CTkFont(size=11),
                         text_color=th["text_muted"]).pack(anchor="w", pady=(4,0))

        field_label(core.t("user"))
        self._user_var = ctk.StringVar()
        self._user_combo = ctk.CTkComboBox(fields, variable=self._user_var,
                                            values=core.get_users(),
                                            width=200, fg_color=th["bg_input"])
        self._user_combo.pack(pady=(0,4))

        field_label(core.t("location"))
        self._loc_var = ctk.StringVar()
        self._loc_combo = ctk.CTkComboBox(fields, variable=self._loc_var,
                                           values=core.get_locations(),
                                           width=200, fg_color=th["bg_input"])
        self._loc_combo.pack(pady=(0,4))

        field_label(core.t("date_label"))
        self._date_var = ctk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ctk.CTkEntry(fields, textvariable=self._date_var, width=200,
                     fg_color=th["bg_input"]).pack(pady=(0,4))

        field_label(core.t("material"))
        self._mat_var = ctk.StringVar(value=core.get_material_keys()[0])
        self._mat_menu = ctk.CTkOptionMenu(fields, variable=self._mat_var,
                                            values=core.get_material_keys(),
                                            width=200, fg_color=th["bg_input"],
                                            button_color=th["bg_input"],
                                            button_hover_color=th["danger"])
        self._mat_menu.pack(pady=(0,4))

        field_label(core.t("quantity_kg"))
        self._qty_var = ctk.StringVar(value="0")
        ctk.CTkEntry(fields, textvariable=self._qty_var, width=200,
                     fg_color=th["bg_input"]).pack(pady=(0,8))

        self._error_label = ctk.CTkLabel(fields, text="",
                                          font=ctk.CTkFont(size=10),
                                          text_color=th["danger"], wraplength=195)
        self._error_label.pack()

        ctk.CTkButton(sidebar, text=core.t("btn_add"),
                      command=self._add_record,
                      fg_color="#1a4a2a", hover_color=th["accent"],
                      font=ctk.CTkFont(size=14, weight="bold"),
                      height=38).pack(fill="x", padx=10, pady=4)

        ctk.CTkFrame(sidebar, height=1, fg_color="#2a2a4a").pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(sidebar, text=core.t("manage"),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=th["text_muted"]).pack(padx=12, pady=(4,4), anchor="w")

        for label, cmd, color in [
            (core.t("btn_users_locs"), self._open_manage,    th["bg_input"]),
            ("🗂 " + core.t("materials_title"), self._open_materials, "#1a2a3a"),
            (core.t("btn_delete"),     self._open_delete,    "#2a0a0a"),
        ]:
            ctk.CTkButton(sidebar, text=label, command=cmd,
                          fg_color=color, hover_color=th["danger"],
                          height=32).pack(fill="x", padx=10, pady=2)

        ctk.CTkFrame(sidebar, height=1, fg_color="#2a2a4a").pack(fill="x", padx=10, pady=8)

        self._mod_info_label = ctk.CTkLabel(
            sidebar,
            text=f"Module: {len(self._loaded_modules)} active",
            font=ctk.CTkFont(size=10), text_color="#506080")
        self._mod_info_label.pack(padx=12, pady=2, anchor="w")
        ctk.CTkLabel(sidebar, text="modules/ → drop .py to add",
                     font=ctk.CTkFont(size=9), text_color="#304050").pack(padx=12, anchor="w")

    def _build_safe_mode_panel(self, parent):
        th = self._th
        f = ctk.CTkFrame(parent, fg_color="#1a0a0a", corner_radius=12)
        f.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(f, text="⚠ Safe Mode",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=th["danger"]).pack(pady=(50,8))
        ctk.CTkLabel(f,
                     text="Nu a fost găsit niciun modul funcțional.\nDatele sunt intacte.\nAdăugați module în dosarul modules/ și apăsați Reîncarcă.\n\nNo working modules found. Data is intact.\nAdd modules to the modules/ folder and click Reload.",
                     font=ctk.CTkFont(size=13), text_color="#a06060",
                     wraplength=500, justify="center").pack(pady=8)
        ctk.CTkButton(f, text=f"↻ {core.t('btn_reload')}",
                      command=self._reload_modules,
                      fg_color="#3a1020", hover_color=th["danger"], height=40).pack(pady=20)

    # -- actions -------------------------------------------------------------

    def _add_record(self):
        self._error_label.configure(text="")
        try:
            core.add_record(
                self._user_var.get().strip(),
                self._loc_var.get().strip(),
                self._date_var.get().strip(),
                self._mat_var.get(),
                self._qty_var.get().strip(),
            )
            self._user_combo.configure(values=core.get_users())
            self._loc_combo.configure(values=core.get_locations())
            self._notify_modules()
            self._update_status(
                f"✓ {self._qty_var.get()} kg {self._mat_var.get()} — "
                f"{self._user_var.get()} / {self._loc_var.get()}"
            )
        except core.ValidationError as e:
            self._error_label.configure(text=str(e))
        except Exception as e:
            self._error_label.configure(text=f"{core.t('error')}: {e}")

    def _notify_modules(self):
        for panel in self._module_panels:
            if panel and hasattr(panel, "on_data_change"):
                try:
                    panel.on_data_change()
                except Exception:
                    pass

    def _update_status(self, msg: str = ""):
        if not hasattr(self, "_status"):
            return
        records = core.get_records()
        total   = sum(core.total_by_material(records).values())
        base    = f"📦 {len(records)} {core.t('status_records')}  |  ♻ {total:.2f} {core.t('status_total')}"
        self._status.configure(text=f"{msg}   —   {base}" if msg else base)

    def _reload_modules(self):
        if hasattr(self, "_tabview"):
            self._tabview.destroy()
        if hasattr(self, "_status"):
            self._status.destroy()

        loaded, failed = module_loader.reload_modules()
        self._loaded_modules = loaded
        self._failed_modules = failed
        self._module_panels  = []

        if loaded:
            self._build_tabview(loaded)
            self._status = ctk.CTkLabel(self._content, text="",
                                         font=ctk.CTkFont(size=11),
                                         text_color=self._th["text_muted"], anchor="w")
            self._status.pack(fill="x", padx=12, pady=(0,4))

        if hasattr(self, "_mod_info_label"):
            self._mod_info_label.configure(text=f"Module: {len(loaded)} active")

        self._update_status(f"↻ {len(loaded)} module reîncărcate")
        if failed:
            self._show_failed_modules()

    def _show_failed_modules(self):
        th  = self._th
        dlg = ctk.CTkToplevel(self)
        dlg.title("Module Eșuate / Failed Modules")
        dlg.geometry("640x400")
        dlg.configure(fg_color="#1a0a0a")
        ctk.CTkLabel(dlg,
                     text=f"⚠ {len(self._failed_modules)} {core.t('modules_failed')}",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=th["danger"]).pack(pady=(16,8))
        tb = ctk.CTkTextbox(dlg, font=("Courier New", 10),
                             fg_color="#0d0000", text_color="#e09090")
        tb.pack(fill="both", expand=True, padx=12, pady=(0,12))
        for fm in self._failed_modules:
            tb.insert("end", f"── {fm.source_file}\n{fm.error}\n\n")
        tb.configure(state="disabled")

    def _open_settings(self):
        SettingsDialog(self, on_save=lambda: messagebox.showinfo(
            "Libracycle", "Repornește aplicația pentru a aplica toate schimbările.\nRestart the app to apply all changes."))

    def _open_materials(self):
        def on_change():
            keys = core.get_material_keys()
            self._mat_menu.configure(values=keys)
            if self._mat_var.get() not in keys and keys:
                self._mat_var.set(keys[0])
            self._notify_modules()
        MaterialsDialog(self, on_change=on_change)

    def _open_manage(self):
        th  = self._th
        dlg = ctk.CTkToplevel(self)
        dlg.title(core.t("btn_users_locs"))
        dlg.geometry("500x480")
        dlg.configure(fg_color=th["bg_main"])

        for _section, label, get_fn, add_fn, del_fn in [
            ("users", core.t("user") + "i",   core.get_users,     core.add_user,     core.remove_user),
            ("locs",  core.t("location") + "i", core.get_locations, core.add_location, core.remove_location),
        ]:
            f = ctk.CTkFrame(dlg, fg_color=th["bg_panel"], corner_radius=10)
            f.pack(fill="x", padx=14, pady=8)
            ctk.CTkLabel(f, text=label,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(8,2))

            lst = ctk.CTkTextbox(f, height=80, fg_color=th["bg_main"],
                                  font=("Courier New", 11))
            lst.pack(fill="x", padx=12, pady=4)

            def refresh(lst=lst, gf=get_fn):
                lst.configure(state="normal")
                lst.delete("1.0", "end")
                lst.insert("end", "\n".join(gf()) or "(gol)")
                lst.configure(state="disabled")

            refresh()

            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=(0,8))
            var = ctk.StringVar()
            ctk.CTkEntry(row, textvariable=var, width=220,
                         placeholder_text=f"Nume {label.lower()}",
                         fg_color=th["bg_input"]).pack(side="left", padx=(0,6))

            def do_add(var=var, af=add_fn, rf=refresh):
                try:
                    af(var.get())
                    var.set("")
                    rf()
                    self._user_combo.configure(values=core.get_users())
                    self._loc_combo.configure(values=core.get_locations())
                except core.ValidationError as e:
                    messagebox.showerror(core.t("validation"), str(e), parent=dlg)

            def do_del(var=var, df=del_fn, rf=refresh):
                name = var.get().strip()
                if name and messagebox.askyesno("Șterge", f"Șterge '{name}'?", parent=dlg):
                    df(name)
                    var.set("")
                    rf()
                    self._user_combo.configure(values=core.get_users())
                    self._loc_combo.configure(values=core.get_locations())

            ctk.CTkButton(row, text="Adaugă", width=80, command=do_add,
                          fg_color="#1a3a2a", hover_color=th["accent"]).pack(side="left", padx=2)
            ctk.CTkButton(row, text="Șterge", width=80, command=do_del,
                          fg_color="#3a1a1a", hover_color=th["danger"]).pack(side="left", padx=2)

    def _open_delete(self):
        th  = self._th
        dlg = ctk.CTkToplevel(self)
        dlg.title(core.t("btn_delete"))
        dlg.geometry("700x450")
        dlg.configure(fg_color=th["bg_main"])

        ctk.CTkLabel(dlg, text="Selectează înregistrarea / Select record:",
                     font=ctk.CTkFont(size=13)).pack(padx=14, pady=(14,4), anchor="w")

        tb = ctk.CTkTextbox(dlg, font=("Courier New", 11),
                             fg_color="#0d0000", text_color="#e0c0c0")
        tb.pack(fill="both", expand=True, padx=14, pady=4)

        def refresh():
            tb.configure(state="normal")
            tb.delete("1.0", "end")
            for r in core.get_records():
                tb.insert("end",
                    f"[{r['id']:4}] {r['date']}  {r['user']:<20}  "
                    f"{r['location']:<20}  {r['material']:<8}  {r['quantity_kg']} kg\n")
            tb.configure(state="disabled")

        refresh()

        row = ctk.CTkFrame(dlg, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(4,14))
        ctk.CTkLabel(row, text="ID:").pack(side="left")
        id_var = ctk.StringVar()
        ctk.CTkEntry(row, textvariable=id_var, width=80,
                     fg_color=th["bg_input"]).pack(side="left", padx=6)

        def do_delete():
            try:
                rid = int(id_var.get().strip())
                if messagebox.askyesno(core.t("delete_confirm_title"),
                                       core.t("confirm_delete", rid), parent=dlg):
                    core.delete_record(rid)
                    id_var.set("")
                    refresh()
                    self._notify_modules()
                    self._update_status(f"🗑 Șters: #{rid}")
            except ValueError:
                messagebox.showerror(core.t("error"), "ID invalid", parent=dlg)

        ctk.CTkButton(row, text=core.t("btn_delete"), command=do_delete,
                      fg_color="#3a1a1a", hover_color=th["danger"]).pack(side="left", padx=6)

    def _import_data(self):
        path = filedialog.askopenfilename(
            title=core.t("btn_import"),
            filetypes=[("JSON/CSV", "*.json *.csv"), ("JSON", "*.json"), ("CSV", "*.csv")]
        )
        if not path:
            return
        try:
            ext = Path(path).suffix.lower()
            if ext == ".json":
                valid, errors = io_engine.import_json(path)
            elif ext == ".csv":
                valid, errors = io_engine.import_csv(path)
            else:
                messagebox.showerror(core.t("error"), "Format nesuportat (.json sau .csv)")
                return

            if errors:
                err_msg = "\n".join(errors[:10])
                if len(errors) > 10:
                    err_msg += f"\n...și {len(errors)-10} erori."
                messagebox.showwarning(core.t("btn_import"), err_msg)

            count = 0
            for r in valid:
                try:
                    core.add_record(r["user"], r["location"], r["date"],
                                    r["material"], r["quantity_kg"])
                    count += 1
                except Exception:
                    pass

            self._user_combo.configure(values=core.get_users())
            self._loc_combo.configure(values=core.get_locations())
            self._notify_modules()
            self._update_status(f"📂 {count} înregistrări importate din {Path(path).name}")
            messagebox.showinfo(core.t("import_success"),
                                f"{core.t('import_records', count)}\n{core.t('import_rejected', len(errors))}")
        except Exception as e:
            messagebox.showerror(core.t("error"), str(e))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = LibracycleApp()
    app.mainloop()
