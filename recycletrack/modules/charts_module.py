"""
RecycleTrack Built-in Module: Charts & Graphs
"""

NAME = "Grafice"
DESCRIPTION = "Grafice de evoluție, distribuție materiale și performanță săptămânală"
ICON = "📊"
VERSION = "1.3"

import customtkinter as ctk
import tkinter as tk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_OK = True
except ImportError as _e:
    MATPLOTLIB_OK = False
    _mpl_err_msg = str(_e)

import core

PALETTE = {
    "hârtie": "#4CAF84",
    "plastic": "#2196B5",
    "metal":   "#E07C3A",
    "sticlă":  "#9C6DB5",
}
BG   = "#1a1a2e"
FG   = "#e8e8f0"
GRID = "#2a2a4a"


def _safe_draw(canvas):
    """Call canvas.draw() safely regardless of matplotlib version."""
    try:
        canvas.draw()
    except TypeError:
        canvas.draw_idle()


class PANEL_CLASS(ctk.CTkFrame):
    def __init__(self, parent, app_context):
        super().__init__(parent, fg_color="transparent")
        self.ctx = app_context
        self._canvas = None
        self._fig    = None
        self._build()

    def _build(self):
        ctrl = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=10)
        ctrl.pack(fill="x", padx=12, pady=(12, 6))

        ctk.CTkLabel(ctrl, text="Tip grafic:",
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=(12, 6), pady=8)

        self._chart_var = ctk.StringVar(value="Evoluție săptămânală")
        options = ["Evoluție săptămânală", "Distribuție materiale",
                   "Performanță cumulativă", "Top locații"]
        ctk.CTkOptionMenu(ctrl, variable=self._chart_var, values=options,
                          command=lambda _: self._render_chart(),
                          width=220, fg_color="#0f3460",
                          button_color="#e94560").pack(side="left", padx=6, pady=8)

        ctk.CTkButton(ctrl, text="↻ Reîncarcă", width=100, command=self._draw,
                      fg_color="#0f3460", hover_color="#e94560").pack(side="right", padx=12, pady=8)

        self._chart_frame = tk.Frame(self, bg="#0d0d1a")
        self._chart_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        if not MATPLOTLIB_OK:
            tk.Label(self._chart_frame, text="⚠ matplotlib nu este instalat.",
                     fg="#e94560", bg="#0d0d1a", font=("Courier New", 12)).pack(expand=True)
            return

        # Delay first draw so the frame is fully laid out
        self.after(200, self._draw)

    def _clear(self):
        if self._canvas:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None
        if self._fig:
            import matplotlib.pyplot as plt
            plt.close(self._fig)
            self._fig = None

    def _render_chart(self):
        if not MATPLOTLIB_OK:
            return

        self._clear()

        chart_type = self._chart_var.get()
        records    = self.ctx.get_records()

        self._fig = Figure(figsize=(7, 4), dpi=100, facecolor=BG)

        if chart_type == "Distribuție materiale":
            ax = self._fig.add_subplot(111)
            self._draw_pie(ax, records)
        else:
            ax = self._fig.add_subplot(111, facecolor=BG)
            if chart_type == "Evoluție săptămânală":
                self._draw_weekly(ax, records)
            elif chart_type == "Performanță cumulativă":
                self._draw_cumulative(ax, records)
            elif chart_type == "Top locații":
                self._draw_locations(ax, records)
            self._style_axis(ax)

        self._fig.tight_layout(pad=1.8)

        self._canvas = FigureCanvasTkAgg(self._fig, master=self._chart_frame)
        widget = self._canvas.get_tk_widget()
        widget.pack(fill="both", expand=True)
        self._chart_frame.update_idletasks()
        _safe_draw(self._canvas)
        # Schedule a second draw after tk settles
        self.after(150, lambda: _safe_draw(self._canvas) if self._canvas else None)

    def _draw_weekly(self, ax, records):
        weeks_data = core.weekly_totals(records)
        if not weeks_data:
            ax.text(0.5, 0.5, "Nu există date", ha="center", va="center",
                    color=FG, fontsize=14, transform=ax.transAxes)
            return
        weeks  = list(weeks_data.keys())
        x      = list(range(len(weeks)))
        bottom = [0.0] * len(weeks)
        for mat in core.MATERIAL_TYPES:
            vals = [weeks_data[w].get(mat, 0) for w in weeks]
            ax.bar(x, vals, bottom=bottom, label=mat,
                   color=PALETTE[mat], width=0.65, alpha=0.9)
            bottom = [b + v for b, v in zip(bottom, vals)]
        ax.set_xticks(x)
        ax.set_xticklabels(weeks, rotation=35, ha="right", fontsize=8, color=FG)
        ax.set_ylabel("kg", color=FG)
        ax.set_title("Evoluție Săptămânală", color=FG, pad=10)
        ax.legend(facecolor=BG, edgecolor=GRID, labelcolor=FG, fontsize=9)

    def _draw_pie(self, ax, records):
        ax.set_facecolor(BG)
        totals = core.total_by_material(records)
        labels = [m for m, v in totals.items() if v > 0]
        values = [v for m, v in totals.items() if v > 0]
        colors = [PALETTE[m] for m in labels]
        if not values:
            ax.text(0.5, 0.5, "Nu există date", ha="center", va="center",
                    color=FG, fontsize=14, transform=ax.transAxes)
            ax.axis("off")
            return
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, colors=colors, autopct="%1.1f%%",
            startangle=140, pctdistance=0.8,
            wedgeprops={"edgecolor": BG, "linewidth": 2}
        )
        for t in texts:     t.set_color(FG)
        for t in autotexts: t.set_color("white"); t.set_fontsize(9)
        ax.set_title("Distribuție Materiale", color=FG, pad=10)

    def _draw_cumulative(self, ax, records):
        trend = core.performance_trend(records)
        if not trend:
            ax.text(0.5, 0.5, "Nu există date", ha="center", va="center",
                    color=FG, fontsize=14, transform=ax.transAxes)
            return
        weeks      = [t[0] for t in trend]
        cumulative = []
        running    = 0.0
        for _, kg in trend:
            running += kg
            cumulative.append(running)
        x = list(range(len(weeks)))
        ax.fill_between(x, cumulative, alpha=0.2, color="#4CAF84")
        ax.plot(x, cumulative, color="#4CAF84", linewidth=2.5, marker="o", markersize=5)
        ax.set_xticks(x)
        ax.set_xticklabels(weeks, rotation=35, ha="right", fontsize=8, color=FG)
        ax.set_ylabel("kg (cumulativ)", color=FG)
        ax.set_title("Performanță Cumulativă", color=FG, pad=10)

    def _draw_locations(self, ax, records):
        from collections import defaultdict
        loc_totals: dict = defaultdict(float)
        for r in records:
            loc_totals[r["location"]] += r["quantity_kg"]
        if not loc_totals:
            ax.text(0.5, 0.5, "Nu există date", ha="center", va="center",
                    color=FG, fontsize=14, transform=ax.transAxes)
            return
        sorted_locs = sorted(loc_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        locs = [l[0] for l in sorted_locs]
        vals = [l[1] for l in sorted_locs]
        bars = ax.barh(locs, vals, color="#4CAF84", alpha=0.85)
        ax.set_xlabel("kg", color=FG)
        ax.set_title("Top Locații", color=FG, pad=10)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_width() + max(vals) * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}", va="center", color=FG, fontsize=9)

    def _style_axis(self, ax):
        ax.tick_params(colors=FG)
        ax.yaxis.label.set_color(FG)
        ax.xaxis.label.set_color(FG)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID)
        ax.grid(axis="y", color=GRID, linewidth=0.5, alpha=0.6)

    def on_data_change(self):
        self.after(50, self._draw)
