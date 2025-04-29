# src/model/patrol_generator.py

import random
from collections import deque

class PatrolGenerator:
    """
    On init, takes everything needed to wire up your Enemy instances:
      - matrix, grid size, tile size
      - patrol area bounding box
      - list of Enemy objects
      - difficulty, base_marker, palette
    Then calls .setup_patrols() to do it all at once.
    """

    def __init__(self,
                 matrix: list[list[int]],
                 grid_cols: int,
                 grid_rows: int,
                 tile_size: tuple[float, float],
                 patrolling_area: tuple[float, float, float, float],
                 enemies: list,
                 difficulty_level: int,
                 base_marker: int,
                 palette: list[tuple[int,int,int,int]],
                 wall_code: int = 0,
                 floor_codes: tuple[int,...] = (1,2)
                ):
        # store all inputs
        self.matrix            = matrix
        self.GRID_COLS         = grid_cols
        self.GRID_ROWS         = grid_rows
        self.PIXEL_ONE_X, self.PIXEL_ONE_Y = tile_size
        self.patrolling_area   = patrolling_area
        self.enemies           = enemies
        self.difficulty_level  = difficulty_level
        self.base_marker       = base_marker
        self.palette           = palette
        self.WALL              = wall_code
        self.FLOORS            = set(floor_codes)

        # do all the work now
        self.setup_patrols()

    def setup_patrols(self):
        """Extract region, compute routes, assign to each Enemy."""
        region = self.extract_region()
        routes = self.generate_routes(region,
                                       len(self.enemies),
                                       self.difficulty_level)

        # assign each enemy its route, start‐pos, marker & color
        for i, (enemy, route) in enumerate(zip(self.enemies, routes)):
            enemy.complete_patrol_route = route
            if route:
                c, r = route[0]
                enemy.position = (c*self.PIXEL_ONE_X + self.PIXEL_ONE_X/2,
                                  r*self.PIXEL_ONE_Y + self.PIXEL_ONE_Y/2)
            enemy.route_marker = self.base_marker + i
            enemy.route_color  = self.palette[i % len(self.palette)]

    #region createment and 

    def extract_region(self):
        x0,y0,x1,y1 = self.patrolling_area
        c0 = int(x0 // self.PIXEL_ONE_X)
        r0 = int(y0 // self.PIXEL_ONE_Y)
        c1 = int(x1 // self.PIXEL_ONE_X)
        r1 = int(y1 // self.PIXEL_ONE_Y)

        region = set()
        for r in range(r0, r1):
            for c in range(c0, c1):
                if (0 <= c < self.GRID_COLS and 0 <= r < self.GRID_ROWS
                    and self.matrix[r][c] in self.FLOORS):
                    region.add((c, r))
        return region

    #main patrol logic

    def get_cell_neighbors(self, cell):
        c, r = cell
        for nc, nr in ((c+1,r),(c-1,r),(c,r+1),(c,r-1)):
            yield (nc, nr)

    def choose_starts(self, region, n):
        if not region or n<=0: return []
        region_list = list(region)
        chosen = [random.choice(region_list)]
        threshold = max(len(region_list)**0.5, 1)
        while len(chosen)<n and region_list:
            cand = random.choice(region_list)
            if all(abs(cand[0]-o[0]) + abs(cand[1]-o[1]) >= threshold for o in chosen)\
               or random.random()<0.3:
                chosen.append(cand)
            region_list.remove(cand)
        return chosen

    def partition(self, region, starts):
        parts = [set() for _ in starts]
        owner = {s:i for i,s in enumerate(starts)}
        q = deque((s,i) for i,s in enumerate(starts))
        while q:
            cell, idx = q.popleft()
            parts[idx].add(cell)
            for nb in self.get_cell_neighbors(cell):
                if nb in region and nb not in owner:
                    owner[nb]=idx
                    q.append((nb,idx))
        return parts

    def dfs_euler(self, start, region):
        visited, route = set(), []
        def dfs(c):
            visited.add(c)
            route.append(c)
            for nb in self.get_cell_neighbors(c):
                if nb in region and nb not in visited:
                    dfs(nb)
                    route.append(c)
        dfs(start)
        return route

    def optimize_route(self, route):
        if not route: return []
        out = [route[0]]
        for c in route[1:]:
            if c!=out[-1]: out.append(c)
        i=0
        while i+2<len(out):
            if out[i]==out[i+2]:
                del out[i+1]
            else:
                i+=1
        return out

    def find_bfs_path(self, start, goal, region):
        q = deque([start]); came={start:None}
        while q:
            cur = q.popleft()
            if cur==goal:
                path=[]
                while cur is not None:
                    path.append(cur)
                    cur=came[cur]
                return path[::-1]
            for nb in self.get_cell_neighbors(cur):
                if nb in region and nb not in came:
                    came[nb]=cur; q.append(nb)
        return []

    def get_deadends_together(self, routes, region):
        for i, rt in enumerate(routes):
            if not rt: continue
            last = rt[-1]
            if not any(nb in region and nb not in rt for nb in self.get_cell_neighbors(last)):
                for j, other in enumerate(routes):
                    if j==i or not other: continue
                    for cell in other:
                        if cell in self.get_cell_neighbors(last):
                            path = self.find_bfs_path(last, cell, region)
                            if len(path)>1:
                                rt.extend(path[1:])
                            break
                    else:
                        continue
                    break
        return routes

    def generate_routes(self, region, guard_count, diff_lvl):
        starts = self.choose_starts(region, guard_count)
        parts  = self.partition(region, starts)
        routes = []
        for i, start in enumerate(starts):
            part = parts[i]
            if not part:
                routes.append([])
                continue
            if start not in part:
                start = next(iter(part))
            r = self.dfs_euler(start, part)
            if diff_lvl >= 3:
                r = self.optimize_route(r)
            routes.append(r)
        return self.get_deadends_together(routes, region)
    