import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
from scipy import stats

class PoissonFlowModel:
    def __init__(self, lambda_rate, T, num_experiments=1000):
        self.lambda_rate = lambda_rate
        self.T = T
        self.num_experiments = num_experiments
        self.event_counts = []
        self.event_times = []

    def generate_flow(self):
        t_current = 0
        times = []  # Список моментов появления событий
        while t_current < self.T:
            tau = np.random.exponential(scale=1 / self.lambda_rate)
            t_current += tau
            if t_current <= self.T:
                times.append(t_current)
        return times

    def run_experiments(self):
        self.event_counts = []
        for _ in range(self.num_experiments):
            times = self.generate_flow()
            count = len(times)
            self.event_counts.append(count)
        self.event_times = self.generate_flow()
        return self.event_counts

    def get_statistics(self):
        if not self.event_counts:
            self.run_experiments()
        mean = np.mean(self.event_counts)
        variance = np.var(self.event_counts, ddof=1)
        std = np.std(self.event_counts, ddof=1)
        theoretical_mean = self.lambda_rate * self.T
        theoretical_variance = self.lambda_rate * self.T
        return {
            'mean': mean,
            'variance': variance,
            'std': std,
            'theoretical_mean': theoretical_mean,
            'theoretical_variance': theoretical_variance,
            'min': min(self.event_counts),
            'max': max(self.event_counts),
        }

    def get_distribution(self):
        if not self.event_counts:
            self.run_experiments()
        unique, counts = np.unique(self.event_counts, return_counts=True)
        frequencies = counts / len(self.event_counts)
        return unique, frequencies

CLR = {
    "bg":          "#F5F6FA",
    "surface":     "#FFFFFF",
    "accent":      "#4F5BD5",
    "accent_light":"#EEF0FF",
    "text_h":      "#1A1D2E",
    "text":        "#3D4155",
    "muted":       "#8B90A7",
    "border":      "#E2E4EF",
    "success":     "#2EAC6D",
    "warn":        "#E08C28",
    "danger":      "#D94040",
    "success_bg":  "#EAF8F2",
    "warn_bg":     "#FEF5E7",
    "danger_bg":   "#FDECEC",
}

FONT_BODY  = ("Segoe UI", 10)
FONT_LABEL = ("Segoe UI", 9)
FONT_H1    = ("Segoe UI Semibold", 13)
FONT_H2    = ("Segoe UI Semibold", 10)
FONT_MONO  = ("Consolas", 10)


def _styled_entry(parent, default="", width=14):
    """Поле ввода с лёгкой стилизацией."""
    var = tk.StringVar(value=default)
    e = tk.Entry(
        parent, textvariable=var, width=width,
        font=FONT_BODY,
        bg=CLR["surface"], fg=CLR["text_h"],
        relief="flat", bd=0,
        highlightthickness=1,
        highlightbackground=CLR["border"],
        highlightcolor=CLR["accent"],
        insertbackground=CLR["accent"],
    )
    return e, var


def _label(parent, text, font=FONT_LABEL, fg=None, **kw):
    return tk.Label(
        parent, text=text, font=font,
        fg=fg or CLR["muted"], bg=CLR["bg"], **kw
    )


def _sep(parent):
    return tk.Frame(parent, height=1, bg=CLR["border"])


class MetricCard(tk.Frame):
    """Карточка с одним показателем: подпись / значение / (суб-текст)."""

    def __init__(self, parent, title, bg_surface=CLR["surface"]):
        super().__init__(parent, bg=bg_surface, padx=14, pady=10)
        self.configure(
            highlightthickness=1,
            highlightbackground=CLR["border"],
        )
        tk.Label(self, text=title, font=FONT_LABEL,
                 fg=CLR["muted"], bg=bg_surface).pack(anchor="w")
        self._val_var = tk.StringVar(value="—")
        self._sub_var = tk.StringVar(value="")
        self._val_lbl = tk.Label(
            self, textvariable=self._val_var,
            font=("Segoe UI Semibold", 15),
            fg=CLR["text_h"], bg=bg_surface,
        )
        self._val_lbl.pack(anchor="w")
        self._sub_lbl = tk.Label(
            self, textvariable=self._sub_var,
            font=FONT_LABEL, fg=CLR["muted"], bg=bg_surface,
        )
        self._sub_lbl.pack(anchor="w")

    def set(self, value: str, sub: str = "", color: str | None = None):
        self._val_var.set(value)
        self._sub_var.set(sub)
        if color:
            self._val_lbl.configure(fg=color)
        else:
            self._val_lbl.configure(fg=CLR["text_h"])


class DeviationRow(tk.Frame):
    """Строка сравнения эмпирического и теоретического значений."""

    def __init__(self, parent, label):
        super().__init__(parent, bg=CLR["surface"])
        self._label = label
        tk.Label(self, text=label, font=FONT_LABEL,
                 fg=CLR["text"], bg=CLR["surface"], width=22, anchor="w").pack(side="left")
        self._emp = tk.Label(self, font=FONT_MONO, fg=CLR["text_h"],
                              bg=CLR["surface"], width=9, anchor="e")
        self._emp.pack(side="left", padx=(0, 8))
        self._theor = tk.Label(self, font=FONT_MONO, fg=CLR["muted"],
                                bg=CLR["surface"], width=9, anchor="e")
        self._theor.pack(side="left", padx=(0, 8))
        self._diff = tk.Label(self, font=FONT_MONO,
                               bg=CLR["surface"], width=8, anchor="e")
        self._diff.pack(side="left")

    def set(self, emp, theor):
        rel_err = abs(emp - theor) / theor * 100 if theor else 0
        color = CLR["success"] if rel_err < 5 else (CLR["warn"] if rel_err < 10 else CLR["danger"])
        self._emp.configure(text=f"{emp:.4f}")
        self._theor.configure(text=f"{theor:.4f}")
        self._diff.configure(text=f"{rel_err:.2f}%", fg=color)


class PoissonFlowGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Пуассоновский поток — Лабораторная №8")
        self.root.configure(bg=CLR["bg"])
        self.root.geometry("1260x820")
        self.root.minsize(1050, 700)
        self.model = None
        self._build()

    def _build(self):
        #  Шапка 
        header = tk.Frame(self.root, bg=CLR["accent"], height=52)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Моделирование пуассоновского потока заявок",
            font=("Segoe UI Semibold", 12),
            fg="#FFFFFF", bg=CLR["accent"],
        ).pack(side="left", padx=18, pady=14)

        #  Основная область (left panel + right panel) 
        body = tk.Frame(self.root, bg=CLR["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=12)

        left = tk.Frame(body, bg=CLR["bg"], width=310)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=CLR["bg"])
        right.pack(side="left", fill="both", expand=True)

        self._build_left(left)
        self._build_right(right)

    def _build_left(self, parent):
        #  Карточка параметров 
        card = tk.Frame(parent, bg=CLR["surface"],
                        highlightthickness=1, highlightbackground=CLR["border"])
        card.pack(fill="x", pady=(0, 10))

        tk.Label(card, text="Параметры", font=FONT_H1,
                 fg=CLR["text_h"], bg=CLR["surface"]).pack(anchor="w", padx=14, pady=(12, 8))
        _sep(card).pack(fill="x", padx=14)

        params = [
            ("Интенсивность  λ  (заявок/сек)", "5.0",  "lambda"),
            ("Интервал времени  T  (сек)",      "10.0", "T"),
            ("Число экспериментов  N",           "1000", "N"),
        ]
        self._entries = {}
        for text, default, key in params:
            row = tk.Frame(card, bg=CLR["surface"])
            row.pack(fill="x", padx=14, pady=6)
            tk.Label(row, text=text, font=FONT_LABEL,
                     fg=CLR["muted"], bg=CLR["surface"]).pack(anchor="w")
            e, var = _styled_entry(row, default, width=20)
            e.pack(fill="x", ipady=5, pady=(3, 0))
            self._entries[key] = var

        btn_frame = tk.Frame(card, bg=CLR["surface"])
        btn_frame.pack(fill="x", padx=14, pady=(8, 14))
        self._run_btn = tk.Button(
            btn_frame,
            text="▶  Запустить моделирование",
            font=("Segoe UI Semibold", 10),
            bg=CLR["accent"], fg="#FFFFFF",
            activebackground="#3B47B8", activeforeground="#FFFFFF",
            relief="flat", bd=0, cursor="hand2",
            command=self.run_simulation,
        )
        self._run_btn.pack(fill="x", ipady=9)

        #  Статус 
        self._status_var = tk.StringVar(value="Введите параметры и запустите моделирование.")
        tk.Label(
            parent, textvariable=self._status_var,
            font=FONT_LABEL, fg=CLR["muted"], bg=CLR["bg"],
            wraplength=290, justify="left",
        ).pack(anchor="w", pady=(0, 10))

        #  Карточки метрик 
        metrics_lbl = tk.Frame(parent, bg=CLR["bg"])
        metrics_lbl.pack(fill="x")
        tk.Label(metrics_lbl, text="Эмпирические характеристики",
                 font=FONT_H2, fg=CLR["text_h"], bg=CLR["bg"]).pack(anchor="w")

        grid = tk.Frame(parent, bg=CLR["bg"])
        grid.pack(fill="x", pady=(6, 0))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self._card_mean  = MetricCard(grid, "Среднее  (M)")
        self._card_var   = MetricCard(grid, "Дисперсия  (D)")
        self._card_std   = MetricCard(grid, "Ст. отклонение  (σ)")
        self._card_range = MetricCard(grid, "Диапазон  [min, max]")

        self._card_mean .grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))
        self._card_var  .grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))
        self._card_std  .grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        self._card_range.grid(row=1, column=1, sticky="nsew", padx=(5, 0))


    def _build_right(self, parent):
        tk.Label(parent, text="Графики", font=FONT_H2,
                 fg=CLR["text_h"], bg=CLR["bg"]).pack(anchor="w")

        plot_card = tk.Frame(parent, bg=CLR["surface"],
                             highlightthickness=1, highlightbackground=CLR["border"])
        plot_card.pack(fill="both", expand=True, pady=(6, 0))

        plt.rcParams.update({
            "font.family":       "Segoe UI",
            "axes.facecolor":    CLR["surface"],
            "figure.facecolor":  CLR["surface"],
            "axes.edgecolor":    CLR["border"],
            "axes.spines.top":   False,
            "axes.spines.right": False,
            "axes.labelcolor":   CLR["text"],
            "xtick.color":       CLR["muted"],
            "ytick.color":       CLR["muted"],
            "grid.color":        CLR["border"],
            "grid.linestyle":    "--",
            "axes.titleweight":  "normal",
            "axes.titlesize":    10,
            "axes.labelsize":    9,
        })

        self.fig = plt.Figure(figsize=(8, 5), dpi=100)
        self.fig.patch.set_facecolor(CLR["surface"])
        self.axes = [
            self.fig.add_subplot(1, 2, 1),
            self.fig.add_subplot(1, 2, 2),
        ]
        self.fig.tight_layout(pad=2.8)

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    #  Логика 

    def run_simulation(self):
        try:
            lambda_rate = float(self._entries["lambda"].get())
            T           = float(self._entries["T"].get())
            N           = int(self._entries["N"].get())

            if lambda_rate <= 0 or T <= 0 or N <= 0:
                raise ValueError("Все параметры должны быть положительными!")

            self._status_var.set("Идёт моделирование…")
            self.root.update_idletasks()

            self.model = PoissonFlowModel(lambda_rate, T, N)
            self.model.run_experiments()

            st = self.model.get_statistics()
            self._update_cards(st)
            self.plot_results()

            self._status_var.set(
                f"Готово — {N} экспериментов, λT = {lambda_rate * T:.2f}"
            )

        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{e}")

    def _update_cards(self, st):
        """Заполнение карточек метрик после расчёта."""
        self._card_mean.set(
            f"{st['mean']:.4f}",
            sub=f"теор. {st['theoretical_mean']:.4f}",
        )
        self._card_var.set(
            f"{st['variance']:.4f}",
            sub=f"теор. {st['theoretical_variance']:.4f}",
        )
        self._card_std.set(f"{st['std']:.4f}")
        self._card_range.set(f"[{st['min']},  {st['max']}]")

    def plot_results(self):
        """Построение графиков — логика не изменена, только стиль."""
        for ax in self.axes:
            ax.clear()

        #  График 1: Распределение числа заявок 
        values, frequencies = self.model.get_distribution()
        lambda_T = self.model.lambda_rate * self.model.T
        x_theor  = np.arange(0, max(values) + 5)
        y_theor  = stats.poisson.pmf(x_theor, lambda_T)

        self.axes[0].bar(
            values, frequencies, alpha=0.75,
            label="Эмпирическое",
            color=CLR["accent"], edgecolor=CLR["surface"], linewidth=0.8,
        )
        self.axes[0].plot(
            x_theor, y_theor, "o-",
            color=CLR["danger"],
            label=f"Пуассон  λT={lambda_T:.2f}",
            markersize=4, linewidth=1.5,
        )
        self.axes[0].set_xlabel("Число заявок за T")
        self.axes[0].set_ylabel("Вероятность")
        self.axes[0].set_title("Распределение числа заявок")
        self.axes[0].legend(fontsize=8)
        self.axes[0].grid(True, alpha=0.5)

        #  График 2: Временная диаграмма потока 
        if self.model.event_times:
            y_ev = np.ones(len(self.model.event_times))
            self.axes[1].scatter(
                self.model.event_times, y_ev,
                color=CLR["accent"], s=120, marker="|",
                linewidths=2, label="Заявки",
            )
            self.axes[1].set_xlim(0, self.model.T)
            self.axes[1].set_ylim(0.5, 1.5)
            self.axes[1].set_xlabel("Время (сек)")
            self.axes[1].set_yticks([])
            self.axes[1].set_title(
                f"Пример потока  (N={len(self.model.event_times)} заявок,  T={self.model.T} сек)"
            )
            self.axes[1].axhline(y=1, color=CLR["border"], linestyle="--", linewidth=1)
            self.axes[1].grid(True, alpha=0.4, axis="x")

            if len(self.model.event_times) > 1:
                intervals    = np.diff([0] + self.model.event_times)
                mean_interval = np.mean(intervals)
                self.axes[1].text(
                    0.02, 0.93,
                    f"Средний интервал: {mean_interval:.3f} сек\n"
                    f"Теоретический:    {1/self.model.lambda_rate:.3f} сек",
                    transform=self.axes[1].transAxes,
                    fontsize=8, va="top",
                    bbox=dict(boxstyle="round,pad=0.5",
                              facecolor=CLR["accent_light"],
                              edgecolor=CLR["border"], linewidth=0.7),
                    color=CLR["text"],
                )

        self.fig.tight_layout(pad=2.8)
        self.canvas.draw()


def main():
    root = tk.Tk()
    app = PoissonFlowGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
