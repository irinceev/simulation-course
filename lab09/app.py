import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SimulationEngine:
    def __init__(self, arrival_rate, service_rate, max_time):
        self.arrival_rate = arrival_rate #лямбда
        self.service_rate = service_rate #мю
        self.max_time = max_time #время
        self.current_time = 0.0
        self.is_busy = 0
        self.history = []
        self.total_customers = 0
        self.lost_customers = 0

    def run_simulation(self):
        time_to_arrival = np.random.exponential(1 / self.arrival_rate) #времени до следующей заявки
        time_to_departure = float('inf') # время до завершения обслуживания

        while self.current_time < self.max_time:
            self.history.append((self.current_time, self.is_busy))
            if time_to_arrival < time_to_departure:

                self.current_time += time_to_arrival
                if self.is_busy == 1:
                    time_to_departure -= time_to_arrival
                self.total_customers += 1
                if self.is_busy == 0:
                    self.is_busy = 1
                    time_to_departure = np.random.exponential(1 / self.service_rate)
                else:
                    self.lost_customers += 1

                time_to_arrival = np.random.exponential(1 / self.arrival_rate)
            else:
                self.current_time += time_to_departure
                time_to_arrival -= time_to_departure
                self.is_busy = 0
                time_to_departure = float('inf')

        self.history.append((self.max_time, self.is_busy))
        return self.total_customers, self.lost_customers

    def calculate_free_time_probability(self):
        total_free_time = 0.0
        for i in range(len(self.history) - 1):
            if self.history[i][1] == 0:
                total_free_time += (self.history[i+1][0] - self.history[i][0])
        return total_free_time / self.max_time


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Моделирование системы обслуживания (М/М/1/0)")
        self.root.geometry("750x450")

        # Верхняя панель для ввода параметров
        settings_frame = tk.Frame(root, pady=15)
        settings_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(settings_frame, text="Поток заявок (лямбда):").pack(side=tk.LEFT, padx=5)
        self.entry_arrival = tk.Entry(settings_frame, width=4)
        self.entry_arrival.insert(0, "4.0")
        self.entry_arrival.pack(side=tk.LEFT, padx=5)

        tk.Label(settings_frame, text="Интенсивность обслуживания (мю):").pack(side=tk.LEFT, padx=5)
        self.entry_service = tk.Entry(settings_frame, width=4)
        self.entry_service.insert(0, "3.0")
        self.entry_service.pack(side=tk.LEFT, padx=5)

        tk.Label(settings_frame, text="Время моделирования:").pack(side=tk.LEFT, padx=5)
        self.entry_time = tk.Entry(settings_frame, width=5)
        self.entry_time.insert(0, "1000")
        self.entry_time.pack(side=tk.LEFT, padx=5)

        btn_start = tk.Button(settings_frame, text="Запустить", command=self.start_process, bg="#e0e0e0", width=12)
        btn_start.pack(side=tk.LEFT, padx=2)

        #Текстовый вывод результатов
        self.text_output = tk.Text(root, width=42, font=("Courier New", 10), bd=1, relief="solid")
        self.text_output.pack(side=tk.BOTTOM, fill=tk.Y, padx=15, pady=10)
        
    def start_process(self):
        try:
            arrival_rate = float(self.entry_arrival.get())
            service_rate = float(self.entry_service.get())
            max_time = float(self.entry_time.get())

            # Запуск расчетов
            sim = SimulationEngine(arrival_rate, service_rate, max_time)
            total, lost = sim.run_simulation()
            p0_practical = sim.calculate_free_time_probability()
            ploss_practical = lost / total if total > 0 else 0

            # Теоретические формулы
            rho = arrival_rate / service_rate
            p0_theoretical = 1 / (1 + rho)
            ploss_theoretical = rho / (1 + rho)

            # Формирование понятного текстового отчета
            report = (
                f" Исходная загрузка системы: {rho:.2f}\n"
                f" Всего поступило заявок:    {total}\n"
                f" Из них отклонено (отказ):  {lost}\n"
                f"-------------------------------------\n"
                f" Вероятность, что система свободна:\n"
                f"   Математическая теория: {p0_theoretical:.4f}\n"
                f"   Данные симуляции:      {p0_practical:.4f}\n"
                f"-------------------------------------\n"
                f" Вероятность отказа в обслуживании:\n"
                f"   Математическая теория: {ploss_theoretical:.4f}\n"
                f"   Данные симуляции:      {ploss_practical:.4f}\n"
            )
            self.text_output.delete("1.0", tk.END)
            self.text_output.insert(tk.END, report)

        except Exception as error:
            self.text_output.delete("1.0", tk.END)
            self.text_output.insert(tk.END, f"Ошибка при вводе данных:\n{str(error)}")

if __name__ == "__main__":
    app_root = tk.Tk()
    MainWindow(app_root)
    app_root.mainloop()