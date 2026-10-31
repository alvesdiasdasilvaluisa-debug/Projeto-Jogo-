# main.py — Plataforma 2D (versão final)
import sys, math, random, pygame

WIDTH, HEIGHT = 960, 540
FPS = 60
TILE = 40

SKY_TOP, SKY_BOTTOM = (110,180,255), (190,230,255)
HILL_FAR, HILL_NEAR = (120,170,210), (90,150,180)
CLOUD = (255,255,255)
DIRT, DIRT_DARK = (150,95,50), (120,70,35)
GRASS, GRASS_DARK = (90,200,90), (60,160,60)
COIN, COIN_DARK, COIN_SHINE = (255,215,0), (200,160,0), (255,255,200)
P_SKIN, P_SHIRT, P_PANTS, P_HAIR, P_EYE = (255,220,180),(220,50,50),(40,60,140),(80,40,20),(30,30,30)
E_BODY, E_BODY2, E_EYE, E_PUPIL, E_FEET = (80,80,220),(200,60,160),(255,255,255),(30,30,30),(50,50,50)
GOAL_POLE, GOAL_FLAG, GOAL_FLAG_D = (80,80,80),(60,220,100),(30,160,60)

GRAVITY, JUMP_FORCE, MOVE_SPEED, MAX_FALL = 0.8, -15, 5, 18
PLAYER_W, PLAYER_H = 32, 48
PLAYER_LIVES = 3
SCORE_COIN, SCORE_STOMP, SCORE_GOAL, BONUS_PER_LIFE = 10, 50, 100, 25


class Cloud:
    def __init__(self, x, y, s, sp):
        self.x, self.y, self.s, self.sp = x, y, s, sp
    def update(self, ww):
        self.x += self.sp
        if self.x - 200*self.s > ww: self.x = -200*self.s
    def draw(self, surf, cam):
        px = self.x - cam.rect.x*0.4
        py = self.y - cam.rect.y*0.2
        s = self.s
        for dx, dy, r in [(0,0,30),(35,5,25),(-35,5,25),(15,-15,22),(-15,-12,20)]:
            pygame.draw.circle(surf, CLOUD, (int(px+dx*s), int(py+dy*s)), int(r*s))


class Background:
    def __init__(self, ww):
        self.ww = ww
        self.clouds = [Cloud(random.randint(0,ww), random.randint(20,180),
                             random.uniform(0.6,1.4), random.uniform(0.1,0.4))
                       for _ in range(12)]
        self.hills = [(i, random.randint(60,130)) for i in range(0, ww+400, 120)]
    def update(self):
        for c in self.clouds: c.update(self.ww)
    def draw_sky(self, surf):
        for y in range(HEIGHT):
            t = y/HEIGHT
            c = tuple(int(SKY_TOP[i]*(1-t) + SKY_BOTTOM[i]*t) for i in range(3))
            pygame.draw.line(surf, c, (0,y), (WIDTH,y))
    def draw_sun(self, surf):
        pygame.draw.circle(surf, (255,240,150), (WIDTH-100,80), 45)
        pygame.draw.circle(surf, (255,255,200), (WIDTH-100,80), 30)
    def draw_hills(self, surf, cam):
        off = cam.rect.x*0.3
        for hx, hh in self.hills:
            px = hx - off
            if -300 < px < WIDTH+300:
                pygame.draw.polygon(surf, HILL_FAR,
                    [(px-140, HEIGHT-120), (px, HEIGHT-120-hh), (px+140, HEIGHT-120)])
        off2 = cam.rect.x*0.5
        for hx, hh in self.hills:
            px = hx - off2
            if -200 < px < WIDTH+200:
                pygame.draw.polygon(surf, HILL_NEAR,
                    [(px-100, HEIGHT-60), (px, HEIGHT-60-hh//2), (px+100, HEIGHT-60)])
    def draw_clouds(self, surf, cam):
        for c in self.clouds: c.draw(surf, cam)


def draw_tile(surf, cam, tile, has_above):
    r = cam.apply(tile)
    pygame.draw.rect(surf, DIRT, r)
    rnd = random.Random(tile.x*7919 + tile.y*104729)
    for _ in range(6):
        pygame.draw.circle(surf, DIRT_DARK,
            (r.x+rnd.randint(4,r.w-6), r.y+rnd.randint(4,r.h-6)), 2)
    if not has_above:
        pygame.draw.rect(surf, GRASS, (r.x, r.y, r.w, 8))
        pygame.draw.rect(surf, GRASS_DARK, (r.x, r.y+6, r.w, 3))
        for gx in range(r.x+4, r.x+r.w-4, 8):
            pygame.draw.line(surf, GRASS_DARK, (gx, r.y+2), (gx, r.y-4), 2)


class Particle:
    def __init__(self, x, y, color, life=30, speed=4):
        self.x, self.y, self.color = x, y, color
        self.life = self.max_life = life
        a = random.uniform(0, 6.283); m = random.uniform(1, speed)
        self.vx, self.vy = math.cos(a)*m, math.sin(a)*m
    def update(self):
        self.x += self.vx; self.y += self.vy; self.vy += 0.15; self.life -= 1
        return self.life > 0
    def draw(self, surf, cam):
        r = max(1, int(4*(self.life/self.max_life)))
        px, py = cam.apply_point(self.x, self.y)
        pygame.draw.circle(surf, self.color, (int(px), int(py)), r)


class ParticleSystem:
    def __init__(self): self.p = []
    def burst(self, x, y, color, n=10):
        for _ in range(n): self.p.append(Particle(x, y, color))
    def update(self): self.p = [p for p in self.p if p.update()]
    def draw(self, surf, cam):
        for p in self.p: p.draw(surf, cam)


class FloatingText:
    def __init__(self, x, y, text, color):
        self.x, self.y, self.text, self.color = x, y, text, color
        self.life = 60
        self.font = pygame.font.SysFont("arial", 22, bold=True)
    def update(self):
        self.y -= 1; self.life -= 1; return self.life > 0
    def draw(self, surf, cam):
        s = self.font.render(self.text, True, self.color)
        s.set_alpha(max(0, min(255, int(255*(self.life/60)))))
        px, py = cam.apply_point(self.x, self.y)
        surf.blit(s, (px, py))


class FloatingTextSystem:
    def __init__(self): self.items = []
    def spawn(self, x, y, t, c=(255,255,0)): self.items.append(FloatingText(x,y,t,c))
    def update(self): self.items = [i for i in self.items if i.update()]
    def draw(self, surf, cam):
        for i in self.items: i.draw(surf, cam)


class Camera:
    def __init__(self, w, h):
        self.rect = pygame.Rect(0, 0, w, h)
        self.shake_timer = self.shake_mag = 0
    def follow(self, target, ww, wh):
        self.rect.centerx = target.rect.centerx
        self.rect.centery = target.rect.centery
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > ww: self.rect.right = ww
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > wh: self.rect.bottom = wh
    def _off(self):
        if self.shake_timer > 0:
            ox = math.sin(self.shake_timer*1.7)*self.shake_mag
            oy = math.cos(self.shake_timer*2.3)*self.shake_mag
            self.shake_timer -= 1
            return ox, oy
        return 0, 0
    def apply(self, rect):
        ox, oy = self._off()
        return rect.move(-self.rect.x+ox, -self.rect.y+oy)
    def apply_point(self, x, y):
        ox, oy = self._off()
        return (x-self.rect.x+ox, y-self.rect.y+oy)
    def shake(self, f=12, m=6):
        self.shake_timer, self.shake_mag = f, m


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, PLAYER_W, PLAYER_H)
        self.vel_x = self.vel_y = 0
        self.on_ground = False
        self.facing = 1
        self.invulnerable = 0
        self.anim = 0
    def handle_input(self):
        k = pygame.key.get_pressed()
        self.vel_x = 0
        if k[pygame.K_LEFT] or k[pygame.K_a]:
            self.vel_x = -MOVE_SPEED; self.facing = -1
        if k[pygame.K_RIGHT] or k[pygame.K_d]:
            self.vel_x = MOVE_SPEED; self.facing = 1
        if (k[pygame.K_SPACE] or k[pygame.K_UP] or k[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_FORCE; self.on_ground = False
    def update(self, tiles):
        self.handle_input()
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL)
        self.rect.x += self.vel_x
        for t in tiles:
            if self.rect.colliderect(t):
                if self.vel_x > 0: self.rect.right = t.left
                elif self.vel_x < 0: self.rect.left = t.right
        self.rect.y += self.vel_y
        self.on_ground = False
        for t in tiles:
            if self.rect.colliderect(t):
                if self.vel_y > 0:
                    self.rect.bottom = t.top; self.vel_y = 0; self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = t.bottom; self.vel_y = 0
        if self.invulnerable > 0: self.invulnerable -= 1
        self.anim += 1
    def hit(self):
        if self.invulnerable > 0: return False
        self.invulnerable = 90; return True
    def respawn(self, x, y):
        self.rect.topleft = (x, y); self.vel_x = self.vel_y = 0
        self.invulnerable = 90
    def draw(self, surf, cam):
        if self.invulnerable > 0 and (self.invulnerable//5)%2 == 0: return
        r = cam.apply(self.rect)
        x, y, w = r.x, r.y, r.w
        hcx, hcy = x + w//2, y + 12
        pygame.draw.circle(surf, P_SKIN, (hcx, hcy), 11)
        pygame.draw.arc(surf, P_HAIR, (hcx-11, hcy-11, 22, 22),
                        math.pi*0.9, math.pi*2.1, 4)
        eo = 4*self.facing
        pygame.draw.circle(surf, P_EYE, (hcx-4+eo, hcy-1), 2)
        pygame.draw.circle(surf, P_EYE, (hcx+4+eo, hcy-1), 2)
        pygame.draw.arc(surf, P_EYE, (hcx-5, hcy+1, 10, 8),
                        math.pi*0.1, math.pi*0.9, 2)
        pygame.draw.rect(surf, P_SHIRT, (x+6, y+22, w-12, 16), border_radius=4)
        walk = math.sin(self.anim*0.3)*3 if self.vel_x != 0 and self.on_ground else 0
        pygame.draw.line(surf, P_SKIN, (x+6, y+25), (x+2, y+32+walk), 3)
        pygame.draw.line(surf, P_SKIN, (x+w-6, y+25), (x+w-2, y+32-walk), 3)
        lw = math.sin(self.anim*0.3)*4 if self.vel_x != 0 and self.on_ground else 0
        pygame.draw.rect(surf, P_PANTS, (x+8, y+36, 6, 12-abs(lw)//2))
        pygame.draw.rect(surf, P_PANTS, (x+w-14, y+36, 6, 12-abs(lw)//2))
        pygame.draw.rect(surf, (60,40,20), (x+7+int(lw), y+46, 8, 3))
        pygame.draw.rect(surf, (60,40,20), (x+w-15-int(lw), y+46, 8, 3))


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol=120, speed=2, color=E_BODY):
        super().__init__()
        self.rect = pygame.Rect(x, y, 34, 30)
        self.start_x = x; self.patrol = patrol; self.speed = speed
        self.direction = 1; self.vel_y = 0; self.color = color; self.anim = 0
    def update(self, tiles):
        self.rect.x += self.speed*self.direction
        if abs(self.rect.x - self.start_x) > self.patrol: self.direction *= -1
        for t in tiles:
            if self.rect.colliderect(t):
                if self.direction > 0: self.rect.right = t.left
                else: self.rect.left = t.right
                self.direction *= -1
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL)
        self.rect.y += self.vel_y
        for t in tiles:
            if self.rect.colliderect(t) and self.vel_y > 0:
                self.rect.bottom = t.top; self.vel_y = 0
        self.anim += 1
    def draw(self, surf, cam):
        r = cam.apply(self.rect)
        pygame.draw.rect(surf, self.color, r, border_radius=10)
        pygame.draw.polygon(surf, self.color,
            [(r.x+6,r.y),(r.x+10,r.y-6),(r.x+14,r.y)])
        pygame.draw.polygon(surf, self.color,
            [(r.right-14,r.y),(r.right-10,r.y-6),(r.right-6,r.y)])
        ey = r.y+12; e1 = r.x+10; e2 = r.right-10; po = self.direction*2
        pygame.draw.circle(surf, E_EYE, (e1,ey), 6)
        pygame.draw.circle(surf, E_EYE, (e2,ey), 6)
        pygame.draw.circle(surf, E_PUPIL, (e1+po,ey), 3)
        pygame.draw.circle(surf, E_PUPIL, (e2+po,ey), 3)
        pygame.draw.arc(surf, E_PUPIL, (r.centerx-6, r.y+19, 12, 8),
                        math.pi, math.pi*2, 2)
        wk = math.sin(self.anim*0.3)*2
        pygame.draw.ellipse(surf, E_FEET, (r.x+2, r.bottom-3+int(wk), 10, 5))
        pygame.draw.ellipse(surf, E_FEET, (r.right-12, r.bottom-3-int(wk), 10, 5))


class FastEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, patrol=200, speed=4, color=E_BODY2)


FASES = [
    [
        "                                              ",
        "                                              ",
        "                              C C C           ",
        "                                              ",
        "                    ###                       ",
        "                              ###      G      ",
        "        C C                                   ",
        "                 E                            ",
        "     P     ###        ###        C C C        ",
        "##############################################",
        "##############################################",
    ],
    [
        "                                                  ",
        "                              C C                 ",
        "                       ###            G           ",
        "                                                  ",
        "        C C                E                      ",
        "     ###      ###     ###      ###                ",
        "                                                  ",
        "   F              C C C           F               ",
        "  P     ###                ###          C C       ",
        "##################################################",
        "##################################################",
    ],
    [
        "                                                    ",
        "                                    C C C           ",
        "                            ###              G      ",
        "                                                    ",
        "        C     F            E                        ",
        "     ###   ###    ###   ###    ###    ###           ",
        "                                                    ",
        "  F          C C C          C C C          F        ",
        " P     ###              ###          ###            ",
        "####################################################",
        "####################################################",
    ],

    [
        "                                                      ",
        "                            C C C                     ",
        "                     ###           ###    G           ",
        "                                       ###               ",
        "        C C C                  E          ###               ",
        "     ###     ###       ###        ###                  ",
        "                                                      ",
        "   F              C C C C              C C C          ",
        "  P    ###                    ###             ###      ",
        "######################################################",
        "######################################################",
    ],
    # FASE 5 — Escadaria de plataformas
    [
        "                                                        ",
        "                                          C C C         ",
        "                                   ###          G       ",
        "                                              ###          ",
        "                          E              ###              ",
        "                   ###        ###                      ",
        "        C C C                                          ",
        "     ###      ###      F         C C C   C C C         ",
        "  P                 ###     ###             ###         ",
        "########################################################",
        "########################################################",
    ],
    # FASE 6 — Corredor com inimigos rápidos
    [
        "                                                          ",
        "              C C C                      C C C            ",
        "        ###         ###            ###         ###   G    ",
        "                                                          ",
        "   F        E             F            E        F         ",
        "  ###     ###    ###    ###     ###    ###     ###        ",
        "                                                          ",
        "     C C C     C C C      C C C      C C C     C C C      ",
        "  P        ###         ###        ###        ###          ",
        "##########################################################",
        "##########################################################",
    ],
    # FASE 7 — Plataformas flutuantes (sem chão contínuo no meio)
    [
        "                                                          ",
        "                   C C C           C C C                  ",
        "            ###            ###            ###      G      ",
        "                                                          ",
        "        C C          E                F          C C      ",
        "     ###    ###   ###   ###       ###   ###   ###         ",
        "                                                          ",
        "   F       C C C       C C C       C C C        E         ",
        "  P    ###         ###       ###        ###   ###         ",
        "##########################################################",
        "##########################################################",
    ],
    # FASE 8 — Final: desafio completo com tudo junto
    [
        "                                                            ",
        "                C C C              C C C        C C C       ",
        "         ###             ###              ###          G    ",
        "                                                            ",
        "    F        E     F          E       F         E     F     ",
        "  ###    ###    ###    ###   ###   ###    ###    ###        ",
        "                                                            ",
        "      C C C     C C C      C C C      C C C     C C C       ",
        "  P        ###        ###        ###        ###              ",
        "############################################################",
        "############################################################",
    ],
]

def total_fases(): return len(FASES)


def load_level(i):
    if i >= len(FASES): return None
    mapa = FASES[i]
    tiles, coins, enemies = [], [], []
    spawn = (TILE, TILE); goal = None; tset = set()
    for ry, row in enumerate(mapa):
        for cx, ch in enumerate(row):
            x, y = cx*TILE, ry*TILE
            if ch == "#":
                tiles.append(pygame.Rect(x, y, TILE, TILE)); tset.add((cx, ry))
            elif ch == "C":
                coins.append(pygame.Rect(x+TILE//4, y+TILE//4, TILE//2, TILE//2))
            elif ch == "E": enemies.append(("normal", x, y))
            elif ch == "F": enemies.append(("fast", x, y))
            elif ch == "P": spawn = (x, y)
            elif ch == "G": goal = pygame.Rect(x, y, TILE, TILE)
    ww = max(len(r) for r in mapa)*TILE
    wh = len(mapa)*TILE
    return tiles, coins, enemies, spawn, goal, ww, wh, tset


def draw_coin(surf, cam, coin, t):
    px, py = cam.apply_point(coin.centerx, coin.centery)
    w = int(coin.w*(0.6 + 0.4*abs(math.sin(t*0.15))))
    pygame.draw.ellipse(surf, (180,140,0), (px-w//2, py-coin.h//2, w, coin.h))
    pygame.draw.ellipse(surf, COIN, (px-w//2, py-coin.h//2+1, w, coin.h-2))
    if w > 8:
        pygame.draw.ellipse(surf, COIN_SHINE, (px-w//4, py-coin.h//3, w//3, coin.h//3))
    pygame.draw.ellipse(surf, COIN_DARK, (px-w//2, py-coin.h//2, w, coin.h), 2)


def draw_goal(surf, cam, goal, t):
    gr = cam.apply(goal)
    px = gr.x + gr.w//3
    pygame.draw.rect(surf, GOAL_POLE, (px, gr.y-40, 6, gr.h+40))
    pygame.draw.circle(surf, (255,220,50), (px+3, gr.y-42), 6)
    wave = math.sin(t*0.15)*4
    pygame.draw.polygon(surf, GOAL_FLAG,
        [(px+6, gr.y-40), (px+40+wave, gr.y-28), (px+6, gr.y-16)])
    pygame.draw.polygon(surf, GOAL_FLAG_D,
        [(px+6, gr.y-40), (px+40+wave, gr.y-28), (px+6, gr.y-16)], 2)


def run_level(screen, clock, fbig, fmed, fsmall, fase_idx):
    tiles, coins, esp, spawn, goal, ww, wh, tset = load_level(fase_idx)
    player = Player(*spawn)
    enemies = pygame.sprite.Group()
    for kind, ex, ey in esp:
        enemies.add(FastEnemy(ex, ey) if kind == "fast" else Enemy(ex, ey))
    cam = Camera(WIDTH, HEIGHT)
    bg = Background(ww)
    parts = ParticleSystem()
    texts = FloatingTextSystem()
    has_above = {(t.x//TILE, t.y//TILE): (t.x//TILE, t.y//TILE - 1) in tset for t in tiles}
    score = 0; lives = PLAYER_LIVES; start = spawn; tick = 0

    while True:
        clock.tick(FPS); tick += 1
        for e in pygame.event.get():
            if e.type == pygame.QUIT: return None
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: return None
        player.update(tiles)
        enemies.update(tiles)
        cam.follow(player, ww, wh)
        bg.update(); parts.update(); texts.update()

        if player.rect.top > wh + 200:
            lives -= 1; cam.shake(15, 8); player.respawn(*start)
            if lives <= 0: return {"status": "gameover", "score": score}

        for c in coins[:]:
            if player.rect.colliderect(c):
                coins.remove(c); score += SCORE_COIN
                parts.burst(c.centerx, c.centery, COIN, 8)
                texts.spawn(c.x, c.y-10, f"+{SCORE_COIN}", (255,240,100))

        for en in list(enemies):
            if player.rect.colliderect(en.rect):
                stomp = player.vel_y > 0 and player.rect.bottom - en.rect.top < 22
                if stomp:
                    enemies.remove(en)
                    parts.burst(en.rect.centerx, en.rect.centery, en.color, 14)
                    texts.spawn(en.rect.x, en.rect.y-10, f"+{SCORE_STOMP}", (120,200,255))
                    score += SCORE_STOMP
                    player.vel_y = JUMP_FORCE*0.7
                elif player.hit():
                    lives -= 1; cam.shake(15, 8)
                    parts.burst(player.rect.centerx, player.rect.centery, (255,60,60), 16)
                    if lives <= 0: return {"status": "gameover", "score": score}
                    player.respawn(*start)

        if goal and player.rect.colliderect(goal):
            score += SCORE_GOAL
            return {"status": "win", "score": score, "lives": lives}

        bg.draw_sky(screen); bg.draw_sun(screen)
        bg.draw_hills(screen, cam); bg.draw_clouds(screen, cam)

        for t in tiles:
            r = cam.apply(t)
            if r.right < -TILE or r.left > WIDTH+TILE: continue
            draw_tile(screen, cam, t, has_above.get((t.x//TILE, t.y//TILE), False))

        if goal: draw_goal(screen, cam, goal, tick)
        for c in coins: draw_coin(screen, cam, c, tick)
        for en in enemies: en.draw(screen, cam)
        player.draw(screen, cam)
        parts.draw(screen, cam)
        texts.draw(screen, cam)

        hs = f"Score: {score}   Vidas: {lives}"
        screen.blit(fmed.render(hs, True, (0,0,0)), (12,12))
        screen.blit(fmed.render(hs, True, (255,255,255)), (10,10))
        fs = f"Fase {total_fases()-fase_idx}/{total_fases()}"
        fw = fsmall.size(fs)[0]
        screen.blit(fsmall.render(fs, True, (0,0,0)), (WIDTH-fw-8, 12))
        screen.blit(fsmall.render(fs, True, (255,255,255)), (WIDTH-fw-10, 10))
        pygame.display.flip()


def screen_fase_ok(screen, clock, fbig, fmed, score_fase, lives):
    bonus = lives*BONUS_PER_LIFE
    final = score_fase + bonus
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: return None
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: return None
                if e.key in (pygame.K_RETURN, pygame.K_SPACE): return final
        screen.fill((20,20,40))
        t = fbig.render("FASE CONCLUÍDA!", True, (80,255,120))
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 120))
        for i, l in enumerate([
            f"Pontos da fase: {score_fase}",
            f"Bônus de vidas (x{BONUS_PER_LIFE}): +{bonus}",
            f"Total da fase: {final}",
        ]):
            s = fmed.render(l, True, (255,255,255))
            screen.blit(s, (WIDTH//2 - s.get_width()//2, 240 + i*45))
        if (pygame.time.get_ticks()//500)%2 == 0:
            s = fmed.render("Pressione ENTER para continuar", True, (200,200,200))
            screen.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT-100))
        pygame.display.flip()


def screen_game_over(screen, clock, fbig, fmed, score):
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: return "quit"
                if e.key == pygame.K_r: return "restart"
        screen.fill((40,0,0))
        t = fbig.render("GAME OVER", True, (255,80,80))
        screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 80))
        s = fmed.render(f"Pontuação final: {score}", True, (255,255,255))
        screen.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT//2))
        r = fmed.render("R = reiniciar   ESC = sair", True, (200,200,200))
        screen.blit(r, (WIDTH//2 - r.get_width()//2, HEIGHT//2 + 50))
        pygame.display.flip()


def screen_vitoria(screen, clock, fbig, fmed, score):
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: return "quit"
                if e.key == pygame.K_r: return "restart"
        screen.fill((0,40,0))
        t = fbig.render("VOCÊ ZEROU O JOGO!", True, (80,255,120))
        screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 100))
        s = fbig.render(f"{score}", True, (255,255,255))
        screen.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT//2 - 10))
        r = fmed.render("R = jogar de novo   ESC = sair", True, (200,200,200))
        screen.blit(r, (WIDTH//2 - r.get_width()//2, HEIGHT//2 + 80))
        pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Plataforma 2D — Pygame")
    clock = pygame.time.Clock()
    fbig = pygame.font.SysFont("arial", 48, bold=True)
    fmed = pygame.font.SysFont("arial", 28, bold=True)
    fsmall = pygame.font.SysFont("arial", 20, bold=True)

    score_total = 0
    fase = 0
    while True:
        if fase >= total_fases():
            acao = screen_vitoria(screen, clock, fbig, fmed, score_total)
            if acao == "restart":
                score_total = 0; fase = 0; continue
            break
        res = run_level(screen, clock, fbig, fmed, fsmall, fase)
        if res is None: break
        if res["status"] == "gameover":
            score_total += res["score"]
            if screen_game_over(screen, clock, fbig, fmed, score_total) == "restart":
                score_total = 0; fase = 0; continue
            break
        # fase concluída
        score_total += res["score"]
        novo = screen_fase_ok(screen, clock, fbig, fmed, res["score"], res["lives"])
        if novo is None: break
        score_total = score_total - res["score"] + novo
        fase += 1

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()