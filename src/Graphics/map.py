import pygame
from .screen import SIZE_X, SIZE_Y

class MapRenderer:
    """
    Responsible solely for drawing a precomputed maze, its items, players, and enemies,
    with overlay support. All map data and assets are injected as parameters.
    """
    def __init__(
        self,
        border_tuples,
        matrix: list[list[int]],
        grid_size: tuple[int, int],
        tile_size: tuple[float, float],
        crate_img: pygame.Surface,
        hidden_img: pygame.Surface,
        key_img: pygame.Surface,
        door_img: pygame.Surface,
        door_open_img: pygame.Surface,
        enemies: list,
        player,  # player instance
        screen,  # external screen
        overlay: bool = True
    ):
        self.screen = screen
        self.border_tuples = border_tuples
        self.matrix = matrix
        self.GRID_ROWS, self.GRID_COLS = grid_size
        self.PIXEL_ONE_X, self.PIXEL_ONE_Y = tile_size
        self.crate_img = crate_img
        self.hidden_img = hidden_img
        self.key_img = key_img
        self.door_img = door_img
        self.door_open_img = door_open_img
        self.enemies = enemies
        self.player = player
        self.overlay = overlay

    def toggle_overlay(self):
        self.overlay = not self.overlay

    def draw_map(self):
        """Draw the full map: tiles, overlay, then player and enemies."""
        self.screen.fill((0, 0, 0))

        # Walls & hidden rooms
        for r, c, x, y, w, h in self.border_tuples:
            val = self.matrix[r][c]
            if val == 0:
                img = self.crate_img
            elif val == 3:
                img = self.hidden_img
            else:
                continue
            self.screen.blit(pygame.transform.scale(img, (int(w), int(h))), (int(x), int(y)))

        # Key & doors
        for r in range(self.GRID_ROWS):
            for c in range(self.GRID_COLS):
                val = self.matrix[r][c]
                if val == 4:
                    img = self.key_img
                elif val == 5:
                    img = self.door_img
                elif val == 6:
                    img = self.door_open_img
                else:
                    continue
                px = c * self.PIXEL_ONE_X
                py = r * self.PIXEL_ONE_Y
                self.screen.blit(img, (int(px), int(py)))

        # Patrol overlay
        if self.overlay:
            colmap = {e.route_marker: e.route_color for e in self.enemies}
            for r in range(self.GRID_ROWS):
                for c in range(self.GRID_COLS):
                    mark = self.matrix[r][c]
                    if mark in colmap:
                        rect = pygame.Rect(
                            c * self.PIXEL_ONE_X,
                            r * self.PIXEL_ONE_Y,
                            self.PIXEL_ONE_X,
                            self.PIXEL_ONE_Y
                        )
                        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                        s.fill(colmap[mark])
                        self.screen.blit(s, rect.topleft)

        # Draw player & enemies on top
        self._draw_player()
        self._draw_enemies()

        # Update display
        pygame.display.flip()

    def _draw_player(self):
        """Draws the player sprite at its current position."""
        px, py = self.player.get_position()
        # Draw at top-left to match collision
        img = self.player.current_image
        self.screen.blit(img, (px, py))

    def _draw_enemies(self):
        for en in self.enemies:
            ex, ey = en.get_position()
            img = en.current_image
            w, h = img.get_width(), img.get_height()
            self.screen.blit(img, (ex - w/2, ey - h/2))