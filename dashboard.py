"""
PC Pulse — Dashboard de Performance
------------------------------------
Monitor de CPU, RAM, disco e rede em tempo real, com gráficos
desenhados nativamente em Canvas (sem dependências pesadas tipo
matplotlib, pra manter o .exe leve e rápido de compilar).
"""

import tkinter as tk
from tkinter import font as tkfont
import psutil
import time
from collections import deque

# ---------------- Paleta ----------------
BG = "#0B0D10"
PANEL = "#12161C"
PANEL_BORDER = "#1E242C"
BLUE = "#1B3A5C"
BLUE_LIGHT = "#3E7BB6"
YELLOW = "#F2C14E"
TEXT = "#E7ECF2"
MUTED = "#7C8896"

HISTORY_LEN = 60  # pontos de histórico por gráfico
REFRESH_MS = 1000


class Sparkline(tk.Canvas):
    """Gráfico de linha simples, desenhado à mão, sem libs externas."""

    def __init__(self, parent, color, max_value=100, width=280, height=90, **kw):
        super().__init__(parent, width=width, height=height, bg=PANEL,
                          highlightthickness=0, **kw)
        self.color = color
        self.max_value = max_value
        self.data = deque([0] * HISTORY_LEN, maxlen=HISTORY_LEN)
        self.w = width
        self.h = height
        self._draw_grid()

    def _draw_grid(self):
        for i in range(1, 4):
            y = self.h * i / 4
            self.create_line(0, y, self.w, y, fill=PANEL_BORDER, tags="grid")

    def push(self, value):
        self.data.append(value)
        self.redraw()

    def redraw(self):
        self.delete("line", "fill")
        step = self.w / (HISTORY_LEN - 1)
        pts = []
        for i, v in enumerate(self.data):
            x = i * step
            y = self.h - (min(v, self.max_value) / self.max_value) * (self.h - 6) - 3
            pts.append((x, y))

        flat = [c for p in pts for c in p]
        if len(pts) >= 2:
            poly = flat + [self.w, self.h, 0, self.h]
            self.create_polygon(*poly, fill=self._fade(self.color), outline="", tags="fill")
            self.create_line(*flat, fill=self.color, width=2, smooth=True, tags="line")

    @staticmethod
    def _fade(hexcolor):
        # aproxima uma versão "translúcida" misturando com o fundo do painel
        hexcolor = hexcolor.lstrip("#")
        r, g, b = int(hexcolor[0:2], 16), int(hexcolor[2:4], 16), int(hexcolor[4:6], 16)
        pr, pg, pb = int(PANEL[1:3], 16), int(PANEL[3:5], 16), int(PANEL[5:7], 16)
        mix = lambda a, p: int(a * 0.22 + p * 0.78)
        return f"#{mix(r,pr):02x}{mix(g,pg):02x}{mix(b,pb):02x}"


class StatCard(tk.Frame):
    def __init__(self, parent, title, unit, color, max_value=100):
        super().__init__(parent, bg=PANEL, highlightbackground=PANEL_BORDER,
                          highlightthickness=1)
        self.unit = unit

        head = tk.Frame(self, bg=PANEL)
        head.pack(fill="x", padx=16, pady=(14, 0))

        tk.Label(head, text=title, bg=PANEL, fg=MUTED,
                  font=("Segoe UI", 10)).pack(side="left")

        self.value_label = tk.Label(head, text="--", bg=PANEL, fg=color,
                                     font=("Segoe UI Semibold", 20))
        self.value_label.pack(side="right")

        self.spark = Sparkline(self, color, max_value=max_value)
        self.spark.pack(padx=12, pady=(8, 14))

    def update_value(self, value):
        self.value_label.config(text=f"{value:.0f}{self.unit}")
        self.spark.push(value)


class NetCard(tk.Frame):
    """Card de rede: duas linhas (upload/download) na mesma sparkline."""

    def __init__(self, parent):
        super().__init__(parent, bg=PANEL, highlightbackground=PANEL_BORDER,
                          highlightthickness=1)
        head = tk.Frame(self, bg=PANEL)
        head.pack(fill="x", padx=16, pady=(14, 0))
        tk.Label(head, text="REDE", bg=PANEL, fg=MUTED,
                  font=("Segoe UI", 10)).pack(side="left")

        self.value_label = tk.Label(head, text="--", bg=PANEL, fg=YELLOW,
                                     font=("Segoe UI Semibold", 16))
        self.value_label.pack(side="right")

        legend = tk.Frame(self, bg=PANEL)
        legend.pack(fill="x", padx=16)
        tk.Label(legend, text="● Download", bg=PANEL, fg=BLUE_LIGHT,
                  font=("Segoe UI", 8)).pack(side="left")
        tk.Label(legend, text="● Upload", bg=PANEL, fg=YELLOW,
                  font=("Segoe UI", 8)).pack(side="left", padx=(10, 0))

        self.canvas = tk.Canvas(self, width=280, height=80, bg=PANEL, highlightthickness=0)
        self.canvas.pack(padx=12, pady=(6, 14))
        self.down_data = deque([0] * HISTORY_LEN, maxlen=HISTORY_LEN)
        self.up_data = deque([0] * HISTORY_LEN, maxlen=HISTORY_LEN)

    def update_value(self, down_kbs, up_kbs):
        self.value_label.config(text=f"↓{down_kbs:.0f}  ↑{up_kbs:.0f} KB/s")
        self.down_data.append(down_kbs)
        self.up_data.append(up_kbs)
        self._redraw()

    def _redraw(self):
        self.canvas.delete("all")
        w, h = 280, 80
        maxv = max(max(self.down_data), max(self.up_data), 50)
        step = w / (HISTORY_LEN - 1)

        for series, color in ((self.down_data, BLUE_LIGHT), (self.up_data, YELLOW)):
            pts = []
            for i, v in enumerate(series):
                x = i * step
                y = h - (v / maxv) * (h - 6) - 3
                pts.append((x, y))
            flat = [c for p in pts for c in p]
            if len(pts) >= 2:
                self.canvas.create_line(*flat, fill=color, width=2, smooth=True)


class Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PC Pulse — Dashboard de Performance")
        self.configure(bg=BG)
        self.geometry("920x560")
        self.minsize(760, 480)

        self._build_header()
        self._build_grid()

        self.last_net = psutil.net_io_counters()
        self.last_time = time.time()

        self.after(200, self._tick)

    def _build_header(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=28, pady=(24, 10))

        tk.Label(header, text="PC PULSE", bg=BG, fg=TEXT,
                  font=("Segoe UI Semibold", 22)).pack(side="left")

        self.status_dot = tk.Canvas(header, width=10, height=10, bg=BG, highlightthickness=0)
        self.status_dot.pack(side="left", padx=(12, 4), pady=6)
        self.status_dot.create_oval(1, 1, 9, 9, fill=YELLOW, outline="")

        tk.Label(header, text="monitorando em tempo real", bg=BG, fg=MUTED,
                  font=("Segoe UI", 10)).pack(side="left")

        self.clock_label = tk.Label(header, text="", bg=BG, fg=MUTED, font=("Segoe UI", 10))
        self.clock_label.pack(side="right")

    def _build_grid(self):
        grid = tk.Frame(self, bg=BG)
        grid.pack(fill="both", expand=True, padx=28, pady=(6, 24))
        for c in range(2):
            grid.columnconfigure(c, weight=1, uniform="col")
        for r in range(2):
            grid.rowconfigure(r, weight=1, uniform="row")

        self.cpu_card = StatCard(grid, "CPU", "%", YELLOW, max_value=100)
        self.cpu_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))

        self.ram_card = StatCard(grid, "MEMÓRIA RAM", "%", BLUE_LIGHT, max_value=100)
        self.ram_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))

        self.disk_card = StatCard(grid, "DISCO", "%", "#E0793C", max_value=100)
        self.disk_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(10, 0))

        self.net_card = NetCard(grid)
        self.net_card.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))

    def _tick(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        now = time.time()
        net = psutil.net_io_counters()
        dt = max(now - self.last_time, 0.001)
        down_kbs = (net.bytes_recv - self.last_net.bytes_recv) / 1024 / dt
        up_kbs = (net.bytes_sent - self.last_net.bytes_sent) / 1024 / dt
        self.last_net = net
        self.last_time = now

        self.cpu_card.update_value(cpu)
        self.ram_card.update_value(ram)
        self.disk_card.update_value(disk)
        self.net_card.update_value(down_kbs, up_kbs)

        self.clock_label.config(text=time.strftime("%H:%M:%S"))

        self.after(REFRESH_MS, self._tick)


if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()
