import tkinter as tk
from tkinter import ttk
import numpy as np
from scipy.stats import chisquare
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ---------- Теоретическое распределение ----------
values = np.array([1, 2, 3, 4])
probs = np.array([0.25, 0.25, 0.25, 0.25])

true_mean = np.sum(values * probs)
true_var = np.sum((values - true_mean) ** 2 * probs)

Ns = [10, 100, 1000, 10000]


# ---------- МОДЕЛИ ----------
def generate_discrete(N):
    return np.random.choice(values, size=N, p=probs)


def generate_normal(N):
    return np.random.normal(0, 1, size=N)


def analyze(sample, N):
    counts = np.array([np.sum(sample == v) for v in values])
    emp_p = counts / N

    mean = np.mean(sample)
    var = np.var(sample)

    rel_m = abs(mean - true_mean) / true_mean
    rel_v = abs(var - true_var) / true_var

    chi2, p = chisquare(counts, probs * N)

    return emp_p, mean, var, rel_m, rel_v, chi2, p


# ---------- GUI ----------
class App:

    def __init__(self, root):
        self.root = root
        root.title("Распределяшки")
        root.geometry("1000x700")

        style = ttk.Style()
        style.theme_use("clam")

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)

        self.tab1 = ttk.Frame(self.tabs)
        self.tab2 = ttk.Frame(self.tabs)

        self.tabs.add(self.tab1, text="Дискретная СВ")
        self.tabs.add(self.tab2, text="Нормальная СВ")

        self.build_discrete()
        self.build_normal()

    # ---------- ДИСКРЕТНАЯ ----------
    def build_discrete(self):

        control = ttk.Frame(self.tab1)
        control.pack(side="top", fill="x", pady=5)

        # Поля для ввода вероятностей
        prob_frame = ttk.Frame(control)
        prob_frame.pack(side="left", padx=10)

        self.prob_entries = []
        for v in values:
            ttk.Label(prob_frame, text=f"P({v})").grid(row=0, column=v-1)
            entry = ttk.Entry(prob_frame, width=5)
            entry.grid(row=1, column=v-1)
            entry.insert(0, str(probs[v-1]))
            self.prob_entries.append(entry)

        # Кнопка для равномерного распределения
        ttk.Button(control,
                   text="РАВНОМЕРНОЕ",
                   command=self.set_uniform_probs).pack(side="left", padx=10)

        # Кнопка запуска моделирования
        ttk.Button(control,
                   text="Запустить моделирование",
                   command=self.run_discrete).pack(side="left", padx=10)

        # Таблица результатов
        self.tree = ttk.Treeview(self.tab1,
                                columns=("N", "Mean", "Var",
                                        "ErrMean", "ErrVar",
                                        "Chi2", "p"),
                                show="headings",
                                height=6)

        # Русские заголовки
        headers = {
            "N": "Объем выборки",
            "Mean": "Среднее",
            "Var": "Дисперсия",
            "ErrMean": "Отн. погрешн. ср.",
            "ErrVar": "Отн. погрешн. дисперсии",
            "Chi2": "χ²",
            "p": "p-значение"
        }

        for c in self.tree["columns"]:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=140)

        self.tree.pack(fill="x", pady=10)

        # Фигуры для 4 графиков
        self.fig1 = Figure(figsize=(8, 6))
        self.ax_d1 = self.fig1.add_subplot(221)
        self.ax_d2 = self.fig1.add_subplot(222)
        self.ax_d3 = self.fig1.add_subplot(223)
        self.ax_d4 = self.fig1.add_subplot(224)

        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.tab1)
        self.canvas1.get_tk_widget().pack(fill="both", expand=True)

    # ---------- Кнопка РАВНОМЕРНОЕ ----------
    def set_uniform_probs(self):
        for entry in self.prob_entries:
            entry.delete(0, tk.END)
            entry.insert(0, "0.25")
        # Обновляем массив probs для генератора
        global probs
        probs = np.array([0.25]*4)

    # ---------- Запуск моделирования ----------
    def run_discrete(self):

        # Читаем вероятности из GUI
        global probs
        try:
            new_probs = np.array([float(e.get()) for e in self.prob_entries])
            if np.any(new_probs < 0):
                raise ValueError
            if abs(new_probs.sum() - 1.0) > 1e-6:
                raise ValueError("Сумма вероятностей должна быть 1")
            probs = new_probs
        except:
            tk.messagebox.showerror("Ошибка", "Введите корректные вероятности (сумма = 1, >=0)")
            return

        self.tree.delete(*self.tree.get_children())
        axes = [self.ax_d1, self.ax_d2, self.ax_d3, self.ax_d4]

        for ax in axes:
            ax.clear()

        for i, N in enumerate(Ns):

            sample = generate_discrete(N)
            emp_p, mean, var, rm, rv, chi2, p = analyze(sample, N)

            self.tree.insert("", "end",
                             values=(N,
                                     round(mean, 4),
                                     round(var, 4),
                                     round(rm, 4),
                                     round(rv, 4),
                                     round(chi2, 4),
                                     round(p, 4)))

            # Гистограмма
            axes[i].hist(sample,
                         bins=np.arange(values.min(),
                                        values.max()+2)-0.5,
                         density=True,
                         alpha=0.8)

            axes[i].set_xticks(values)
            axes[i].set_title(f"N = {N}")

        self.fig1.suptitle("Дискретное распределение (пользовательские вероятности)")

        self.canvas1.draw()

    # ---------- НОРМАЛЬНАЯ ----------
    # ---------- НОРМАЛЬНАЯ ----------
    def build_normal(self):

        control = ttk.Frame(self.tab2)
        control.pack(side="top", fill="x", pady=5)

        ttk.Button(control,
                   text="Запустить моделирование",
                   command=self.run_normal).pack(side="left", padx=10)

        self.fig2 = Figure(figsize=(8, 6))

        self.ax_n1 = self.fig2.add_subplot(221)
        self.ax_n2 = self.fig2.add_subplot(222)
        self.ax_n3 = self.fig2.add_subplot(223)
        self.ax_n4 = self.fig2.add_subplot(224)

        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.tab2)
        self.canvas2.get_tk_widget().pack(fill="both", expand=True)

    def run_normal(self):
        axes = [self.ax_n1, self.ax_n2, self.ax_n3, self.ax_n4]

        for ax in axes:
            ax.clear()

        x = np.linspace(-4, 4, 400)
        pdf = (1 / np.sqrt(2*np.pi)) * np.exp(-x**2 / 2)

        for i, N in enumerate(Ns):

            sample = generate_normal(N)

            # Гистограмма
            axes[i].hist(sample,
                         bins=30,
                         density=True,
                         alpha=0.6)

            # Теоретическая кривая
            axes[i].plot(x, pdf,
                         linewidth=2)

            axes[i].set_title(f"N = {N}")
            # Убираем сетку и легенду
            axes[i].grid(False)

        self.fig2.suptitle("Нормальное распределение: гистограмма и плотность")

        self.canvas2.draw()


root = tk.Tk()
app = App(root)
root.mainloop()