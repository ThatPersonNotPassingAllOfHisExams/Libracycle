"""
RecycleTrack Module Template
Copy this file to modules/my_module.py and customize.

Required attributes: NAME, PANEL_CLASS
Optional: DESCRIPTION, ICON, VERSION
"""

NAME = "Modul Exemplu"
DESCRIPTION = "Un modul demonstrativ"
ICON = "🧩"
VERSION = "1.0"

import customtkinter as ctk

class PANEL_CLASS(ctk.CTkFrame):
    """
    This class is instantiated with (parent, app_context).
    app_context gives access to core data functions.
    """
    def __init__(self, parent, app_context):
        super().__init__(parent, fg_color="transparent")
        self.ctx = app_context  # Use ctx.get_records(), ctx.add_record(), etc.
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text=f"👋 Bun venit în {NAME}!",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=40)
        ctk.CTkLabel(self, text="Editează acest fișier pentru a crea modulul tău.",
                     wraplength=400).pack()

    def on_data_change(self):
        """Called by the app when records are added/deleted. Optional."""
        pass
