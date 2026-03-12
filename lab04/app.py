import statistics
import random
import matplotlib.pyplot as plt
import numpy as np

# LCG генератор
def lcg_random(seed=1, n=100000):
    m = 2**32
    a = 1664525
    c = 1013904223
    numbers = []
    x = seed
    for i in range(n):
        x = (a * x + c) % m
        numbers.append(x / m)
    return numbers

# Генерация данных
lcg_nums = lcg_random()
lcg_mean = statistics.mean(lcg_nums)
lcg_var = statistics.variance(lcg_nums)

random.seed(1)
rand_nums = [random.random() for _ in range(100000)]
rand_mean = statistics.mean(rand_nums)
rand_var = statistics.variance(rand_nums)

# Теоретические значения  мю=0.5, сигмакв=1/12
theory_mean = 0.5
theory_var = 1/12 

print("Результаты:")
print(f"LCG: среднее={lcg_mean:.6f}, дисперсия={lcg_var:.6f}")
print(f"random: среднее={rand_mean:.6f}, дисперсия={rand_var:.6f}")
print(f"Теория: среднее={theory_mean:.6f}, дисперсия={theory_var:.6f}")

# График с гистограммами и таблицей
fig = plt.figure(figsize=(14, 6))

# Гистограммы
ax1 = plt.subplot(1, 2, 1)
ax1.hist(lcg_nums, bins=50, density=True, alpha=0.7, label='LCG', color='red', edgecolor='black')
ax1.hist(rand_nums, bins=50, density=True, alpha=0.7, label='random', color='green', edgecolor='black')

# Теоретическая плотность U[0,1)
x = np.linspace(0, 1, 100)
ax1.plot(x, np.ones_like(x), 'r--', linewidth=2, label='Теоретическая плотность')

ax1.set_title('Распределение случайных чисел (n=100000)')
ax1.set_xlabel('Значение')
ax1.set_ylabel('Плотность')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Таблица результатов
ax2 = plt.subplot(1, 2, 2)
ax2.axis('tight')
ax2.axis('off')

# Данные для таблицы
table_data = [
    ['Параметр', 'Теория', 'LCG', 'random'],
    ['Среднее', f'{theory_mean:.6f}', f'{lcg_mean:.6f}', f'{rand_mean:.6f}'],
    ['Дисперсия', f'{theory_var:.6f}', f'{lcg_var:.6f}', f'{rand_var:.6f}']
]

# Создание таблицы
table = ax2.table(cellText=table_data[1:], colLabels=table_data[0],
                  cellLoc='center', loc='center',
                  colColours=['#f0f0f0']*4,
                  cellColours=[['#e6f3ff']*4]*2)

table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1, 2)

ax2.set_title('Сравнение статистик выборки', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.show()
