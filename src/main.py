import pygame
from Graphics.main_graphics import MainGraphics
from Logic.logic_setup import LogicSetup
from Graphics.post_game_menu import PostGameMenu


def main():
    pygame.init()
    screen = pygame.display.set_mode((1000, 750))
    clock = pygame.time.Clock()

    gfx = MainGraphics()
    post_menu = PostGameMenu(screen, clock)
    app_running = True

    while app_running:
        # --- PRE-GAME MENU ---
        gfx.pre_game()  # show NEW GAME / DEV MODE / QUIT
        if gfx.menu_choice == 2:  # Quit
            break

        # Settings are now in gfx (difficulty, rows, cols, enemy_count)
        in_game = True
        while in_game and app_running:
            # --- SET UP A RUN/LEVEL ---
            logic = LogicSetup(
                gfx.maze_difficulty,
                gfx.rows,
                gfx.cols,
                gfx.enemy_count
            )
            logic.generate_game()

            # Inject into graphics
            bt, mat, grid_size, tile_size, key_pos, door_pos, player, enemies = \
                logic.get_graphics_attributes()
            gfx.in_game(bt, mat, grid_size, tile_size, player, enemies)

            # --- PLAY LOOP ---
            result = {'won': False, 'lost': False}
            while True:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        app_running = False
                        in_game = False
                        break
                if not app_running or not in_game:
                    break

                logic.handle_input(pygame.key.get_pressed())
                result = logic.update()

                gfx.map_renderer.draw_map()
                clock.tick(60)

                if result['won'] or result['lost']:
                    break

            if not app_running:
                break

            # --- POST-GAME MENU ---
            choice = post_menu.show(won=result['won'])
            if choice == 'next':
                # Next level: increment size or difficulty as desired
                gfx.rows += 1
                gfx.cols += 1
                continue  # stay in_game for next level

            if choice == 'exit':
                app_running = False
                in_game = False
            elif choice in ('new', 'menu'):
                # For both New Game and Main Menu, return to PRE-GAME
                in_game = False

        # loop back to PRE-GAME or exit

    pygame.quit()

if __name__ == '__main__':
    main()