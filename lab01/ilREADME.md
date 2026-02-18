### Моделирование полёта тела в атмосфере

**Задание:**  
Реализовать приложение для моделирования полёта тела в атмосфере.  
Предусмотреть возможность ввода шага моделирования и вывода результатов.

Выполнить моделирование **без очистки предыдущих результатов** для различных шагов моделирования, сравнить траектории и заполнить таблицу:

**Сделать выводы.**

**В отчёт включить:**

* код программы;
* скриншот с несколькими траекториями;
* заполненную таблицу;
* выводы.

---

Код программы:

    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import tkinter as tk
    from tkinter import ttk, messagebox
    
    G = 9.81 
    RHO_0 = 1.225  
    C = 0.15 
    
    class FlightSimulator:
        def __init__(self):
            self.state = {}
        def get_derivatives(self, state, dt, m, S):
            # Вспомогательная функция вычисляет скорости и ускорения
            x, y, vx, vy = state
            v = np.sqrt(vx**2 + vy**2)
            k = 0.5 * C * RHO_0 * S / m
    
            # Ускорения (dv/dt)
            ax = -k * vx * v
            ay = -G - k * vy * v
    
            #производные: [dx/dt, dy/dt, dvx/dt, dvy/dt]
            return np.array([vx, vy, ax, ay])
    
        def step_rk4(self, x, y, vx, vy, dt, m, S):
            # Один шаг методом Рунге-Кутты 4 порядка
            state = np.array([x, y, vx, vy])
    
            k1 = self.get_derivatives(state, dt, m, S)
            k2 = self.get_derivatives(state + k1 * dt / 2, dt, m, S)
            k3 = self.get_derivatives(state + k2 * dt / 2, dt, m, S)
            k4 = self.get_derivatives(state + k3 * dt, dt, m, S)
    
            # Итоговое изменение
            delta = (k1 + 2*k2 + 2*k3 + k4) * dt / 6
    
            return x + delta[0], y + delta[1], vx + delta[2], vy + delta[3]
    
        def simulate(self, v0, angle, dt, m=1.0, S=0.01):
            angle_rad = np.radians(angle)
    
            t, x, y = 0, 0.0, 0.0
            vx = v0 * np.cos(angle_rad)
            vy = v0 * np.sin(angle_rad)
    
            traj_x, traj_y = [x], [y]
            max_h = 0.0
    
            while y >= 0:
                x, y, vx, vy = self.step_rk4(x, y, vx, vy, dt, m, S)
                t += dt
    
                if y >= 0:
                    traj_x.append(x)
                    traj_y.append(y)
                    max_h = max(max_h, y)
    
            final_v = np.sqrt(vx**2 + vy**2)
            return {'x': traj_x, 'y': traj_y, 'range': x, 'max_height': max_h, 'final_velocity': final_v, 'dt': dt}
    
        def start_step_simulation(self, v0, angle, dt, m=1.0, S=0.01):
            angle_rad = np.radians(angle)
            self.state = {
                't': 0,
                'x': 0.0,
                'y': 0.0,
                'vx': v0 * np.cos(angle_rad),
                'vy': v0 * np.sin(angle_rad),
                'm': m,
                'S': S,
                'dt': dt,
                'running': True
            }
            return self.state['x'], self.state['y']
    
        def next_step(self):
            s = self.state
            if not s.get('running', False):
                return None
            
            s['x'], s['y'], s['vx'], s['vy'] = self.step_rk4(
                s['x'], s['y'], s['vx'], s['vy'], s['dt'], s['m'], s['S']
            )
            s['t'] += s['dt']
    
            if s['y'] < 0:
                s['running'] = False
    
            return s['x'], s['y']
    class SimulationApp:
        def __init__(self, root):
            self.root = root
            self.root.title("Моделирование полёта тела в атмосфере")
            self.root.geometry("1200x800")
    
            self.simulator = FlightSimulator()
            self.results = []
    
            self.is_animating = False
            self.animation_data = {}
    
            self.create_widgets()
    
        def create_widgets(self):
            control_frame = ttk.LabelFrame(self.root, text="Параметры моделирования", padding=10)
            control_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
    
            ttk.Label(control_frame, text="Начальная скорость (м/с):").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.v0_entry = ttk.Entry(control_frame, width=15)
            self.v0_entry.insert(0, "20")
            self.v0_entry.grid(row=0, column=1, pady=5)
    
            ttk.Label(control_frame, text="Угол запуска (градусы):").grid(row=1, column=0, sticky=tk.W, pady=5)
            self.angle_entry = ttk.Entry(control_frame, width=15)
            self.angle_entry.insert(0, "50")
            self.angle_entry.grid(row=1, column=1, pady=5)
    
            ttk.Label(control_frame, text="Шаг моделирования (с):").grid(row=2, column=0, sticky=tk.W, pady=5)
            self.dt_entry = ttk.Entry(control_frame, width=15)
            self.dt_entry.insert(0, "0.01")
            self.dt_entry.grid(row=2, column=1, pady=5)
    
            ttk.Label(control_frame, text="Масса (кг):").grid(row=3, column=0, sticky=tk.W, pady=5)
            self.m_entry = ttk.Entry(control_frame, width=15)
            self.m_entry.insert(0, "1.0")
            self.m_entry.grid(row=3, column=1, pady=5)
    
            ttk.Label(control_frame, text="Площадь (м²):").grid(row=4, column=0, sticky=tk.W, pady=5)
            self.s_entry = ttk.Entry(control_frame, width=15)
            self.s_entry.insert(0, "0.01")
            self.s_entry.grid(row=4, column=1, pady=5)
    
            self.btn_run = ttk.Button(control_frame, text="Запустить моделирование", 
                      command=self.run_simulation)
            self.btn_run.grid(row=5, column=0, columnspan=2, pady=10)
    
            ttk.Button(control_frame, text="Очистить все", 
                      command=self.clear_all).grid(row=6, column=0, columnspan=2, pady=5)
    
            ttk.Button(control_frame, text="Заполнить таблицу автоматически", 
                      command=self.auto_fill_table).grid(row=7, column=0, columnspan=2, pady=10)
    
            table_frame = ttk.LabelFrame(control_frame, text="Результаты", padding=5)
            table_frame.grid(row=8, column=0, columnspan=2, pady=10, sticky=tk.EW)
    
            columns = ('dt', 'range', 'height', 'velocity')
            self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=8)
    
            self.tree.heading('dt', text='Шаг, с')
            self.tree.heading('range', text='Дальность, м')
            self.tree.heading('height', text='Макс. высота, м')
            self.tree.heading('velocity', text='Скорость, м/с')
    
            self.tree.column('dt', width=80, anchor=tk.CENTER)
            self.tree.column('range', width=100, anchor=tk.CENTER)
            self.tree.column('height', width=120, anchor=tk.CENTER)
            self.tree.column('velocity', width=110, anchor=tk.CENTER)
    
            scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
            self.tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.tree.pack(fill=tk.BOTH, expand=True)
    
            graph_frame = ttk.Frame(self.root)
            graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
            self.fig = Figure(figsize=(8, 6))
            self.ax = self.fig.add_subplot(111)
            self.setup_plot()
    
            self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
        def setup_plot(self):
            self.ax.set_xlabel('Дальность (м)', fontsize=12)
            self.ax.set_ylabel('Высота (м)', fontsize=12)
            self.ax.set_title('Траектории полёта тела', fontsize=14, fontweight='bold')
            self.ax.grid(True, alpha=0.3)
    
        def run_simulation(self):
            if self.is_animating:
                self.stop_animation()
                return
    
            try:
                v0 = float(self.v0_entry.get())
                angle = float(self.angle_entry.get())
                dt = float(self.dt_entry.get())
                m = float(self.m_entry.get())
                S = float(self.s_entry.get())
    
                instant_result = self.simulator.simulate(v0, angle, dt, m, S)
                
                self.tree.insert('', tk.END, values=(
                    f"{dt}",
                    f"{instant_result['range']:.2f}",
                    f"{instant_result['max_height']:.2f}",
                    f"{instant_result['final_velocity']:.2f}"
                ))
    
                x, y = self.simulator.start_step_simulation(v0, angle, dt, m, S)
                
                self.current_traj_x = [x]
                self.current_traj_y = [y]
                self.max_h = 0
                
                self.anim_line, = self.ax.plot([], [], linewidth=2, label=f'dt={dt} (RK4)')
                self.ax.legend(loc='upper right')
                
                self.is_animating = True
                self.btn_run.config(text="Остановить")
                
                self.timer_tick()
    
            except ValueError:
                messagebox.showerror("Ошибка")
    
        def timer_tick(self):
            if not self.is_animating: return
    
            res = self.simulator.next_step()
    
            if res is None:
                self.stop_animation()
                s = self.simulator.state
                final_v = np.sqrt(s['vx']**2 + s['vy']**2)
    
                self.tree.insert('', tk.END, values=(
                    f"{s['dt']}",
                    f"{s['x']:.2f}",
                    f"{self.max_h:.2f}",
                    f"{final_v:.2f}"
                ))
                return
    
            x, y = res
            self.current_traj_x.append(x)
            self.current_traj_y.append(y)
            self.max_h = max(self.max_h, y)
    
            self.anim_line.set_data(self.current_traj_x, self.current_traj_y)
    
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw_idle()
    
            self.root.after(10, self.timer_tick)
    
        def stop_animation(self):
            self.is_animating = False
            self.btn_run.config(text="Запустить моделирование")
    
        def clear_all(self):
            self.stop_animation()
            self.results = []
            self.ax.clear()
            self.setup_plot()
            self.canvas.draw()
    
            for item in self.tree.get_children():
                self.tree.delete(item)
    
        def auto_fill_table(self):
            try:
                v0 = float(self.v0_entry.get())
                angle = float(self.angle_entry.get())
                m = float(self.m_entry.get())
                S = float(self.s_entry.get())
    
                steps = [1, 0.1, 0.01, 0.001, 0.0001]
                colors = plt.cm.viridis(np.linspace(0, 1, len(steps)))
    
                for i, dt in enumerate(steps):
                    result = self.simulator.simulate(v0, angle, dt, m, S)
                    self.results.append(result)
    
                    self.ax.plot(result['x'], result['y'], 
                                linewidth=2,
                                color=colors[i])
    
                    self.tree.insert('', tk.END, values=(
                        f"{dt}",
                        f"{result['range']:.2f}",
                        f"{result['max_height']:.2f}",
                        f"{result['final_velocity']:.2f}"
                    ))
    
                self.ax.legend(loc='upper right')
                self.canvas.draw()
    
            except ValueError:
                messagebox.showerror("Ошибка")
    
    if __name__ == "__main__":
        root = tk.Tk()
        app = SimulationApp(root)
        root.mainloop()

---

Скриншот с несколькими траекториями:

<img width="666" height="719" alt="image" src="https://github.com/user-attachments/assets/4a3d351f-c8cc-4878-a394-63caf72bfb09" />

---

Заполненная таблица:

|Шаг моделирования, с|1|0.1|0.01|0.001|0.0001|
|-|-|-|-|-|-|
| Дальность полёта, м | 49.98 | 39.00 | 39.00 | 38.97 | 38.97 |
| Максимальная высота, м | 10.75 | 11.76 | 11.77 | 11.77 | 11.77 |
| Скорость в конечной точке, м/с | 26.47 | 19.48 | 19.48 | 19.46 | 19.46 |

---
Вывод:
В ходе работы было реализовано приложение для моделирования полёта тела в атмосфере с предусмотренной возможность ввода шага моделирования и вывода результатов(в том числе в сразу табличном, необходимом для лабораторной, виде)

В коде для моделирования полёта тела был использован метод Рунге-Кутты 4 порядка из-за его большей точности, нежели у метода Эйлера(сходимость у РК значительно быстрее, чем у Эйлера). Это объясняется тем, что Эйлер используетс только одну производную в начале шага, грубо говоря, смотрит наклон и идёт прямо, а в РК4 вычисляется одна и та же производная, но уже в разных точках шага, и с помощью них строит плавную и точную кривую.

На заполненной таблице видно, как существенно отличаются между друг другом только первый и второй шаг(там уже почти достигнут точный результат). Далее результаты выходят практически те же самые, меняясь лишь в сотых значениях.






