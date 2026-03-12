import tkinter as tk
from tkinter import ttk
import random
import math

# =============================
# ОКНО
# =============================
root = tk.Tk()
root.title("Random Event Simulator")
root.geometry("600x500")
root.configure(bg="#1e1e1e")
root.resizable(False, False)

style = ttk.Style()
style.theme_use("clam")

style.configure("TNotebook",
                background="#1e1e1e",
                borderwidth=0)

style.configure("TNotebook.Tab",
                background="#2a2a2a",
                foreground="#eaeaea",
                padding=10)

style.map("TNotebook.Tab",
          background=[("selected", "#4cc9f0")],
          foreground=[("selected", "#000000")])

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# =============================
# ВКЛАДКА 1 — ДА / НЕТ
# =============================
frame1 = tk.Frame(notebook, bg="#1e1e1e")
notebook.add(frame1, text="Да / Нет")

result_label = tk.Label(frame1,
                        text="?",
                        font=("Segoe UI", 60, "bold"),
                        fg="#4cc9f0",
                        bg="#1e1e1e")
result_label.pack(pady=80)

def yes_no():
    result = random.choice(["ДА", "НЕТ"])
    color = "#00e676" if result == "ДА" else "#ff5252"
    result_label.config(text=result, fg=color)

btn_yesno = tk.Button(frame1,
                      text="СПРОСИТЬ",
                      command=yes_no,
                      font=("Segoe UI", 14, "bold"),
                      bg="#2a2a2a",
                      fg="#eaeaea",
                      activebackground="#4cc9f0",
                      relief="flat",
                      padx=20,
                      pady=10)
btn_yesno.pack()

# =============================
# ВКЛАДКА 2 — MAGIC 8 BALL (Изменил на твой алгоритм)
# =============================
frame2 = tk.Frame(notebook, bg="#1e1e1e")
notebook.add(frame2, text="Magic 8-Ball")

canvas = tk.Canvas(frame2, width=400, height=400, bg="#1e1e1e", highlightthickness=0)
canvas.pack(pady=20)

center = 200
radius = 150

# Градиентный шар
base_r, base_g, base_b = 110, 198, 255
for i in range(120):
    factor = i / 120
    r = int(base_r * (1-factor) + 20*factor)
    g = int(base_g * (1-factor) + 20*factor)
    b = int(base_b * (1-factor) + 20*factor)
    color = f"#{r:02x}{g:02x}{b:02x}"
    canvas.create_oval(center-radius+i*1.2, center-radius+i*1.2,
                      center+radius-i*1.2, center+radius-i*1.2, fill=color, outline="")

canvas.create_oval(center-radius, center-radius, center+radius, center+radius, outline="#0a0a0a", width=4)

# Шестиугольник
hex_radius = 95
hex_coords = []
for i in range(6):
    angle = math.radians(60 * i - 30)
    x = center + hex_radius * math.cos(angle)
    y = center + hex_radius * math.sin(angle) 
    hex_coords.extend([x, y])

polygon = canvas.create_polygon(hex_coords, fill="#042E49", outline="")
text_item = canvas.create_text(center, center, text="", fill="white", font=("Segoe UI", 14, "bold"), justify="center")

# ТВОИ СОБЫТИЯ для Magic 8-Ball
magic_answers = [
    ("Да", 0.125), ("Нет", 0.125), ("Скорее всего", 0.125), ("Сомнительно", 0.125),
    ("Без сомнений", 0.125), ("Спроси позже", 0.125), ("Определенно да", 0.125), ("Маловероятно", 0.125)
]

spinning = False
current_angle = 0

def rotate_polygon(angle):
    coords = []
    for i in range(0, len(hex_coords), 2):
        x = hex_coords[i] - center
        y = hex_coords[i+1] - center
        new_x = x*math.cos(angle) - y*math.sin(angle)
        new_y = x*math.sin(angle) + y*math.cos(angle)
        coords.extend([new_x+center, new_y+center])
    canvas.coords(polygon, coords)
    canvas.coords(text_item, center, center)

def spin(step=0, total_steps=60):
    global current_angle, spinning
    if step < total_steps:
        angle_per_step = (2*3.14159265)/total_steps
        current_angle += angle_per_step
        rotate_polygon(current_angle)
        canvas.itemconfig(text_item, text="")
        root.after(16, spin, step+1, total_steps)
    else:
        current_angle = 0
        rotate_polygon(current_angle)
        spinning = False
        show_prediction()

def fade_in(text, alpha=0):
    if alpha <= 1:
        val = int(255 * alpha)
        color = f"#{val:02x}{val:02x}{val:02x}"
        canvas.itemconfig(text_item, text=text, fill=color, font=("Segoe UI", 14, "bold"))
        root.after(30, fade_in, text, alpha+0.08)

def show_prediction():
    global text_visible
    rand_val = random.random()  
    A = 1                    
    k = 0                       
    
    while True:
        k += 1                   
        answer_name, Pk = magic_answers[k-1]  
        A = A - Pk              
        
        if A <= rand_val:        
            fade_in(answer_name) 
            return

def click_ball(event):
    global spinning
    if spinning: return
    spin()

canvas.bind("<Button-1>", click_ball)

root.mainloop()
