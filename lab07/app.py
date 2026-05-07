import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch
import matplotlib.patheffects as pe
import random
import math


# ─────────────────────────────────────────────
#  ЦВЕТОВАЯ ПАЛИТРА
# ─────────────────────────────────────────────
PALETTE = {
    'bg':          '#0D1117',
    'panel':       '#161B22',
    'panel2':      '#1C2128',
    'border':      '#30363D',
    'accent':      '#58A6FF',
    'accent2':     '#3FB950',
    'accent3':     '#FF7B72',
    'text':        '#E6EDF3',
    'text_dim':    '#8B949E',
    'sunny':       '#FFD60A',
    'cloudy':      '#79C0FF',
    'overcast':    '#8B949E',
    'sunny_bg':    '#2D2A00',
    'cloudy_bg':   '#001D3D',
    'overcast_bg': '#1A1A1A',
}

STATE_COLORS  = {1: PALETTE['sunny'],   2: PALETTE['cloudy'],   3: PALETTE['overcast']}
STATE_BG      = {1: PALETTE['sunny_bg'],2: PALETTE['cloudy_bg'],3: PALETTE['overcast_bg']}
STATE_NAMES   = {1: 'Ясно ☀', 2: 'Облачно ⛅', 3: 'Пасмурно 🌧'}
STATE_ICONS   = {1: '☀️', 2: '⛅', 3: '🌧️'}
STATE_LABELS  = {1: 'Ясно', 2: 'Облачно', 3: 'Пасмурно'}


# ─────────────────────────────────────────────
#  ДВИЖОК: НЕПРЕРЫВНАЯ ЦЕПЬ МАРКОВА
# ─────────────────────────────────────────────
class WeatherMarkovEngine:
    def __init__(self):
        # Матрица интенсивностей (только внедиагональные)
        self._rates = np.array([
            [0.0,  0.3,  0.2],
            [0.4,  0.0,  0.3],
            [0.1,  0.4,  0.0],
        ], dtype=float)
        self._build_Q()

        self.states      = STATE_LABELS
        self.current_state = 1
        self.history     = []          # list of (state, duration_days)
        self.current_day = 0.0
        self.day_history = []          # list of (day_int, state) for discrete display

    # ── Построение Q из внедиагональных элементов ──
    def _build_Q(self):
        Q = self._rates.copy()
        np.fill_diagonal(Q, -Q.sum(axis=1))
        self.Q = Q

    def get_rates(self):
        return self._rates.copy()

    def set_rates(self, rates_3x3):
        r = np.array(rates_3x3, dtype=float)
        np.fill_diagonal(r, 0)
        if np.any(r < 0):
            raise ValueError("Интенсивности должны быть неотрицательными")
        self._rates = r
        self._build_Q()

    def get_Q(self):
        return self.Q.copy()

    def reset(self, initial_state=1):
        self.current_state = initial_state
        self.history       = []
        self.current_day   = 0.0
        self.day_history   = []

    # ── Выбор следующего состояния методом обратного преобразования ──
    @staticmethod
    def _choose_next_state(candidates):
        """
        candidates: список пар (state, probability), сумма вероятностей = 1
        Метод обратного преобразования: идём по кумулятивной сумме,
        возвращаем первое состояние где накопленная сумма >= rand_val.
        """
        rand_val = random.random()  # U ~ Uniform[0, 1]
        cumulative = 0.0
        for state, prob in candidates:
            cumulative += prob
            if cumulative >= rand_val:
                return state
        # На случай ошибок округления — возвращаем последний
        return candidates[-1][0]

    # ── Один переход (непрерывное время) ──
    def step(self):
        s = self.current_state - 1
        lambda_total = abs(self.Q[s, s])
        if lambda_total < 1e-12:
            return self.current_state, 1.0

        duration = random.expovariate(lambda_total)

        # Заполняем дискретные дни
        start_day = int(self.current_day)
        end_day   = int(self.current_day + duration)
        for d in range(start_day, end_day + 1):
            self.day_history.append((d, self.current_state))

        self.history.append((self.current_state, duration))
        self.current_day += duration

        # Формируем список (состояние, вероятность) для всех состояний кроме текущего
        r2 = self._rates[s].copy()
        r2[s] = 0
        total = r2.sum()
        candidates = [
            (state_idx + 1, r2[state_idx] / total)
            for state_idx in range(3)
            if state_idx != s
        ]

        next_s = self._choose_next_state(candidates)
        self.current_state = next_s
        return next_s, duration

    # ── Стационарное распределение ──
    def get_stationary(self):
        eigenvalues, eigenvectors = np.linalg.eig(self.Q.T)
        idx = np.argmin(np.abs(eigenvalues))
        pi  = np.real(eigenvectors[:, idx])
        pi  = pi / pi.sum()
        return pi

    # ── Эмпирическое (по времени) ──
    def get_empirical(self):
        if not self.history:
            return np.array([1/3, 1/3, 1/3])
        total = sum(d for _, d in self.history)
        times = [0.0, 0.0, 0.0]
        for s, d in self.history:
            times[s-1] += d
        return np.array(times) / total

    # ── Кумулятивное ──
    def get_cumulative(self):
        if len(self.history) < 2:
            return np.empty((0, 3))
        cum  = []
        runs = [0.0, 0.0, 0.0]
        tot  = 0.0
        for s, d in self.history:
            runs[s-1] += d
            tot        += d
            cum.append([runs[0]/tot, runs[1]/tot, runs[2]/tot])
        return np.array(cum)

    def get_statistics(self):
        if not self.history:
            return None
        total = sum(d for _, d in self.history)
        emp   = self.get_empirical()
        stat  = self.get_stationary()
        return {
            'total_time':   total,
            'total_events': len(self.history),
            'empirical':    emp,
            'stationary':   stat,
            'current_day':  int(self.current_day),
        }


# ─────────────────────────────────────────────
#  ГЛАВНЫЙ GUI
# ─────────────────────────────────────────────
class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌤 Марковская Модель Погоды")
        self.root.geometry("1540x920")
        self.root.configure(bg=PALETTE['bg'])
        self.root.resizable(True, True)

        self.engine        = WeatherMarkovEngine()
        self.is_running    = False
        self.sim_speed     = 300       # мс между шагами
        self.target_days   = tk.IntVar(value=100)
        self._after_id     = None

        self._style()
        self._build_ui()
        self._refresh_all()
        self._loop()

    # ── ttk стиль ──
    def _style(self):
        style = ttk.Style()
        style.theme_use('clam')
        bg, panel, text, border = PALETTE['bg'], PALETTE['panel'], PALETTE['text'], PALETTE['border']
        acc = PALETTE['accent']

        style.configure('.',             background=bg,    foreground=text,  font=('Segoe UI', 10))
        style.configure('TFrame',        background=bg)
        style.configure('Panel.TFrame',  background=panel)
        style.configure('TLabel',        background=bg,    foreground=text)
        style.configure('Panel.TLabel',  background=panel, foreground=text)
        style.configure('Dim.TLabel',    background=panel, foreground=PALETTE['text_dim'])
        style.configure('TEntry',        fieldbackground=PALETTE['panel2'], foreground=text,
                        insertcolor=text, bordercolor=border, relief='flat')
        style.configure('TButton',       background=PALETTE['panel2'], foreground=text,
                        bordercolor=border, relief='flat', padding=(8,5))
        style.map('TButton',             background=[('active', PALETTE['border'])])
        style.configure('Accent.TButton',background=acc,   foreground='#000',
                        font=('Segoe UI', 10, 'bold'), relief='flat', padding=(10,6))
        style.map('Accent.TButton',      background=[('active', '#79C0FF')])
        style.configure('Green.TButton', background=PALETTE['accent2'], foreground='#000',
                        font=('Segoe UI', 10, 'bold'), relief='flat', padding=(10,6))
        style.map('Green.TButton',       background=[('active', '#56D364')])
        style.configure('Red.TButton',   background=PALETTE['accent3'], foreground='#fff',
                        font=('Segoe UI', 10, 'bold'), relief='flat', padding=(10,6))
        style.map('Red.TButton',         background=[('active', '#FF9E8C')])
        style.configure('TScale',        background=panel, troughcolor=PALETTE['panel2'],
                        sliderlength=16, sliderrelief='flat')
        style.configure('TSpinbox',      fieldbackground=PALETTE['panel2'], foreground=text,
                        bordercolor=border)

    # ═══════════════════════════════════════════
    #  ПОСТРОЕНИЕ UI
    # ═══════════════════════════════════════════
    def _build_ui(self):
        # ── Шапка ──
        header = tk.Frame(self.root, bg=PALETTE['panel'], height=58)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)

        tk.Label(header, text="МАРКОВСКАЯ МОДЕЛЬ ПОГОДЫ",
                 bg=PALETTE['panel'], fg=PALETTE['accent'],
                 font=('Consolas', 18, 'bold')).pack(side='left', padx=20, pady=14)
        tk.Label(header, text="непрерывная цепь Маркова · дискретное отображение дней",
                 bg=PALETTE['panel'], fg=PALETTE['text_dim'],
                 font=('Segoe UI', 10)).pack(side='left', padx=5, pady=14)

        # ── Тело: левая панель + правые графики ──
        body = tk.Frame(self.root, bg=PALETTE['bg'])
        body.pack(fill='both', expand=True)

        left = tk.Frame(body, bg=PALETTE['panel'], width=340)
        left.pack(side='left', fill='y', padx=(8,4), pady=8)
        left.pack_propagate(False)

        right = tk.Frame(body, bg=PALETTE['bg'])
        right.pack(side='left', fill='both', expand=True, padx=(4,8), pady=8)

        self._build_left(left)
        self._build_right(right)

    # ─────────────────────────────────────────
    #  ЛЕВАЯ ПАНЕЛЬ
    # ─────────────────────────────────────────
    def _build_left(self, parent):
        pad = dict(padx=14, pady=5)

        # ── Текущее состояние ──
        self.state_frame = tk.Frame(parent, bg=PALETTE['sunny_bg'], height=80)
        self.state_frame.pack(fill='x', padx=10, pady=(14,6))
        self.state_frame.pack_propagate(False)

        self.state_icon  = tk.Label(self.state_frame, text='☀️',  bg=PALETTE['sunny_bg'],
                                    font=('Segoe UI Emoji', 26))
        self.state_icon.place(x=14, y=10)

        self.state_lbl   = tk.Label(self.state_frame, text='Ясно',
                                    bg=PALETTE['sunny_bg'], fg=PALETTE['sunny'],
                                    font=('Segoe UI', 18, 'bold'))
        self.state_lbl.place(x=70, y=8)

        self.day_lbl     = tk.Label(self.state_frame, text='День 0',
                                    bg=PALETTE['sunny_bg'], fg=PALETTE['text_dim'],
                                    font=('Segoe UI', 10))
        self.day_lbl.place(x=70, y=42)

        # ── Матрица интенсивностей ──
        self._section(parent, "МАТРИЦА ИНТЕНСИВНОСТЕЙ (λᵢⱼ)")

        info = tk.Label(parent, text="Введите интенсивности переходов.\nДиагональ вычисляется автоматически.",
                        bg=PALETTE['panel'], fg=PALETTE['text_dim'],
                        font=('Segoe UI', 8), justify='left')
        info.pack(anchor='w', **pad)

        matrix_wrap = tk.Frame(parent, bg=PALETTE['panel'])
        matrix_wrap.pack(**pad)

        headers = ['→', 'Ясно', 'Облачно', 'Пасмурно']
        for j, h in enumerate(headers):
            color = [PALETTE['text_dim'], PALETTE['sunny'], PALETTE['cloudy'], PALETTE['overcast']][j]
            tk.Label(matrix_wrap, text=h, bg=PALETTE['panel'], fg=color,
                     font=('Segoe UI', 9, 'bold'), width=9, anchor='center').grid(row=0, column=j, padx=2, pady=2)

        rows = ['Ясно', 'Облачно', 'Пасмурно']
        row_colors = [PALETTE['sunny'], PALETTE['cloudy'], PALETTE['overcast']]
        self.rate_entries = {}

        for i in range(3):
            tk.Label(matrix_wrap, text=rows[i], bg=PALETTE['panel'], fg=row_colors[i],
                     font=('Segoe UI', 9, 'bold'), width=9, anchor='e').grid(row=i+1, column=0, padx=2, pady=2)
            for j in range(3):
                if i == j:
                    # Диагональ — вычисляется автоматически
                    lbl = tk.Label(matrix_wrap, text='auto', width=7,
                                   bg=PALETTE['panel2'], fg=PALETTE['text_dim'],
                                   font=('Consolas', 9, 'italic'),
                                   relief='flat', anchor='center')
                    lbl.grid(row=i+1, column=j+1, padx=2, pady=2, ipady=4)
                    self.rate_entries[(i,j)] = lbl
                else:
                    var = tk.StringVar(value=f"{self.engine.get_rates()[i,j]:.2f}")
                    ent = tk.Entry(matrix_wrap, textvariable=var, width=7,
                                  bg=PALETTE['panel2'], fg=PALETTE['text'],
                                  font=('Consolas', 9), relief='flat',
                                  insertbackground=PALETTE['text'],
                                  justify='center', bd=0, highlightthickness=1,
                                  highlightbackground=PALETTE['border'],
                                  highlightcolor=PALETTE['accent'])
                    ent.grid(row=i+1, column=j+1, padx=2, pady=2, ipady=4)
                    self.rate_entries[(i,j)] = ent

        ttk.Button(parent, text="✓ Применить матрицу", style='Accent.TButton',
                   command=self._apply_matrix).pack(fill='x', padx=14, pady=6)

        # ── Управление симуляцией ──
        self._section(parent, "СИМУЛЯЦИЯ")

        # Целевое число дней
        days_row = tk.Frame(parent, bg=PALETTE['panel'])
        days_row.pack(fill='x', padx=14, pady=(0,4))
        tk.Label(days_row, text="Смоделировать дней:", bg=PALETTE['panel'],
                 fg=PALETTE['text_dim'], font=('Segoe UI', 9)).pack(side='left')
        ttk.Spinbox(days_row, from_=10, to=10000, textvariable=self.target_days,
                    width=7, font=('Consolas', 9)).pack(side='right')

        # Кнопки
        btn_row1 = tk.Frame(parent, bg=PALETTE['panel'])
        btn_row1.pack(fill='x', padx=14, pady=2)
        self.btn_start = ttk.Button(btn_row1, text="▶  Старт", style='Green.TButton',
                                    command=self._start)
        self.btn_start.pack(side='left', expand=True, fill='x', padx=(0,3))
        self.btn_stop  = ttk.Button(btn_row1, text="⏸  Стоп", style='Red.TButton',
                                    command=self._stop, state='disabled')
        self.btn_stop.pack(side='left', expand=True, fill='x', padx=(3,0))

        btn_row2 = tk.Frame(parent, bg=PALETTE['panel'])
        btn_row2.pack(fill='x', padx=14, pady=2)
        ttk.Button(btn_row2, text="⏭  Шаг", command=self._step).pack(
            side='left', expand=True, fill='x', padx=(0,3))
        ttk.Button(btn_row2, text="🔄  Сброс", command=self._reset).pack(
            side='left', expand=True, fill='x', padx=(3,0))

        # Скорость
        spd_row = tk.Frame(parent, bg=PALETTE['panel'])
        spd_row.pack(fill='x', padx=14, pady=(6,0))
        tk.Label(spd_row, text="Скорость:", bg=PALETTE['panel'],
                 fg=PALETTE['text_dim'], font=('Segoe UI', 9)).pack(side='left')
        self.spd_lbl = tk.Label(spd_row, text="300 мс", bg=PALETTE['panel'],
                                fg=PALETTE['accent'], font=('Consolas', 9))
        self.spd_lbl.pack(side='right')

        self.spd_var = tk.IntVar(value=300)
        spd_scale = ttk.Scale(parent, from_=20, to=1500, variable=self.spd_var,
                              orient='horizontal', command=self._spd_changed)
        spd_scale.pack(fill='x', padx=14, pady=(2,8))

        # ── Экспорт ──
        self._section(parent, "ЭКСПОРТ")
        ttk.Button(parent, text="💾  Сохранить в CSV", style='Accent.TButton',
                   command=self._export).pack(fill='x', padx=14, pady=6)

        # ── Статистика ──
        self._section(parent, "СТАТИСТИКА")
        self.stats_box = tk.Text(parent, height=9, bg=PALETTE['panel2'],
                                 fg=PALETTE['text'], font=('Consolas', 8),
                                 relief='flat', bd=0,
                                 highlightthickness=1,
                                 highlightbackground=PALETTE['border'])
        self.stats_box.pack(fill='x', padx=14, pady=(0,14))
        self.stats_box.config(state='disabled')

    def _section(self, parent, title):
        f = tk.Frame(parent, bg=PALETTE['panel'])
        f.pack(fill='x', padx=14, pady=(10,2))
        tk.Label(f, text=title, bg=PALETTE['panel'], fg=PALETTE['accent'],
                 font=('Consolas', 8, 'bold')).pack(side='left')
        tk.Frame(f, bg=PALETTE['border'], height=1).pack(side='left', fill='x', expand=True, padx=6)

    # ─────────────────────────────────────────
    #  ПРАВАЯ ПАНЕЛЬ: ГРАФИКИ
    # ─────────────────────────────────────────
    def _build_right(self, parent):
        plt.style.use('dark_background')
        self.fig = Figure(figsize=(11, 8), dpi=100, facecolor=PALETTE['bg'])
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self._setup_axes()

    def _setup_axes(self):
        self.fig.clear()
        gs = self.fig.add_gridspec(3, 2, hspace=0.48, wspace=0.32,
                                   left=0.07, right=0.97, top=0.95, bottom=0.07)
        self.ax_timeline  = self.fig.add_subplot(gs[0, :])   # Временной ряд — во всю ширину
        self.ax_compare   = self.fig.add_subplot(gs[1, 0])   # Сравнение
        self.ax_heatmap   = self.fig.add_subplot(gs[1, 1])   # Матрица Q
        self.ax_converge  = self.fig.add_subplot(gs[2, :])   # Сходимость — во всю ширину

        for ax in [self.ax_timeline, self.ax_compare, self.ax_heatmap, self.ax_converge]:
            ax.set_facecolor(PALETTE['panel'])
            for spine in ax.spines.values():
                spine.set_edgecolor(PALETTE['border'])

    # ─────────────────────────────────────────
    #  ОБНОВЛЕНИЕ ГРАФИКОВ
    # ─────────────────────────────────────────
    def _update_plots(self):
        self._setup_axes()
        history = self.engine.history

        # ── 1. ВРЕМЕННОЙ РЯД (ступенчатый, дискретные дни) ──
        ax = self.ax_timeline
        if history:
            # Берём последние 60 переходов
            disp = history[-60:] if len(history) > 60 else history
            states    = [h[0] for h in disp]
            durations = [h[1] for h in disp]

            t = [0.0]
            for d in durations:
                t.append(t[-1] + d)

            # Раскраска фона
            for i in range(len(t)-1):
                ax.axvspan(t[i], t[i+1], color=STATE_COLORS[states[i]], alpha=0.15, linewidth=0)

            # Ступенчатая линия
            ax.step(t[:-1], states, where='post',
                    color='white', linewidth=1.5, zorder=3)

            # Маркеры состояний
            for i, s in enumerate(states):
                ax.plot(t[i], s, 'o', color=STATE_COLORS[s], markersize=5, zorder=4)

            ax.set_yticks([1, 2, 3])
            ax.set_yticklabels([STATE_LABELS[1], STATE_LABELS[2], STATE_LABELS[3]],
                               color=PALETTE['text'], fontsize=9)
            ax.yaxis.label.set_color(PALETTE['text_dim'])
            ax.set_xlabel('Время (дни)', color=PALETTE['text_dim'], fontsize=9)
            ax.set_title(f'Поток состояний — последние {len(disp)} событий',
                         color=PALETTE['text'], fontsize=10, fontweight='bold', pad=8)
            ax.tick_params(colors=PALETTE['text_dim'], labelsize=8)
            ax.set_ylim(0.4, 3.6)
            ax.grid(axis='y', color=PALETTE['border'], alpha=0.5, linewidth=0.5)
        else:
            ax.set_title('Поток состояний', color=PALETTE['text'], fontsize=10, pad=8)
            ax.text(0.5, 0.5, 'Запустите симуляцию', ha='center', va='center',
                    color=PALETTE['text_dim'], fontsize=12, transform=ax.transAxes)

        # ── 2. СРАВНЕНИЕ ЭМПИРИКИ И ТЕОРИИ ──
        ax = self.ax_compare
        emp  = self.engine.get_empirical()
        stat = self.engine.get_stationary()

        x      = np.arange(3)
        w      = 0.35
        colors = [PALETTE['sunny'], PALETTE['cloudy'], PALETTE['overcast']]

        bars_e = ax.bar(x - w/2, emp,  w, color=colors, alpha=0.9, edgecolor='white', linewidth=0.5, label='Эмпирич.')
        bars_t = ax.bar(x + w/2, stat, w, color=colors, alpha=0.45, edgecolor='white', linewidth=0.5,
                        linestyle='--', label='Теоретич.', hatch='//')

        for bar, v in zip(bars_e, emp):
            ax.text(bar.get_x() + bar.get_width()/2, v + 0.015, f'{v:.2f}',
                    ha='center', va='bottom', color='white', fontsize=7)
        for bar, v in zip(bars_t, stat):
            ax.text(bar.get_x() + bar.get_width()/2, v + 0.015, f'{v:.2f}',
                    ha='center', va='bottom', color='white', fontsize=7)

        ax.set_xticks(x)
        ax.set_xticklabels([STATE_LABELS[1], STATE_LABELS[2], STATE_LABELS[3]],
                           color=PALETTE['text'], fontsize=9)
        ax.set_ylim(0, 1.0)
        ax.set_title('Эмпирика vs Теория', color=PALETTE['text'], fontsize=10, fontweight='bold', pad=8)
        ax.set_ylabel('Доля времени', color=PALETTE['text_dim'], fontsize=9)
        ax.tick_params(colors=PALETTE['text_dim'], labelsize=8)
        ax.legend(fontsize=7, framealpha=0.15, labelcolor='white')
        ax.grid(axis='y', color=PALETTE['border'], alpha=0.4, linewidth=0.5)

        # ── 3. ТЕПЛОВАЯ КАРТА МАТРИЦЫ Q ──
        ax = self.ax_heatmap
        Q = self.engine.get_Q()
        im = ax.imshow(Q, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=0.5)
        labels = [STATE_LABELS[1], STATE_LABELS[2], STATE_LABELS[3]]
        ax.set_xticks([0, 1, 2]); ax.set_xticklabels(labels, color=PALETTE['text'], fontsize=8)
        ax.set_yticks([0, 1, 2]); ax.set_yticklabels(labels, color=PALETTE['text'], fontsize=8)
        ax.set_title('Матрица Q (интенсивности)', color=PALETTE['text'], fontsize=10, fontweight='bold', pad=8)

        for i in range(3):
            for j in range(3):
                v = Q[i, j]
                txt_color = 'black' if abs(v) < 0.3 else 'white'
                style = 'italic' if i == j else 'normal'
                ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                        color=txt_color, fontsize=9, fontweight='bold', style=style)

        # ── 4. СХОДИМОСТЬ К СТАЦИОНАРНОМУ ──
        ax = self.ax_converge
        cum = self.engine.get_cumulative()

        if len(cum) > 1:
            xs = np.arange(1, len(cum)+1)
            c  = [PALETTE['sunny'], PALETTE['cloudy'], PALETTE['overcast']]
            for i in range(3):
                ax.plot(xs, cum[:, i], color=c[i], linewidth=1.5,
                        label=STATE_LABELS[i+1], alpha=0.9)
                ax.axhline(y=stat[i], color=c[i], linestyle='--', alpha=0.4, linewidth=1)
                # Подпись теор. линии
                ax.text(len(cum)*1.002, stat[i], f'{stat[i]:.2f}',
                        color=c[i], fontsize=7, va='center')

            ax.set_ylim(0, 1)
            ax.set_xlabel('Количество переходов', color=PALETTE['text_dim'], fontsize=9)
            ax.set_ylabel('Накопл. доля времени', color=PALETTE['text_dim'], fontsize=9)
            ax.set_title('Сходимость к стационарному распределению',
                         color=PALETTE['text'], fontsize=10, fontweight='bold', pad=8)
            ax.legend(fontsize=8, framealpha=0.1, labelcolor='white', loc='upper right')
            ax.grid(color=PALETTE['border'], alpha=0.3, linewidth=0.5)
            ax.tick_params(colors=PALETTE['text_dim'], labelsize=8)
        else:
            ax.set_title('Сходимость к стационарному распределению',
                         color=PALETTE['text'], fontsize=10, pad=8)
            ax.text(0.5, 0.5, 'Недостаточно данных', ha='center', va='center',
                    color=PALETTE['text_dim'], fontsize=11, transform=ax.transAxes)

        self.canvas.draw_idle()

    # ─────────────────────────────────────────
    #  ОБНОВЛЕНИЕ ЛЕВОЙ ПАНЕЛИ
    # ─────────────────────────────────────────
    def _update_state_widget(self):
        s    = self.engine.current_state
        col  = STATE_COLORS[s]
        bg   = STATE_BG[s]
        icon = STATE_ICONS[s]
        name = STATE_LABELS[s]

        self.state_frame.config(bg=bg)
        self.state_icon.config(text=icon, bg=bg)
        self.state_lbl.config(text=name, fg=col, bg=bg)
        day = int(self.engine.current_day)
        self.day_lbl.config(text=f"День {day}", bg=bg)

    def _update_diag(self):
        """Обновить автодиагональ в матрице."""
        try:
            r = np.zeros((3,3))
            for i in range(3):
                for j in range(3):
                    if i != j:
                        r[i,j] = float(self.rate_entries[(i,j)].get())
            for i in range(3):
                diag = -r[i].sum()
                self.rate_entries[(i,i)].config(text=f'{diag:.2f}')
        except Exception:
            pass

    def _update_stats(self):
        st = self.engine.get_statistics()
        self.stats_box.config(state='normal')
        self.stats_box.delete('1.0', 'end')
        if st:
            lines = [
                f"Переходов:  {st['total_events']}",
                f"Прошло дней:{st['current_day']}",
                f"Общ. время: {st['total_time']:.2f} дн.",
                "",
                "Доля времени (эмпир. / теор.):",
            ]
            for i in range(3):
                e = st['empirical'][i]
                t = st['stationary'][i]
                lines.append(f"  {STATE_LABELS[i+1]:8s}: {e:.3f} / {t:.3f}")

            # Погрешность
            err = np.mean(np.abs(st['empirical'] - st['stationary']))
            lines.append(f"\nСредн. погреш.: {err:.4f}")
        else:
            lines = ['Нет данных.\nЗапустите симуляцию.']
        self.stats_box.insert('end', '\n'.join(lines))
        self.stats_box.config(state='disabled')

    def _refresh_all(self):
        self._update_state_widget()
        self._update_diag()
        self._update_stats()
        self._update_plots()

    # ─────────────────────────────────────────
    #  УПРАВЛЕНИЕ
    # ─────────────────────────────────────────
    def _apply_matrix(self):
        try:
            r = np.zeros((3,3))
            for i in range(3):
                for j in range(3):
                    if i != j:
                        r[i,j] = float(self.rate_entries[(i,j)].get())
            self.engine.set_rates(r)
            self._update_diag()
            self._update_plots()
            messagebox.showinfo("Матрица применена",
                                "Интенсивности обновлены.\nДиагональ вычислена автоматически.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _start(self):
        if not self.is_running:
            self.is_running = True
            self.btn_start.config(state='disabled')
            self.btn_stop.config(state='normal')

    def _stop(self):
        self.is_running = False
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')

    def _reset(self):
        self._stop()
        self.engine.reset(initial_state=1)
        self._refresh_all()

    def _step(self):
        self.engine.step()
        self._refresh_all()

    def _spd_changed(self, val):
        self.sim_speed = int(float(val))
        self.spd_lbl.config(text=f"{self.sim_speed} мс")

    # ─────────────────────────────────────────
    #  ГЛАВНЫЙ ЦИКЛ
    # ─────────────────────────────────────────
    def _loop(self):
        if self.is_running:
            # Проверяем, не достигли ли целевого числа дней
            if int(self.engine.current_day) >= self.target_days.get():
                self._stop()
                messagebox.showinfo("Симуляция завершена",
                                    f"Достигнуто {self.target_days.get()} дней!")
            else:
                _, dur = self.engine.step()
                self._update_state_widget()
                # Обновляем графики не каждый шаг (дорого), а примерно каждые 5
                if len(self.engine.history) % 5 == 0:
                    self._update_plots()
                self._update_stats()
                delay = max(20, self.sim_speed)
                self._after_id = self.root.after(delay, self._loop)
                return
        self._after_id = self.root.after(80, self._loop)

    # ─────────────────────────────────────────
    #  ЭКСПОРТ CSV
    # ─────────────────────────────────────────
    def _export(self):
        if not self.engine.history:
            messagebox.showwarning("Нет данных", "Сначала запустите симуляцию.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            initialfile="weather_markov.csv",
            title="Сохранить историю"
        )
        if not filename:
            return

        try:
            df = pd.DataFrame(self.engine.history, columns=['Состояние_код', 'Длительность_дни'])
            df['Состояние'] = df['Состояние_код'].map(STATE_LABELS)

            # Добавим условные даты (от сегодня)
            start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cum   = 0.0
            dates = []
            for dur in df['Длительность_дни']:
                dates.append((start + timedelta(days=cum)).strftime('%Y-%m-%d'))
                cum += dur
            df.insert(0, 'Дата', dates)

            df.to_csv(filename, index=False, encoding='utf-8-sig')

            # Статистика
            st   = self.engine.get_statistics()
            sfile = filename.replace('.csv', '_статистика.csv')
            stat_df = pd.DataFrame({
                'Состояние':            [STATE_LABELS[i] for i in range(1,4)],
                'Эмпирич_доля':         st['empirical'],
                'Теорет_доля':          st['stationary'],
                'Погрешность':          np.abs(st['empirical'] - st['stationary'])
            })
            stat_df.to_csv(sfile, index=False, encoding='utf-8-sig')

            messagebox.showinfo("Сохранено",
                                f"История: {filename}\nСтатистика: {sfile}")
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", str(e))


# ─────────────────────────────────────────────
#  ТОЧКА ВХОДА
# ─────────────────────────────────────────────
def main():
    root = tk.Tk()
    app  = WeatherApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()