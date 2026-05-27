"""
RecycleTrack Built-in Module: Ecological Benefits
"""

NAME = "Beneficii Ecologice"
DESCRIPTION = "Calculează și vizualizează impactul ecologic al reciclării"
ICON = "🌱"
VERSION = "1.0"

import customtkinter as ctk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import core


CARD_COLORS = {
    "hârtie":  ("#1a3a2a", "#4CAF84", "🌳"),
    "plastic": ("#1a2a3a", "#2196B5", "🛢️"),
    "metal":   ("#3a2a1a", "#E07C3A", "⚡"),
    "sticlă":  ("#2a1a3a", "#9C6DB5", "🏖️"),
}


class PANEL_CLASS(ctk.CTkFrame):
    def __init__(self, parent, app_context):
        super().__init__(parent, fg_color="transparent")
        self.ctx = app_context
        self._cards = {}
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 6))
        ctk.CTkLabel(header, text="🌱 Beneficii Ecologice", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#4CAF84").pack(side="left", padx=16, pady=10)
        ctk.CTkButton(header, text="↻ Actualizează", command=self._refresh,
                      fg_color="#0f3460", hover_color="#4CAF84", width=120).pack(side="right", padx=12)

        self._summary_label = ctk.CTkLabel(header, text="", font=ctk.CTkFont(size=12),
                                            text_color="#a0a0c0")
        self._summary_label.pack(side="right", padx=12)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.columnconfigure((0, 1), weight=1)

        for i, mat in enumerate(core.MATERIAL_TYPES):
            bg, accent, icon = CARD_COLORS[mat]
            card = ctk.CTkFrame(grid, fg_color=bg, corner_radius=12)
            card.grid(row=i // 2, column=i % 2, padx=8, pady=8, sticky="nsew")

            title_row = ctk.CTkFrame(card, fg_color="transparent")
            title_row.pack(fill="x", padx=12, pady=(12, 4))
            ctk.CTkLabel(title_row, text=f"{icon} {mat.upper()}",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=accent).pack(side="left")

            self._cards[mat] = {
                "kg_label": ctk.CTkLabel(card, text="0.000 kg",
                                          font=ctk.CTkFont(size=12), text_color="#a0a0c0"),
                "benefits_frame": ctk.CTkFrame(card, fg_color="transparent"),
            }
            self._cards[mat]["kg_label"].pack(anchor="w", padx=14)
            self._cards[mat]["benefits_frame"].pack(fill="x", padx=14, pady=(4, 12))

        self._refresh()

    def _refresh(self):
        records = self.ctx.get_records()
        totals = core.total_by_material(records)
        eco = core.eco_benefits(records)
        grand = sum(totals.values())

        self._summary_label.configure(text=f"Total: {grand:.2f} kg reciclat")

        for mat in core.MATERIAL_TYPES:
            kg = totals[mat]
            benefits = eco[mat]
            labels_map = core.eco_labels(mat)

            card = self._cards[mat]
            card["kg_label"].configure(text=f"{kg:.3f} kg colectat")

            frame = card["benefits_frame"]
            for w in frame.winfo_children():
                w.destroy()

            for key, val in benefits.items():
                label_text = labels_map.get(key, key)
                row = ctk.CTkFrame(frame, fg_color="transparent")
                row.pack(fill="x", pady=1)
                _, accent, _ = CARD_COLORS[mat]
                ctk.CTkLabel(row, text=f"• {val:.3f}", font=ctk.CTkFont(size=13, weight="bold"),
                             text_color=accent, width=90, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=11),
                             text_color="#c0c0d8", anchor="w").pack(side="left")

    def on_data_change(self):
        self._refresh()
