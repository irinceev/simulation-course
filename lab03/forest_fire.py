import pygame
import numpy as np
import random

pygame.init()

MENU_WIDTH = 300
SIM_WIDTH = 900
HEIGHT = 800
WIDTH = MENU_WIDTH + SIM_WIDTH

GRID_SIZE = 180
CELL_SIZE = SIM_WIDTH // GRID_SIZE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Симулятор лесного пожара")

clock = pygame.time.Clock()

EMPTY, TREE, FIRE, ASH, WATER = 0, 1, 2, 3, 4

COLORS = {
    EMPTY: (25,25,35),
    TREE: (40,160,60),
    FIRE: (255,120,0),
    ASH: (70,70,70),
    WATER: (40,120,255)
}

base_fire_spread = 0.35
humidity = 0.2
tree_growth = 0.002
lightning_prob = 0.00005
fps = 60
wind = (0,0)
paused = False

ash_decay = 0.02
burn_time = 3

grid = np.random.choice([EMPTY, TREE], size=(GRID_SIZE, GRID_SIZE), p=[0.4,0.6])
burn_grid = np.zeros((GRID_SIZE, GRID_SIZE))

font = pygame.font.SysFont("consolas",18)
big_font = pygame.font.SysFont("consolas",22,bold=True)


class Slider:
    def __init__(self,x,y,w,min_val,max_val,value,label):
        self.rect = pygame.Rect(x,y,w,8)
        self.min=min_val
        self.max=max_val
        self.value=value
        self.label=label
        self.dragging=False

    def draw(self):
        pygame.draw.rect(screen,(60,60,70),self.rect)
        pos=(self.value-self.min)/(self.max-self.min)
        knob_x=self.rect.x+pos*self.rect.w
        pygame.draw.circle(screen,(200,200,255),(int(knob_x),self.rect.y+4),8)

        text=font.render(f"{self.label}: {self.value:.4f}",True,(220,220,220))
        screen.blit(text,(self.rect.x,self.rect.y-22))

    def update(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging=True

        if event.type==pygame.MOUSEBUTTONUP:
            self.dragging=False

        if event.type==pygame.MOUSEMOTION and self.dragging:
            x=max(self.rect.x,min(event.pos[0],self.rect.x+self.rect.w))
            ratio=(x-self.rect.x)/self.rect.w
            self.value=self.min+ratio*(self.max-self.min)


class Button:
    def __init__(self,x,y,w,h,text):
        self.rect=pygame.Rect(x,y,w,h)
        self.text=text

    def draw(self):
        pygame.draw.rect(screen,(70,70,90),self.rect,border_radius=6)
        txt=font.render(self.text,True,(255,255,255))
        screen.blit(txt,(self.rect.centerx-txt.get_width()//2,
                         self.rect.centery-txt.get_height()//2))

    def clicked(self,event):
        return event.type==pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)


sliders=[
Slider(40,120,200,0.01,1.0,base_fire_spread,"Распространение"),
Slider(40,190,200,0.0,0.9,humidity,"Влажность"),
Slider(40,260,200,0.0,0.01,tree_growth,"Рост леса"),
Slider(40,330,200,0.0,0.001,lightning_prob,"Молния"),
Slider(40,400,200,10,120,fps,"Скорость")
]

buttons=[
Button(40,470,200,40,"Пауза / Старт"),
Button(40,520,200,40,"Перезапуск"),
Button(40,570,200,40,"Поджечь"),
Button(40,620,200,40,"Добавить воду")
]

wind_buttons=[
Button(120,700,60,30,"↑"),
Button(120,760,60,30,"↓"),
Button(60,730,60,30,"←"),
Button(180,730,60,30,"→"),
Button(120,730,60,30,"•")
]


def update_simulation():

    global grid,burn_grid

    new_grid=grid.copy()
    new_burn=burn_grid.copy()

    wind_strength=0.8

    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):

            state=grid[x,y]

            if state==FIRE:

                new_burn[x,y]+=1

                if new_burn[x,y]>=burn_time:
                    new_grid[x,y]=ASH
                    new_burn[x,y]=0


            elif state==ASH:

                if random.random()<ash_decay:
                    new_grid[x,y]=EMPTY


            elif state==EMPTY:

                if random.random()<tree_growth:
                    new_grid[x,y]=TREE


            elif state==TREE:

                if random.random()<lightning_prob:
                    new_grid[x,y]=FIRE
                    new_burn[x,y]=1
                    continue

                catch_fire=False

                for dx in [-1,0,1]:
                    for dy in [-1,0,1]:

                        if dx==0 and dy==0:
                            continue

                        nx=x+dx
                        ny=y+dy

                        if 0<=nx<GRID_SIZE and 0<=ny<GRID_SIZE:

                            if grid[nx,ny]==FIRE:

                                prob=base_fire_spread

                                if abs(dx)+abs(dy)==2:
                                    prob*=0.7

                                dir_x=-dx
                                dir_y=-dy

                                if wind!=(0,0):

                                    wind_len=(wind[0]**2+wind[1]**2)**0.5
                                    wind_x=wind[0]/wind_len
                                    wind_y=wind[1]/wind_len

                                    dir_len=(dir_x**2+dir_y**2)**0.5
                                    dir_x/=dir_len
                                    dir_y/=dir_len

                                    dot=wind_x*dir_x+wind_y*dir_y

                                    prob+=dot*wind_strength

                                prob*=1-humidity

                                for wx in [-1,0,1]:
                                    for wy in [-1,0,1]:

                                        cx=x+wx
                                        cy=y+wy

                                        if 0<=cx<GRID_SIZE and 0<=cy<GRID_SIZE:

                                            if grid[cx,cy]==WATER:
                                                prob*=0.5

                                prob=max(0,min(1,prob))

                                if random.random()<prob:
                                    catch_fire=True
                                    break

                    if catch_fire:
                        break

                if catch_fire:
                    new_grid[x,y]=FIRE
                    new_burn[x,y]=1


    grid=new_grid
    burn_grid=new_burn


def draw_sim():

    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):

            rect=pygame.Rect(
                MENU_WIDTH+x*CELL_SIZE,
                y*CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )

            color=COLORS[grid[x,y]]

            if grid[x,y]==FIRE:
                color=(255,random.randint(80,150),0)

            pygame.draw.rect(screen,color,rect)


def draw_menu():

    pygame.draw.rect(screen,(30,30,45),(0,0,MENU_WIDTH,HEIGHT))

    title=big_font.render("🔥 FIRE CONTROL",True,(255,200,100))
    screen.blit(title,(40,40))

    for s in sliders:
        s.draw()

    for b in buttons:
        b.draw()

    for wb in wind_buttons:
        wb.draw()

    wind_text=font.render(f"Wind: {wind}",True,(200,200,255))
    screen.blit(wind_text,(90,670))


running=True

while running:

    clock.tick(int(fps))
    screen.fill((10,10,20))

    for event in pygame.event.get():

        if event.type==pygame.QUIT:
            running=False

        for s in sliders:
            s.update(event)

        if buttons[0].clicked(event):
            paused=not paused

        if buttons[1].clicked(event):

            grid=np.random.choice(
                [EMPTY,TREE],
                size=(GRID_SIZE,GRID_SIZE),
                p=[0.4,0.6]
            )

        if buttons[2].clicked(event):
            x=random.randint(0,GRID_SIZE-1)
            y=random.randint(0,GRID_SIZE-1)
            grid[x,y]=FIRE

        if buttons[3].clicked(event):
            x=random.randint(0,GRID_SIZE-1)
            y=random.randint(0,GRID_SIZE-1)
            grid[x,y]=WATER

        if wind_buttons[0].clicked(event):
            wind=(0,-1)

        elif wind_buttons[1].clicked(event):
            wind=(0,1)

        elif wind_buttons[2].clicked(event):
            wind=(-1,0)

        elif wind_buttons[3].clicked(event):
            wind=(1,0)

        elif wind_buttons[4].clicked(event):
            wind=(0,0)

    base_fire_spread=sliders[0].value
    humidity=sliders[1].value
    tree_growth=sliders[2].value
    lightning_prob=sliders[3].value
    fps=sliders[4].value

    if not paused:
        update_simulation()

    draw_sim()
    draw_menu()
    pygame.display.flip()

pygame.quit()
