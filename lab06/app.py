import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from scipy import stats
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random


Ns = [10, 100, 1000, 10000]


def get_prediction(answers):
    rand_val = random.random()
    A = 1
    k = 0

    while True:
        k += 1
        answer_name, Pk = answers[k - 1]
        A = A - Pk

        if A <= rand_val:
            return answer_name

class App:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная работа №6")
        root.geometry("1100x800")

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)

        self.tab1 = ttk.Frame(self.tabs)
        self.tab2 = ttk.Frame(self.tabs)

        self.tabs.add(self.tab1, text="lab06-1 Дискретная СВ")
        self.tabs.add(self.tab2, text="lab06-2 Нормальная СВ")

        self.build_discrete()
        self.build_normal()

    def build_discrete(self):
        top = ttk.Frame(self.tab1)
        top.pack(fill="x", pady=5)

        ttk.Label(top, text="X").grid(row=0, column=0)
        ttk.Label(top, text="P").grid(row=0, column=1)

        self.x_entries = []
        self.p_entries = []

        default_x = [1, 2, 3, 4, 5]
        default_p = [0.2, 0.2, 0.2, 0.2, 0.2]

        for i in range(5):
            ex = ttk.Entry(top, width=6)
            ex.insert(0, str(default_x[i]))
            ex.grid(row=i + 1, column=0, padx=2)
            self.x_entries.append(ex)

            ep = ttk.Entry(top, width=6)
            ep.insert(0, str(default_p[i]))
            ep.grid(row=i + 1, column=1, padx=2)
            self.p_entries.append(ep)

        ttk.Button(
            top,
            text="Запустить моделирование",
            command=self.run_discrete
        ).grid(row=1, column=2, rowspan=5, padx=10)

        self.tree1 = ttk.Treeview(
            self.tab1,
            columns=("N", "M", "ErrM", "D", "ErrD", "Chi2", "Res"),
            show="headings",
            height=5
        )

        headers = [
            "N",
            "M (эмп)",
            "M ошибка %",
            "D (эмп)",
            "D ошибка %",
            "χ²",
            "Критерий"
        ]

        for col, h in zip(self.tree1["columns"], headers):
            self.tree1.heading(col, text=h)
            self.tree1.column(col, width=130, anchor="center")

        self.tree1.pack(fill="x", pady=5)

        self.fig1 = Figure(figsize=(8, 6))
        self.ax_d1 = self.fig1.add_subplot(221)
        self.ax_d2 = self.fig1.add_subplot(222)
        self.ax_d3 = self.fig1.add_subplot(223)
        self.ax_d4 = self.fig1.add_subplot(224)

        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.tab1)
        self.canvas1.get_tk_widget().pack(fill="both", expand=True)

    def run_discrete(self):

        try:
            values = []
            probs = []

            for i in range(len(self.x_entries)):
                x = self.x_entries[i].get().strip()
                p = self.p_entries[i].get().strip()

                if x and p:
                    values.append(float(x))
                    probs.append(float(p))

            if len(values) < 2:
                raise ValueError("Введите хотя бы 2 значения")

            values = np.array(values)
            probs = np.array(probs)

            if np.any(probs <= 0):
                raise ValueError("Все вероятности должны быть положительными")

            if not np.isclose(np.sum(probs), 1.0):
                raise ValueError("Сумма вероятностей должна быть 1")

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return

        self.tree1.delete(*self.tree1.get_children())

        axes = [self.ax_d1, self.ax_d2, self.ax_d3, self.ax_d4]
        for ax in axes:
            ax.clear()
        
        # "M (эмп)",
        # "M ошибка %",
        # "D (эмп)",
        # "D ошибка %",
        # "χ²",
        # "Критерий"
        
        m_teor = np.sum(values * probs)
        d_teor = np.sum(values**2 * probs) - m_teor**2

        answers = list(zip(values.tolist(), probs.tolist()))

        for i, N in enumerate(Ns):

            samples = np.array([get_prediction(answers) for _ in range(N)])

            m_emp = np.mean(samples)
            d_emp = np.var(samples)

            err_m = abs(m_emp - m_teor) / abs(m_teor) * 100 if abs(m_teor) > 1e-9 else float('nan')
            err_d = abs(d_emp - d_teor) / d_teor * 100 if d_teor > 1e-9 else float('nan')

            observed = np.array([np.sum(samples == v) for v in values])
            expected = probs * N

            chi_stat, _ = stats.chisquare(observed, f_exp=expected)
            chi_crit = stats.chi2.ppf(0.95, df=len(values) - 1)

            status = "ПРОЙДЕН" if chi_stat < chi_crit else "ОТКЛОНЕН"

            err_m_str = f"{err_m:.2f}" if not np.isnan(err_m) else "N/A"
            err_d_str = f"{err_d:.2f}" if not np.isnan(err_d) else "N/A"

            self.tree1.insert(
                "",
                "end",
                values=(
                    N,
                    f"{m_emp:.3f}",
                    err_m_str,
                    f"{d_emp:.3f}",
                    err_d_str,
                    f"{chi_stat:.3f}",
                    status
                )
            )

            x = np.arange(len(values))
            axes[i].bar(x - 0.2, probs, 0.4, label="Теория", color="steelblue")
            axes[i].bar(x + 0.2, observed / N, 0.4, label="Эмп", color="orange")
            axes[i].set_xticks(x)
            axes[i].set_xticklabels(values)
            axes[i].set_title(f"N = {N}")
            axes[i].legend(fontsize=8)

        self.fig1.tight_layout(pad=3.0)
        self.canvas1.draw()

    def build_normal(self):

        top = ttk.Frame(self.tab2)
        top.pack(fill="x", pady=5)

        ttk.Label(top, text="Среднее (mu)").grid(row=0, column=0)
        self.mu_entry = ttk.Entry(top, width=8)
        self.mu_entry.insert(0, "0")
        self.mu_entry.grid(row=0, column=1)

        ttk.Label(top, text="Отклонение (sigma)").grid(row=0, column=2)
        self.sigma_entry = ttk.Entry(top, width=8)
        self.sigma_entry.insert(0, "1")
        self.sigma_entry.grid(row=0, column=3)

        ttk.Button(
            top,
            text="Запустить моделирование",
            command=self.run_normal
        ).grid(row=0, column=4, padx=10)

        self.tree2 = ttk.Treeview(
            self.tab2,
            columns=("N", "M", "ErrM", "D", "ErrD", "Chi2", "Res"),
            show="headings",
            height=5
        )

        headers = [
            "N",
            "M (эмп)",
            "M ошибка %",
            "D (эмп)",
            "D ошибка %",
            "χ²",
            "Критерий"
        ]

        for col, h in zip(self.tree2["columns"], headers):
            self.tree2.heading(col, text=h)
            self.tree2.column(col, width=120, anchor="center")

        self.tree2.pack(fill="x", pady=5)

        self.fig2 = Figure(figsize=(8, 6))
        self.ax_n1 = self.fig2.add_subplot(221)
        self.ax_n2 = self.fig2.add_subplot(222)
        self.ax_n3 = self.fig2.add_subplot(223)
        self.ax_n4 = self.fig2.add_subplot(224)

        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.tab2)
        self.canvas2.get_tk_widget().pack(fill="both", expand=True)

    def run_normal(self):

        try:
            mu = float(self.mu_entry.get())
            sigma = float(self.sigma_entry.get())
            if sigma <= 0:
                raise ValueError("Sigma должна быть положительной")
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return

        self.tree2.delete(*self.tree2.get_children())

        axes = [self.ax_n1, self.ax_n2, self.ax_n3, self.ax_n4]
        for ax in axes:
            ax.clear()

        for i, N in enumerate(Ns):

            u1 = np.random.rand(N)
            u2 = np.random.rand(N)

            samples = np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2)
            samples = samples * sigma + mu

            m_emp = np.mean(samples)
            d_emp = np.var(samples)

            if abs(mu) > 1e-9:
                err_m = abs(m_emp - mu) / abs(mu) * 100
                err_m_str = f"{err_m:.2f}"
            else:
                err_m_str = f"{abs(m_emp - mu):.4f} (абс)"

            err_d = abs(d_emp - sigma**2) / sigma**2 * 100

            counts, bins = np.histogram(samples, bins=10)
            cdf = stats.norm.cdf(bins, mu, sigma)
            probs = np.diff(cdf)
            expected = probs / np.sum(probs) * N

            chi_stat, _ = stats.chisquare(counts, f_exp=expected)
            chi_crit = stats.chi2.ppf(0.95, df=9)

            status = "ПРОЙДЕН" if chi_stat < chi_crit else "ОТКЛОНЕН"

            self.tree2.insert(
                "",
                "end",
                values=(
                    N,
                    f"{m_emp:.3f}",
                    err_m_str,
                    f"{d_emp:.3f}",
                    f"{err_d:.2f}",
                    f"{chi_stat:.3f}",
                    status
                )
            )

            axes[i].hist(samples, bins=30, density=True, alpha=0.6,
                         color="steelblue", label="Выборка")

            x = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 200)
            pdf = stats.norm.pdf(x, mu, sigma)

            axes[i].plot(x, pdf, color="red", linewidth=1.5, label="N(μ,σ²)")
            axes[i].set_title(f"N = {N}")
            axes[i].legend(fontsize=8)

        self.fig2.tight_layout(pad=3.0)
        self.canvas2.draw()


root = tk.Tk()
app = App(root)
root.mainloop()
