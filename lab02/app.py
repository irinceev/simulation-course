import tkinter as tk
from tkinter import ttk
import numpy as np
import time
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from solver import simulate, calculate_next_step

class Colors:
    BG_MAIN = "#f8f9fa"
    BG_CARD = "#ffffff"
    BG_INPUT = "#ffffff"
    BG_HEADER = "#f1f3f4"
    
    TEXT_PRIMARY = "#212529"
    TEXT_SECONDARY = "#6c757d"
    TEXT_INVERTED = "#ffffff"
    
    ACCENT = "#007bff"  # ✅ ИСПРАВЛЕНО: был белый!
    ACCENT_HOVER = "#0056b3"
    
    TEMP_ACCENT = "#fd7e14"
    
    BORDER = "#dee2e6"
    GRID_LINE = "#e9ecef"
    PLOT_LINE = "#007bff"
    
    SUCCESS = "#28a745"
    WARNING = "#ffc107"
    ERROR = "#dc3545"

class Fonts:
    TITLE = ("Segoe UI", 18, "bold")
    SUBTITLE = ("Segoe UI", 12)
    
    LABEL = ("Segoe UI", 11)
    LABEL_SMALL = ("Segoe UI", 10)
    
    VALUE = ("Consolas", 11)
    STATUS_VALUE = ("Segoe UI", 14, "bold")
    
    BUTTON = ("Segoe UI", 11, "bold")

class HeatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Теплопроводность")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 750)
        self.root.configure(bg=Colors.BG_MAIN)
        
        self.materials = {
            "Медь": {"Плотность": 8960, "Теплоёмкость": 385, "Теплопроводность": 401, "Длина": 0.1},
            "Алюминий": {"Плотность": 2700, "Теплоёмкость": 900, "Теплопроводность": 237, "Длина": 0.1},
            "Сталь": {"Плотность": 7850, "Теплоёмкость": 475, "Теплопроводность": 50, "Длина": 0.1},
        }
        self.current_material = "Медь"
        
        self.running = False
        self.animation_job = None

        self.setup_styles()
        self.create_layout()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=Colors.BG_MAIN)
        
        style.configure("Header.TLabel",
                       font=Fonts.TITLE,
                       background=Colors.BG_MAIN,
                       foreground=Colors.TEXT_PRIMARY)
        style.configure("SubHeader.TLabel",
                       font=Fonts.SUBTITLE,
                       background=Colors.BG_MAIN,
                       foreground=Colors.TEXT_SECONDARY)

        style.configure("TLabel",
                       background=Colors.BG_CARD,
                       font=Fonts.LABEL,
                       foreground=Colors.TEXT_PRIMARY)
        style.configure("Info.TLabel",
                       background=Colors.BG_CARD,
                       font=Fonts.LABEL_SMALL,
                       foreground=Colors.TEXT_SECONDARY)

        style.configure("TEntry",
                       fieldbackground=Colors.BG_INPUT,
                       foreground=Colors.TEXT_PRIMARY,
                       font=Fonts.VALUE,
                       borderwidth=1,
                       relief="solid")

        # ✅ ОБЫЧНЫЕ КНОПКИ — БЕЗ СТИЛЕЙ!
        style.configure("Treeview",
                       background=Colors.BG_CARD,
                       foreground=Colors.TEXT_PRIMARY,
                       font=Fonts.LABEL_SMALL,
                       rowheight=28,
                       borderwidth=1,
                       relief="solid")
        style.configure("Treeview.Heading",
                       font=Fonts.LABEL,
                       background=Colors.BG_HEADER,
                       foreground=Colors.TEXT_PRIMARY)
        style.map("Treeview",
                 background=[("selected", Colors.ACCENT)],
                 foreground=[("selected", Colors.TEXT_INVERTED)])

        style.configure("TNotebook",
                       background=Colors.BG_MAIN,
                       borderwidth=1)
        style.configure("TNotebook.Tab",
                       font=Fonts.LABEL,
                       padding=[12, 8])

    def create_layout(self):
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=20, pady=(15, 10))

        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        self.create_controls(main)
        
        right = ttk.Frame(main)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(15, 0))

        self.create_visualization(right)
        self.create_tables(right)

    def create_controls(self, parent):
        panel = ttk.LabelFrame(parent, text="Параметры", padding=15)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        self.entries = {}

        material_frame = ttk.Frame(panel)
        material_frame.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(material_frame, text="Материал:", 
                 font=Fonts.LABEL_SMALL).pack(side=tk.LEFT)
        
        self.material_combo = ttk.Combobox(material_frame, 
                                         values=list(self.materials.keys()),
                                         font=Fonts.VALUE, width=12, state="readonly")
        self.material_combo.set(self.current_material)
        self.material_combo.pack(side=tk.RIGHT, padx=(12, 0))
        self.material_combo.bind("<<ComboboxSelected>>", self.on_material_change)

        self.create_block(panel, "Свойства материала", [
            "Плотность", "Теплоёмкость", "Теплопроводность", "Длина"
        ], self.materials[self.current_material].values())

        self.create_block(panel, "Температура", [
            "Начальная", "Слева", "Справа"
        ], ["180", "300", "30"])

        self.create_block(panel, "Расчёт", [
            "Шаг пространства", "Шаг времени", "Время моделирования"
        ], ["0.01", "0.01", "2"])

        btn_frame = ttk.Frame(panel)
        btn_frame.pack(fill=tk.X, pady=20)

        # ✅ Обычные кнопки БЕЗ style!
        ttk.Button(btn_frame, text="Запуск", 
                  command=self.start_animation).pack(fill=tk.X, pady=(0, 8))
        ttk.Button(btn_frame, text="Стоп", 
                  command=self.stop_animation).pack(fill=tk.X, pady=(0, 8))

        self.btn_calc = ttk.Button(btn_frame, text="Заполнить таблицу", 
                                  command=self.start_table_thread)
        self.btn_calc.pack(fill=tk.X)

        status_frame = ttk.Frame(panel)
        status_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Label(status_frame, text="Время:", 
                font=("Segoe UI", 11)).pack(anchor="w")
        self.time_value = tk.Label(status_frame, text="0.00 с", 
                                font=("Segoe UI", 16, "bold"))  # Черный!
        self.time_value.pack(anchor="w", pady=(5, 15))

        ttk.Label(status_frame, text="Температура в центре:", 
                font=("Segoe UI", 11)).pack(anchor="w")
        self.temp_value = tk.Label(status_frame, text="— °C", 
                                font=("Segoe UI", 16, "bold"))
        self.temp_value.pack(anchor="w")

    def on_material_change(self, event=None):
        selected = self.material_combo.get()
        if selected in self.materials:
            self.current_material = selected
            material = self.materials[selected]
            
            self.entries["Плотность"].delete(0, tk.END)
            self.entries["Плотность"].insert(0, str(material["Плотность"]))
            self.entries["Теплоёмкость"].delete(0, tk.END)
            self.entries["Теплоёмкость"].insert(0, str(material["Теплоёмкость"]))
            self.entries["Теплопроводность"].delete(0, tk.END)
            self.entries["Теплопроводность"].insert(0, str(material["Теплопроводность"]))
            self.entries["Длина"].delete(0, tk.END)
            self.entries["Длина"].insert(0, str(material["Длина"]))

    def create_block(self, parent, title, labels, defaults):
        block = ttk.LabelFrame(parent, text=title, padding=12)
        block.pack(fill=tk.X, pady=(0, 12))
        
        for label, default in zip(labels, defaults):
            row = ttk.Frame(block)
            row.pack(fill=tk.X, pady=3)
            
            ttk.Label(row, text=label + ":", width=18, 
                     font=Fonts.LABEL_SMALL).pack(side=tk.LEFT)
            
            entry = ttk.Entry(row, font=Fonts.VALUE, width=12)
            entry.insert(0, str(default))
            entry.pack(side=tk.RIGHT)
            
            self.entries[label] = entry

    def create_visualization(self, parent):
        viz_frame = ttk.LabelFrame(parent, text="Визуализация", padding=15)
        viz_frame.pack(fill=tk.BOTH, pady=(0, 15))

        self.fig = Figure(figsize=(10, 4.5), facecolor=Colors.BG_CARD, dpi=100)
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12, hspace=0.55)
        
        for ax in (self.ax1, self.ax2):
            ax.set_facecolor(Colors.BG_CARD)
            ax.grid(True, color=Colors.GRID_LINE, linewidth=0.5, alpha=0.7)
            ax.tick_params(colors=Colors.TEXT_SECONDARY, labelsize=9)

        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_tables(self, parent):
        tables_frame = ttk.LabelFrame(parent, text="Температура в центре (t=2с)", padding=15)
        tables_frame.pack(fill=tk.BOTH, expand=True)

        self.tabs = ttk.Notebook(tables_frame)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        temp_frame = ttk.Frame(self.tabs)
        self.tabs.add(temp_frame, text="Температура")
        self.temp_table = self.create_styled_table(temp_frame)

    def create_styled_table(self, parent):
        columns = ["Шаг по врем\\по простр", "0.1", "0.01", "0.001", "0.0001"]
        
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=5)
        
        for i, col in enumerate(columns):
            tree.heading(col, text=col, anchor="center")
            width = 85 if i == 0 else 95
            tree.column(col, width=width, anchor="center", minwidth=70)
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        return tree

    def read_params(self):
        p = {label: float(entry.get()) for label, entry in self.entries.items()}
        self.rho = p["Плотность"]
        self.c = p["Теплоёмкость"]
        self.lam = p["Теплопроводность"]
        self.L = p["Длина"]
        self.T0 = p["Начальная"]
        self.Tl = p["Слева"]
        self.Tr = p["Справа"]
        self.h = p["Шаг пространства"]
        self.dt = p["Шаг времени"]
        self.t_end = p["Время моделирования"]

    def start_animation(self):
        if self.running:
            return
        self.running = True
        self.read_params()

        self.Nx = int(round(self.L / self.h))
        if self.Nx < 2:
            self.Nx = 2

        self.x = np.linspace(0, self.L, self.Nx + 1)
        self.T = np.full(self.Nx + 1, self.T0)
        self.T[0], self.T[-1] = self.Tl, self.Tr

        dx = self.L / self.Nx
        self.A = self.lam / dx**2
        self.C = self.A
        self.B = 2 * self.lam / dx**2 + self.rho * self.c / self.dt

        self.alpha = np.zeros(self.Nx + 1)
        self.beta = np.zeros(self.Nx + 1)
        self.current_time = 0

        self.update_animation()

    def update_animation(self):
        if not self.running:
            return

        self.T = calculate_next_step(
            self.T, self.alpha, self.beta,
            self.A, self.B, self.C,
            self.Nx, self.rho, self.c,
            self.dt, self.Tl, self.Tr
        )
        self.current_time += self.dt

        self.ax1.clear()
        self.ax1.set_facecolor(Colors.BG_CARD)
        self.ax1.plot(self.x, self.T, color=Colors.PLOT_LINE, lw=2.5)
        self.ax1.set_xlabel("Длина, м", color=Colors.TEXT_SECONDARY)
        self.ax1.set_ylabel("°C", color=Colors.TEXT_SECONDARY, rotation=0)
        self.ax1.set_title("Профиль температуры", color=Colors.TEXT_PRIMARY, fontweight="bold", pad=10)
        self.ax1.grid(True, color=Colors.GRID_LINE, alpha=0.7, linewidth=0.5)
        self.ax1.tick_params(colors=Colors.TEXT_SECONDARY)

        self.ax2.clear()
        self.ax2.set_facecolor(Colors.BG_CARD)
        self.ax2.imshow([self.T], aspect='auto', cmap='coolwarm',
                       extent=[0, self.L, 0, 0.1], interpolation='bilinear')
        self.ax2.set_yticks([])
        self.ax2.set_xlabel("Длина, м", color=Colors.TEXT_SECONDARY)
        self.ax2.set_title("Визуализация тепла", color=Colors.TEXT_PRIMARY, fontweight="bold", pad=10)
        self.ax2.tick_params(colors=Colors.TEXT_SECONDARY)

        self.canvas.draw_idle()

        center = self.T[self.Nx // 2]
        self.time_value.config(text=f"{self.current_time:.2f} с")
        self.temp_value.config(text=f"{center:.2f} °C")

        self.animation_job = self.root.after(40, self.update_animation)

    def stop_animation(self):
        self.running = False
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None

    def start_table_thread(self):
        if self.running:
            return
        self.btn_calc.config(state="disabled")
        threading.Thread(target=self.calculate_table, daemon=True).start()

    def calculate_table(self):
        self.root.after(0, lambda: self.temp_table.delete(*self.temp_table.get_children()))
        
        self.read_params()
        dts = [0.1, 0.01, 0.001, 0.0001]
        hs = [0.1, 0.01, 0.001, 0.0001]

        for dt_val in dts:
            temp_row = [f"{dt_val:g}"]
            for h_val in hs:
                try:
                    _, center = simulate(self.rho, self.c, self.lam, self.Tl, self.Tr, self.T0,
                                       self.L, h_val, 2.0, dt_val)
                    temp_row.append(f"{center:.2f}")
                except:
                    temp_row.append("—")
            self.root.after(0, lambda row=temp_row: self.temp_table.insert("", tk.END, values=row))
        
        self.root.after(0, lambda: self.btn_calc.config(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    app = HeatApp(root)
    root.mainloop()
