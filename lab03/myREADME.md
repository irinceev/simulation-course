### Клеточные автоматы. Лесные пожары

**Задание:**  
Реализовать моделирование возникновения и распространения лесных пожаров с использованием двумерного клеточного автомата.

Правила:

## 1. Состояния клеток

Клетка может быть в одном из пяти состояний:

EMPTY, TREE, FIRE, ASH, WATER = 0, 1, 2, 3, 4

EMPTY — пустая клетка

TREE — дерево

FIRE — горящее дерево

ASH — выгоревшая клетка

WATER — вода

## 2. Инициализация сетки

Случайное заполнение дерева и пустыми клетками:

grid = np.random.choice([EMPTY, TREE], size=(GRID_SIZE, GRID_SIZE), p=[0.4, 0.6])

## 3. Соседство

Используется окрестность Мура — 8 соседей:

for dx in [-1, 0, 1]:
    for dy in [-1, 0, 1]:
        if dx == 0 and dy == 0:
            continue

## 5. Правила переходов
# 5.1 Самовозгорание дерева
if random.random() < lightning_prob:
    new_grid[x, y] = FIRE

TREE → FIRE по случайной молнии.

# 5.2 Горение от соседей

Если соседняя клетка горит:

if grid[nx, ny] == FIRE:
    prob = base_fire_spread

# 5.3 Ветер

Влияние ветра на направление распространения:

wind_len = (wind[0]**2 + wind[1]**2)**0.5
wind_x = wind[0] / wind_len
wind_y = wind[1] / wind_len

dir_len = (dir_x**2 + dir_y**2)**0.5
dir_x /= dir_len
dir_y /= dir_len

dot = wind_x * dir_x + wind_y * dir_y
prob += dot * wind_strength

# 5.4 Влажность

Уменьшает вероятность возгорания:

prob *= (1 - humidity)

# 5.5 Ограничение вероятности
prob = max(0, min(1, prob))

# 5.6 Проверка возгорания дерева
if random.random() < prob:
    new_grid[x, y] = FIRE
# 5.7 Горящая клетка → пепел
elif state == FIRE:
    new_grid[x, y] = ASH
# 5.8 Распад пепла
if random.random() < ash_decay:
    new_grid[x, y] = EMPTY

ASH → EMPTY с небольшой вероятностью.

# 5.9 Рост деревьев
elif state == EMPTY:
    if random.random() < tree_growth:
        new_grid[x, y] = TREE

EMPTY → TREE.

# 5.10 Взаимодействие с водой
if grid[nx, ny] == WATER:
    prob *= 0.5

Вода замедляет распространение огня.

## 6. Синхронное обновление сетки
new_grid = grid.copy()
...
grid = new_grid

Все клетки обновляются одновременно в каждом шаге симуляции.

## 7. Действия пользователя

Поджечь случайное дерево:

grid[x, y] = FIRE

Добавить воду:

grid[x, y] = WATER

Пауза/старт и перезапуск симуляции через UI.


