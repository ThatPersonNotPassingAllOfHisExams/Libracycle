"""
RecycleTrack Built-in Module: Reports
"""

NAME = "Rapoarte"
DESCRIPTION = "Generează și exportă rapoarte detaliate (TXT, JSON, CSV)"
ICON = "📄"
VERSION = "1.0"

import customtkinter as ctk
import tkinter.filedialog as fd
import tkinter.messagebox as mb
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import core
import io_engine
from datetime import datetime


class PANEL_CLASS(ctk.CTkFrame):
    def __init__(self, parent, app_context):
        super().__init__(parent, fg_color="transparent")
        self.ctx = app_context
        self._build()

    def _build(self):
        # Filter bar
        fbar = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=10)
        fbar.pack(fill="x", padx=12, pady=(12, 6))
        ctk.CTkLabel(fbar, text="Filtre:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(12, 6), pady=8)

        self._user_var = ctk.StringVar(value="Toți utilizatorii")
        self._loc_var  = ctk.StringVar(value="Toate locațiile")
        self._mat_var  = ctk.StringVar(value="Toate materialele")
        self._date_from_var = ctk.StringVar(value="")
        self._date_to_var   = ctk.StringVar(value="")

        self._user_menu = ctk.CTkOptionMenu(fbar, variable=self._user_var, values=["Toți utilizatorii"],
                                             width=160, command=lambda _: self._refresh())
        self._user_menu.pack(side="left", padx=4, pady=8)
        self._loc_menu = ctk.CTkOptionMenu(fbar, variable=self._loc_var, values=["Toate locațiile"],
                                            width=160, command=lambda _: self._refresh())
        self._loc_menu.pack(side="left", padx=4, pady=8)

        ctk.CTkLabel(fbar, text="De la:").pack(side="left", padx=(8, 2))
        self._from_entry = ctk.CTkEntry(fbar, textvariable=self._date_from_var, width=100,
                                         placeholder_text="YYYY-MM-DD")
        self._from_entry.pack(side="left", padx=2, pady=8)
        ctk.CTkLabel(fbar, text="Până la:").pack(side="left", padx=(4, 2))
        self._to_entry = ctk.CTkEntry(fbar, textvariable=self._date_to_var, width=100,
                                       placeholder_text="YYYY-MM-DD")
        self._to_entry.pack(side="left", padx=2, pady=8)
        ctk.CTkButton(fbar, text="Aplică", width=80, command=self._refresh,
                      fg_color="#0f3460", hover_color="#e94560").pack(side="left", padx=8)

        # Stats summary row
        self._stats_frame = ctk.CTkFrame(self, fg_color="#0d1b2a", corner_radius=10)
        self._stats_frame.pack(fill="x", padx=12, pady=4)

        # Report text area
        self._text = ctk.CTkTextbox(self, font=("Courier New", 11), fg_color="#0d0d1a",
                                     text_color="#c8d8e8", wrap="none")
        self._text.pack(fill="both", expand=True, padx=12, pady=4)

        # Export bar
        ebar = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=10)
        ebar.pack(fill="x", padx=12, pady=(4, 12))
        ctk.CTkLabel(ebar, text="Exportă:", font=ctk.CTkFont(size=13)).pack(side="left", padx=12, pady=8)
        ctk.CTkButton(ebar, text="📄 TXT", width=90, command=self._export_txt,
                      fg_color="#1a3a2a", hover_color="#4CAF84").pack(side="left", padx=4, pady=8)
        ctk.CTkButton(ebar, text="📊 CSV", width=90, command=self._export_csv,
                      fg_color="#1a2a3a", hover_color="#2196B5").pack(side="left", padx=4, pady=8)
        ctk.CTkButton(ebar, text="🗂️ JSON", width=90, command=self._export_json,
                      fg_color="#3a2a1a", hover_color="#E07C3A").pack(side="left", padx=4, pady=8)

        self._update_filters()
        self._refresh()

    def _update_filters(self):
        users = ["Toți utilizatorii"] + core.get_users()
        locs  = ["Toate locațiile"] + core.get_locations()
        self._user_menu.configure(values=users)
        self._loc_menu.configure(values=locs)

    def _get_filters(self):
        user = self._user_var.get()
        loc  = self._loc_var.get()
        df   = self._date_from_var.get().strip()
        dt   = self._date_to_var.get().strip()
        return (
            None if user == "Toți utilizatorii" else user,
            None if loc  == "Toate locațiile" else loc,
            df or None,
            dt or None,
        )

    def _refresh(self):
        self._update_filters()
        u, l, df, dt = self._get_filters()
        try:
            df_val = core.validate_date(df) if df else None
            dt_val = core.validate_date(dt) if dt else None
        except Exception:
            df_val = dt_val = None

        records = core.get_records(user=u, location=l, date_from=df_val, date_to=dt_val)
        self._current_records = records

        # Stats
        for w in self._stats_frame.winfo_children():
            w.destroy()
        totals = core.total_by_material(records)
        grand = sum(totals.values())
        stat_items = [("Înregistrări", str(len(records))),
                      ("Total kg", f"{grand:.2f}")] + \
                     [(m, f"{kg:.2f} kg") for m, kg in totals.items() if kg > 0]
        for label, val in stat_items:
            f = ctk.CTkFrame(self._stats_frame, fg_color="#0f3460", corner_radius=6)
            f.pack(side="left", padx=6, pady=6)
            ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=14, weight="bold"),
                         text_color="#e8e8f0").pack(padx=10, pady=(4, 0))
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=10),
                         text_color="#7080a0").pack(padx=10, pady=(0, 4))

        # Render text report in text box
        import io
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")

        if not records:
            self._text.insert("end", "  (Nu există înregistrări pentru filtrele selectate)")
        else:
            lines = self._build_text_report(records)
            self._text.insert("end", "\n".join(lines))
        self._text.configure(state="disabled")

    def _build_text_report(self, records):
        totals = core.total_by_material(records)
        grand  = sum(totals.values())
        weeks  = core.weekly_totals(records)
        eco    = core.eco_benefits(records)
        best_w, best_kg = core.best_week(records)
        sep = "─" * 58

        lines = [f"  RAPORT RECYCLETRACK — {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                 sep, ""]
        lines += [f"  Înregistrări: {len(records)}    Total colectat: {grand:.2f} kg", ""]
        lines += ["  MATERIALE:"]
        for mat, kg in totals.items():
            pct = (kg / grand * 100) if grand else 0
            bar = "█" * int(pct / 4)
            lines.append(f"    {mat:<10} {kg:>8.2f} kg  {pct:5.1f}%  {bar}")
        lines.append("")
        if best_w:
            lines += [f"  📅 Cea mai bună săptămână: {best_w} ({best_kg:.2f} kg)", ""]
        lines += ["  EVOLUȚIE SĂPTĂMÂNALĂ:"]
        for week, mats in weeks.items():
            wt = sum(mats.values())
            lines.append(f"    {week}: {wt:.2f} kg")
        lines += ["", "  BENEFICII ECOLOGICE:"]
        for mat, benefits in eco.items():
            if totals[mat] > 0:
                lines.append(f"    {mat.upper()} ({totals[mat]:.2f} kg):")
                labels = core.ECO_LABELS[mat]
                for k, v in benefits.items():
                    lines.append(f"      • {v:.3f} {labels.get(k, k)}")
        return lines

    def _export_txt(self):
        path = fd.asksaveasfilename(defaultextension=".txt",
                                     filetypes=[("Text", "*.txt")],
                                     title="Salvează raport TXT")
        if not path: return
        try:
            io_engine.export_txt_report(self._current_records, path=path)
            mb.showinfo("Export", f"Raport salvat:\n{path}")
        except Exception as e:
            mb.showerror("Eroare", str(e))

    def _export_csv(self):
        path = fd.asksaveasfilename(defaultextension=".csv",
                                     filetypes=[("CSV", "*.csv")],
                                     title="Salvează CSV")
        if not path: return
        try:
            io_engine.export_csv(self._current_records, path=path)
            mb.showinfo("Export", f"CSV salvat:\n{path}")
        except Exception as e:
            mb.showerror("Eroare", str(e))

    def _export_json(self):
        path = fd.asksaveasfilename(defaultextension=".json",
                                     filetypes=[("JSON", "*.json")],
                                     title="Salvează JSON")
        if not path: return
        try:
            io_engine.export_json(self._current_records, path=path)
            mb.showinfo("Export", f"JSON salvat:\n{path}")
        except Exception as e:
            mb.showerror("Eroare", str(e))

    def on_data_change(self):
        self._refresh()
