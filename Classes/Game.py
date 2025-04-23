import os
import random
from collections import deque
import pygame
import time

from matrix_sizes import (
    SIZE_X, SIZE_Y,
    border_tuples,
    player_start_x, player_start_y,
    matrix,
    GRID_COLS, GRID_ROWS,
    PIXEL_ONE_X, PIXEL_ONE_Y,
    enemy_count, maze_difficulty,
    T_WALL, T_FLOOR, T_HIDDEN, T_KEY, T_DOOR_C, T_DOOR_O
)

from Player import Player
from Enemy import Enemy

def get_neighbors(cell):
    col, row = cell
    return [(col+1, row), (col, row+1), (col-1, row), (col, row-1)]

def get_region(patrolling_area):
    x_min, y_min, x_max, y_max = patrolling_area
    col_min = int(x_min // PIXEL_ONE_X)
    row_min = int(y_min // PIXEL_ONE_Y)
    col_max = int(x_max // PIXEL_ONE_X)
    row_max = int(y_max // PIXEL_ONE_Y)
    region = set()
    for row in range(row_min, row_max):
        for col in range(col_min, col_max):
            if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
                if matrix[row][col] in (1, 2):
                    region.add((col, row))
    return region

def choose_starting_points(region, guard_count):
    region_list = list(region)
    if not region_list:
        return []
    chosen = [random.choice(region_list)]
    threshold = max(GRID_COLS, GRID_ROWS) // 4
    while len(chosen) < guard_count and region_list:
        c = random.choice(region_list)
        if all(abs(c[0]-p[0]) + abs(c[1]-p[1]) >= threshold for p in chosen):
            chosen.append(c)
        elif random.random() < .3:
            chosen.append(c)
        region_list.remove(c)
    return chosen

def partition_region_among_guards(region, starts):
    g = len(starts)
    parts = [set() for _ in range(g)]
    frontier, owner = deque(), {}
    for i, s in enumerate(starts):
        frontier.append((s, i))
        owner[s] = i
    while frontier:
        cur, idx = frontier.popleft()
        parts[idx].add(cur)
        for nb in get_neighbors(cur):
            if nb in region and nb not in owner:
                owner[nb] = idx
                frontier.append((nb, idx))
    for i in range(g):
        if not parts[i]:
            parts[i] = set(region)
    return parts

def dfs_euler(start, region):
    route, vis = [], set()
    def dfs(v):
        vis.add(v)
        route.append(v)
        for nb in get_neighbors(v):
            if nb in region and nb not in vis:
                dfs(nb)
                route.append(v)
    dfs(start)
    return route

def optimize_patrol_route(route):
    if not route:
        return route
    out = []
    for c in route:
        if not out or out[-1] != c:
            out.append(c)
    i = 0
    while i < len(out) - 2:
        if out[i] == out[i+2]:
            del out[i+1]
        else:
            i += 1
    return out

def bfs_path(s, t, region):
    q, came = deque([s]), {s: None}
    while q:
        v = q.popleft()
        if v == t:
            path = []
            while v is not None:
                path.append(v)
                v = came[v]
            return path[::-1]
        for nb in get_neighbors(v):
            if nb in region and nb not in came:
                came[nb] = v
                q.append(nb)
    return []

def join_dead_end_routes(routes, region):
    for i, rt in enumerate(routes):
        if not rt:
            continue
        last = rt[-1]
        if any(nb in region and nb not in rt for nb in get_neighbors(last)):
            continue
        for j, other in enumerate(routes):
            if i == j or not other:
                continue
            for cell in other:
                if cell in get_neighbors(last):
                    path = bfs_path(last, cell, region)
                    if path and len(path) > 1:
                        rt.extend(path[1:])
                        break
            else:
                continue
            break
    return routes

def generate_guard_patrol_routes(region, n, diff):
    starts = choose_starting_points(region, n)
    parts  = partition_region_among_guards(region, starts)
    routes = []
    for i in range(n):
        start = starts[i] if starts[i] in parts[i] else next(iter(parts[i]))
        r = dfs_euler(start, parts[i])
        if diff >= 3:
            r = optimize_patrol_route(r)
        routes.append(r)
    return join_dead_end_routes(routes, region)
# ──────────────────────────────────────────────────────────────────

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Stealth Game – Dynamic Guard Patrols")
        self.screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
        self.clock  = pygame.time.Clock()

        # fonts & assets
        self.font_small = pygame.font.SysFont(None, 24)
        self.font_big   = pygame.font.SysFont(None, 48)
        asset = lambda f: os.path.join("../Assets", f)

        # backgrounds
        self.bg_main  = pygame.transform.scale(
            pygame.image.load(asset("Opening_screen.jpg")).convert(),
            (SIZE_X, SIZE_Y)
        )
        self.bg_level = pygame.image.load(asset("background.jpg")).convert()

        # base tiles
        self.crate_img  = pygame.image.load(asset("walls.png")).convert_alpha()
        self.hidden_img = pygame.image.load(asset("hidden_room.png")).convert_alpha()

        # key & door
        self.key_img = pygame.transform.scale(
            pygame.image.load(asset("key.png")).convert_alpha(),
            (int(PIXEL_ONE_X)/2, int(PIXEL_ONE_Y)/2)
        )
        self.door_img = pygame.transform.scale(
            pygame.image.load(asset("Door_closed.png")).convert_alpha(),
            (int(PIXEL_ONE_X), int(PIXEL_ONE_Y))
        )
        self.door_open = pygame.transform.scale(
            pygame.image.load(asset("Door_open.png")).convert_alpha(),
            (int(PIXEL_ONE_X), int(PIXEL_ONE_Y))
        )

        # locate key & door in the matrix
        self.key_pos = next(
            ((r, c) for r in range(GRID_ROWS) for c in range(GRID_COLS)
             if matrix[r][c] == T_KEY),
            None
        )
        self.door_pos = next(
            ((r, c) for r in range(GRID_ROWS) for c in range(GRID_COLS)
             if matrix[r][c] == T_DOOR_C),
            None
        )

        # player & guards
        self.player      = Player(player_start_x, player_start_y)
        self.difficulty  = 1 if maze_difficulty == "easy" else 3
        self.guard_count = enemy_count
        self.enemies     = []
        self.overlay     = True
        self.paused      = False
        self.help_on     = False
        self.patrolling_area = (0, 0, SIZE_X, SIZE_Y)

    # ── MAIN MENU ─────────────────────────────────────────
    def show_main_menu(self):
        choice, labels = 0, ("NEW GAME", "QUIT")
        while True:
            self.screen.blit(self.bg_main, (0, 0))
            for i, lbl in enumerate(labels):
                col = (255,255,0) if i==choice else (255,255,255)
                txt = self.font_big.render(lbl, True, col)
                self.screen.blit(txt, txt.get_rect(
                    center=(SIZE_X//2, SIZE_Y//2 + i*60)))
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); exit()
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_UP, pygame.K_w):
                        choice = (choice-1) % 2
                    if e.key in (pygame.K_DOWN, pygame.K_s):
                        choice = (choice+1) % 2
                    if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if choice == 0:
                            return
                        pygame.quit(); exit()

    # ── PAUSE OVERLAY ────────────────────────────────────
    def draw_paused(self):
        veil = pygame.Surface((SIZE_X, SIZE_Y), pygame.SRCALPHA)
        veil.fill((0,0,0,180))
        self.screen.blit(veil, (0,0))
        txt = self.font_big.render("PAUSED", True, (255,255,255))
        self.screen.blit(txt, txt.get_rect(center=(SIZE_X//2, SIZE_Y//2)))

    # ── HELP OVERLAY ─────────────────────────────────────
    def draw_help(self):
        lines = [
            "Controls:",
            "  P … pause / resume",
            "  K … toggle patrol overlay",
            "  H … help",
            "  WASD … move",
            "  Esc … quit"
        ]
        pad = 8
        w = max(self.font_small.size(l)[0] for l in lines) + pad*2
        h = (self.font_small.get_height()+pad)*len(lines) + pad
        surf = pygame.Surface((w,h), pygame.SRCALPHA)
        surf.fill((0,0,0,180))
        for i,l in enumerate(lines):
            txt = self.font_small.render(l, True, (255,255,255))
            surf.blit(txt, (pad, pad + i*(self.font_small.get_height()+pad)))
        self.screen.blit(surf, ((SIZE_X-w)//2, (SIZE_Y-h)//2))

    # ── DRAW MAP ─────────────────────────────────────────
    def draw_map(self):
        # walls & hidden
        for (r, c, x, y, w, h) in border_tuples:
            val = matrix[r][c]
            if val == T_WALL:
                img = self.crate_img
            elif val == T_HIDDEN:
                img = self.hidden_img
            else:
                img = None
            if img:
                self.screen.blit(pygame.transform.scale(img, (int(w),int(h))),
                                 (int(x),int(y)))

        # key & door
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                val = matrix[r][c]
                if val == T_KEY:
                    img = self.key_img
                elif val == T_DOOR_C:
                    img = self.door_img
                elif val == T_DOOR_O:
                    img = self.door_open
                else:
                    continue
                px, py = c*PIXEL_ONE_X, r*PIXEL_ONE_Y
                self.screen.blit(img, (int(px), int(py)))

        # patrol overlay
        if self.overlay:
            col_by_marker = {e.route_marker: e.route_color for e in self.enemies}
            for rr in range(GRID_ROWS):
                for cc in range(GRID_COLS):
                    mark = matrix[rr][cc]
                    # only overlay on markers above door codes
                    if mark >= T_DOOR_O + 1:
                        col = col_by_marker.get(mark, (0,0,0,128))
                        s = pygame.Surface((int(PIXEL_ONE_X),int(PIXEL_ONE_Y)), pygame.SRCALPHA)
                        s.fill(col)
                        self.screen.blit(s, (cc*PIXEL_ONE_X, rr*PIXEL_ONE_Y))

    # ── ENEMY SETUP ───────────────────────────────────────
    def level_changes(self):
        region = get_region(self.patrolling_area)
        routes = generate_guard_patrol_routes(region, self.guard_count, self.difficulty)
        palette = [
            (0,0,255,128),(255,0,0,128),(0,255,0,128),
            (255,255,0,128),(255,0,255,128),(0,255,255,128)
        ]
        for i, rt in enumerate(routes):
            if not rt:
                continue
            sx = rt[0][0]*PIXEL_ONE_X + PIXEL_ONE_X/2
            sy = rt[0][1]*PIXEL_ONE_Y + PIXEL_ONE_Y/2
            en = Enemy((sx, sy), rt, move_speed=3, update_interval=1)
            # shift markers past the door codes
            en.route_marker = T_DOOR_O + 1 + i
            en.route_color  = palette[i % len(palette)]
            self.enemies.append(en)

    # ── MAIN LOOP ─────────────────────────────────────────
    def game_loop(self):
        self.show_main_menu()
        self.options_screen()
        self.level_changes()

        running = True
        while running:
            if self.player.get_win():
                veil = pygame.Surface((SIZE_X, SIZE_Y), pygame.SRCALPHA)
                veil.fill((0,0,0,180))
                self.screen.blit(veil, (0,0))
                txt = self.font_big.render("YOU WON", True, (255,255,255))
                self.screen.blit(txt, txt.get_rect(center=(SIZE_X//2, SIZE_Y//2)))
                pygame.display.flip()
                time.sleep(3)
                return

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        running = False
                    elif e.key == pygame.K_p:
                        self.paused = not self.paused
                    elif e.key == pygame.K_k and not self.paused:
                        self.overlay = not self.overlay
                    elif e.key == pygame.K_h:
                        self.help_on = not self.help_on
                        self.paused  = self.help_on or self.paused

            if not self.paused:
                self.screen.blit(self.bg_level, (0,0))
                self.draw_map()

                # move player
                self.player.move()
                px, py = self.player.get_position()
                col, row = int(px//PIXEL_ONE_X), int(py//PIXEL_ONE_Y)

                # pick up key
                if not self.player.has_key and matrix[row][col] == T_KEY:
                    self.player.has_key = True
                    matrix[row][col] = T_FLOOR

                # open door when adjacent
                if self.player.has_key and self.door_pos is not None:
                    dr, dc = self.door_pos
                    if self.player.near_door((dr, dc)):
                        matrix[dr][dc] = T_DOOR_O

                # update & draw enemies
                ppx = self.player.get_position()
                for en in self.enemies:
                    en.update(ppx)

                self.player.draw(self.screen)
                for en in self.enemies:
                    en.draw(self.screen)
            else:
                self.draw_paused()

            if self.help_on:
                self.draw_help()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    # ── overlay‑toggle pre‑game screen ──────────────────────────
    def options_screen(self):
        font, show = pygame.font.SysFont(None,36), True
        while True:
            self.screen.fill((0,0,0))
            txts = [
                f"Show Enemy Patrol Overlay: {'ON' if show else 'OFF'} (K)",
                "Press ENTER to continue"
            ]
            for i,t in enumerate(txts):
                self.screen.blit(font.render(t,True,(255,255,255)),(50,50+i*40))
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_k:
                        show = not show
                    elif e.key == pygame.K_RETURN:
                        self.overlay = show
                        return

if __name__ == "__main__":
    Game().game_loop()
