from typing import Any
import pygame as pg
import sys, os

pg.init()

screen = pg.display.set_mode((800, 600))
GRAVITY = 0.8
screen_rect = screen.get_rect()
fps = 60
clock = pg.time.Clock()

tiles = pg.sprite.Group()
traps = pg.sprite.Group()
trophy = pg.sprite.GroupSingle()


class Character(pg.sprite.Sprite):
    def __init__(self, x, y, char, scale, speed, anim_delay):
        pg.sprite.Sprite.__init__(self)
        self.alive = True
        self.animation_list = []
        self.animation_types = ["idle", "run", "death"]
        for d in self.animation_types:
            num_of_frames = len(os.listdir(f"C:\\platformer\\materials\\{char}\\{d}"))
            temp_list = []
            for i in range(num_of_frames):
                img = pg.image.load(f"C:\\platformer\\materials\\{char}\\{d}\\{i}.png")
                img = pg.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
                temp_list.append(img)
            self.animation_list.append(temp_list)
        self.action = 0
        self.frame_index = 0
        self.update_time = pg.time.get_ticks()
        self.anim_delay = anim_delay
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed
        self.jump = False
        self.on_the_ground = False
        self.vel_y = 0
        self.flip = False

    def update_animation(self):
        
        if pg.time.get_ticks() - self.update_time > self.anim_delay:
            self.update_time = pg.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pg.time.get_ticks()

    def update(self):
        self.update_animation()

    def collide(self):
        if pg.sprite.spritecollide(self, traps, False, pg.sprite.collide_mask):
            self.alive = False

    def move_y(self):
        if self.alive and not level.win:
            if self.jump and self.on_the_ground:
                self.vel_y = -18
                self.jump = self.on_the_ground = False

        if not self.on_the_ground:
            self.vel_y += GRAVITY

        dy = self.vel_y

        for tile in tiles:
            if tile.rect.colliderect(self.rect.x, self.rect.y + dy, self.rect.w, self.rect.h):
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile.rect.bottom - self.rect.top
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile.rect.top - self.rect.bottom

        # отслеживание игрока на земле
        self.on_the_ground = False
        for tile in tiles:
            if tile.rect.colliderect(self.rect.x, self.rect.y + 1, self.rect.w, self.rect.h):
                self.on_the_ground = True
        self.rect.y += int(dy)

    def draw(self):
        screen.blit(pg.transform.flip(self.image, self.flip, False), self.rect)
        pg.draw.rect(screen, (255, 0, 0), self.rect, 1)


class Player(Character):
    def __init__(self, x, y, scale, speed, anim_delay):
        Character.__init__(self, x, y, 'player', scale, speed, anim_delay)

    def move_x(self, ml, mr):
        dx = 0

        if mr:
            dx = self.speed
        elif ml:
            dx = -self.speed
        if self.flip and dx > 0:
            self.flip = False
        if not self.flip and dx < 0:
            self.flip = True
        for tile in tiles:
            if tile.rect.colliderect(self.rect.x + dx, self.rect.y, self.rect.w, self.rect.h):
                if dx > 0:
                    dx = tile.rect.left - self.rect.right
                elif dx < 0:
                    dx = tile.rect.right - self.rect.left

        self.rect.x += dx


class Enemy(Character):
    def __init__(self, x, y, scale, speed, anim_delay):
        Character.__init__(self, x, y, "player", scale, speed, anim_delay)
        self.idling = False
        self.move_counter = 0
        self.idle_counter = 0
        self.direction = 1
        self.gap_detector = pg.Rect(self.rect.right, self.rect.top, 5, 300)

    def ai(self):
        # устанавливаем смещение относительно направления
        if self.direction > 0:
            dx = self.speed
            self.flip = False
        else:
            dx = -self.speed
            self.flip = True

        # проверка, стоит персонаж или идет
        if not self.idling:
            self.update_action(1)
            if self.move_counter > 50:
                self.move_counter *= -1
                self.idling = True
            else:
                self.move_counter += 1
        else:
            self.update_action(0)
            dx = 0
            if self.idle_counter < 120:
                self.idle_counter += 1
            else:
                self.idle_counter = 0
                self.idling = False
                self.direction *= -1

        # проверка вертикальных столкновений
        for tile in tiles:
            if tile.rect.colliderect(self.rect.x + dx, self.rect.y, self.rect.w, self.rect.h):
                if dx > 0:
                    dx = tile.rect.left - self.rect.right
                elif dx < 0:
                    dx = tile.rect.right - self.rect.left

        # применение сформированного значения перемещения врага
        self.rect.x += dx

        # перемещение gap_detector относительно врага
        if self.direction > 0:
            self.gap_detector.topleft = self.rect.topright
        else:
            self.gap_detector.topright = self.rect.topleft

        # определение столкновения gap_detector с землей: если есть - идем, нет - стоим
        detect_floor = False
        for tile in tiles:
            if tile.rect.colliderect(self.gap_detector):
                detect_floor = True
                break
        if not detect_floor:
            if not self.idling:
                self.idling = True

    def draw(self):
        screen.blit(pg.transform.flip(self.image, self.flip, False), self.rect)
        pg.draw.rect(screen, (255, 0, 0), self.rect, 1)
        pg.draw.rect(screen, (0, 0, 0), self.gap_detector)


class Trap(pg.sprite.Sprite):
    def __init__(self, x, y):
        pg.sprite.Sprite.__init__(self)
        self.animation_list = []
        num_of_frames = len(os.listdir(f"C:\\platformer\\materials\\traps\\saw"))
        for i in range(num_of_frames):
            img = pg.image.load(f"C:\\platformer\\materials\\traps\\saw\\{i}.png")
            img = pg.transform.scale(img, (50, 50))
            self.animation_list.append(img)
        self.frame_index = 0
        self.image = self.animation_list[self.frame_index]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.update_time = pg.time.get_ticks()

    def update(self):
        anim_delay = 50
        if pg.time.get_ticks() - self.update_time > anim_delay:
            self.update_time = pg.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list):
            self.frame_index = 0
        self.image = self.animation_list[self.frame_index]
        print(self.frame_index)


class Tile(pg.sprite.Sprite):
    def __init__(self, x, y, img_path):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.transform.scale(pg.image.load(img_path), (50, 50))
        self.rect = self.image.get_rect(topleft=(x, y))


class Level:
    def __init__(self):
        self.win = False
        self.level = ["xxxxxxxxxxxxxxxx",
                      "x              x",
                      "x              x",
                      "xw      x      x",
                      "xxxt           x",
                      "x          x   x",
                      "x    xxx      xx",
                      "x              x",
                      "x              x",
                      "x p      e  xx x",
                      "x              x",
                      "xxxxxxxxxx xxxxx",]

    def create(self):
        x = 0
        y = 0
        for row in self.level:
            for col in row:
                if col == "x":
                    t = Tile(x, y, "C:\\platformer\\materials\\tile.png")
                    tiles.add(t)
                elif col == "t":
                    t = Trap(x, y)
                    traps.add(t)
                elif col == "p":
                    p = Player(x, y, 0.23, 4, 130)
                elif col == "w":
                    t = Tile(x, y, "C:\\platformer\\materials\\trophy.png")
                    trophy.add(t)
                elif col == "e":
                    e = Enemy(x, y, 0.23, 1, 130)
                    enemies.append(e)
                x += 50
            x = 0
            y += 50
        return p


enemies = []
level = Level()
player = level.create()
moving_left = False
moving_right = False

font = pg.font.SysFont("impact", 56)
mess1 = font.render("WIN", True, (0, 0, 0))
mess2 = font.render("FAIL", True, (0, 0, 0))
print(pg.font.get_fonts())


while True:

    for event in pg.event.get():
        if event.type == pg.QUIT:
            sys.exit()
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RIGHT:
                moving_right = True
            elif event.key == pg.K_LEFT:
                moving_left = True
            elif event.key == pg.K_UP:
                player.jump = True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_RIGHT:
                moving_right = False
            elif event.key == pg.K_LEFT:
                moving_left = False

    if player.alive and not level.win:
        if moving_left or moving_right:
            player.update_action(1)
        else:
            player.update_action(0)
        player.move_x(moving_left, moving_right)

    screen.fill((139, 0, 0))

    tiles.update()
    tiles.draw(screen)

    traps.update()
    traps.draw(screen)

    player.move_y()
    player.collide()
    player.update_animation()
    player.draw()

    for enemy in enemies:
        enemy.move_y()
        enemy.ai()
        enemy.update()
        enemy.draw()

    if pg.sprite.spritecollide(player, trophy, True, pg.sprite.collide_mask):
        level.win = True
    trophy.draw(screen)

    if not player.alive:
        player.update_action(2)
        screen.blit(mess2, (380, 280))

    if level.win:
        player.update_action(0)
        screen.blit(mess1, (380, 280))

    pg.display.flip()
    clock.tick(fps)
