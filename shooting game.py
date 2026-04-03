import pygame
import random
import math
import heapq
import os
import sys

# Initialize Pygame and Font module
pygame.init()
pygame.font.init()

# --- Level System Logic ---
LEVEL_FILE = "save_data.txt"


def load_level():
    if not os.path.exists(LEVEL_FILE):
        try:
            with open(LEVEL_FILE, "w") as f:
                f.write("level = 1\n")
        except Exception as e:
            print(f"Error creating {LEVEL_FILE}: {e}")
        return 1
    try:
        with open(LEVEL_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                if "level" in line and "=" in line:
                    level_str = line.split("=")[1].strip()
                    return int(level_str)
        return 1
    except Exception as e:
        print(f"Error reading {LEVEL_FILE}: {e}")
        return 1


def increment_level(current):
    new_level = min(current + 1, 31)
    try:
        with open(LEVEL_FILE, "w") as f:
            f.write(f"level = {new_level}\n")
    except Exception as e:
        print(f"Error updating {LEVEL_FILE}: {e}")
    return new_level


current_level = load_level()

# Setup the Pygame display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SCALED)
screen_rect = screen.get_rect()
pygame.display.set_caption("Light Caster: Abyssal Survivor")
clock = pygame.time.Clock()

# Fonts for UI
ui_font = pygame.font.SysFont(None, 32)
game_over_font = pygame.font.SysFont(None, 72)
win_font = pygame.font.SysFont(None, 72)
boss_hp_font = pygame.font.SysFont(None, 24)

font_large = pygame.font.SysFont(None, 72)
font_medium = pygame.font.SysFont(None, 48)
font_small = pygame.font.SysFont(None, 24)

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BLUE = (0, 0, 139)
GRAY = (128, 128, 128)

BG_COLOR = (245, 246, 227)
WALL_COLOR = (147, 161, 161)
TEXT_COLOR = (44, 62, 80)

PLAYER_COLOR = (41, 128, 185)
SHIELD_COLOR = (100, 200, 255)
HP_GREEN = (46, 204, 113)
HP_RED = (231, 76, 60)
ENERGY_YELLOW = (241, 196, 15)

# Bot Colors
C_RED = (255, 107, 107)
C_GREEN = (26, 188, 156)
C_PINK = (253, 121, 168)
C_PURPLE = (155, 89, 182)
C_ORANGE = (253, 150, 68)
C_DEMON = (44, 62, 80)
C_GHOST = (116, 185, 255)
C_BOSS = (192, 57, 43)

SPECIAL_STAGES = [
    {"color": (45, 52, 54), "hp": 9}, {"color": (99, 110, 114), "hp": 8},
    {"color": (108, 92, 231), "hp": 7}, {"color": (214, 48, 49), "hp": 6},
    {"color": (225, 112, 85), "hp": 5}, {"color": (9, 132, 227), "hp": 4},
    {"color": (250, 177, 160), "hp": 3}, {"color": (253, 203, 110), "hp": 2},
    {"color": (223, 230, 233), "hp": 1}
]


# --- Dynamic Wall Layouts ---
def get_walls_for_level(level):
    layout_type = level % 5
    if layout_type == 1:
        return [pygame.Rect(200, 150, 400, 40), pygame.Rect(200, 410, 400, 40), pygame.Rect(100, 260, 40, 80)]
    elif layout_type == 2:
        return [pygame.Rect(380, 60, 40, 140), pygame.Rect(380, 400, 40, 140), pygame.Rect(100, 280, 180, 40),
                pygame.Rect(520, 280, 180, 40)]
    elif layout_type == 3:
        return [pygame.Rect(150, 100, 100, 40), pygame.Rect(150, 100, 40, 100), pygame.Rect(550, 100, 100, 40),
                pygame.Rect(610, 100, 40, 100), pygame.Rect(150, 460, 100, 40), pygame.Rect(150, 400, 40, 100),
                pygame.Rect(550, 460, 100, 40), pygame.Rect(610, 400, 40, 100)]
    elif layout_type == 4:
        return [pygame.Rect(140, 160, 520, 40), pygame.Rect(140, 400, 520, 40)]
    else:
        return [pygame.Rect(260, 140, 40, 320), pygame.Rect(500, 140, 40, 320)]


walls = get_walls_for_level(current_level)

# Player Setup
player_size = 40
player_rect = pygame.Rect(WIDTH // 2, HEIGHT // 2, player_size, player_size)
player_float_x, player_float_y = float(player_rect.x), float(player_rect.y)
player_aim_x, player_aim_y = 1.0, 0.0

# Base Speeds
base_bot_speed_pps = 100
light_speed_pps = 900
fireball_speed_pps = 450
boss_speed_pps = 60

# HP, Ammo, Shield & Energy Setup
max_hp, player_hp = 20, 20
last_damage_time, damage_cooldown = 0, 1000
last_heal_time = 0

max_light, light_left = 30, 30
is_reloading, reload_end_time = False, 0
max_reloads, reloads_left = 5, 5

shield_active, shield_end_time = False, 0
max_energy, player_energy = 20, 20
sprint_time_accumulator = 0
last_energy_regen = 0

# Supreme Judgement Setup
last_judgement_time = -35000
judgement_cooldown = 35000
judgement_radius = 200  # Slightly smaller
show_judgement_blast = 0
pending_judgement_time = 0
judgement_delay = 0

# Projectile & Pickup Setup
player_lights, enemy_lights = [], []
light_size = 6
pickups, blue_dots = [], []
pickup_size = 12
last_pickup_spawn_time = last_pickup_decay_time = 0

# Bot Setup
bots = []
bot_size, ghost_size = 30, 20
last_spawn_time = 0
spawn_delay = random.randint(4000, 7500)
bot_kill_count = 0

# Demon & Boss Setup
blind_zones = []
last_demon_spawn_time = 0
demon_spawn_delay = random.randint(20000, 40000)
bosses, fireballs, boss_hazards = [], [], []
fireball_size = light_size * 3
last_ghost_spawn_time = 0
ghost_spawn_delay = random.randint(15000, 25000)

# Game State
game_state = "menu"
peaceful_mode = False
game_over, game_won = False, False
phase = "normal"
game_time = 0
last_real_time = pygame.time.get_ticks()
countdown_duration = 100000
game_start_time = 0
madness_start_time, madness_duration = 0, 20000
max_revives, revives_left = 2, 2
last_curse_spawn_time = 0

# UI Rects
desc_button_rect = pygame.Rect(0, 0, 0, 0)
peaceful_button_rect = pygame.Rect(0, 0, 0, 0)
start_button_rect = pygame.Rect(0, 0, 0, 0)
back_button_rect = pygame.Rect(20, 20, 120, 40)


# --- Drawing Shapes Function ---
def draw_shape(surface, shape_type, color, rect):
    cx, cy = rect.centerx, rect.centery
    w, h = rect.width, rect.height
    hw, hh = w // 2, h // 2

    if shape_type == "circle":
        pygame.draw.circle(surface, color, (cx, cy), hw)
    elif shape_type == "diamond":
        pygame.draw.polygon(surface, color, [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)])
    elif shape_type == "hexagon":
        pygame.draw.polygon(surface, color,
                            [(cx, cy - hh), (cx + hw, cy - hh // 2), (cx + hw, cy + hh // 2), (cx, cy + hh),
                             (cx - hw, cy + hh // 2), (cx - hw, cy - hh // 2)])
    elif shape_type == "cross":
        pygame.draw.rect(surface, color, (cx - hw, cy - hh // 3, w, h // 1.5))
        pygame.draw.rect(surface, color, (cx - hw // 3, cy - hh, w // 1.5, h))
    elif shape_type == "star":
        pts = []
        for i in range(10):
            angle = i * math.pi / 5 - math.pi / 2
            r = hw if i % 2 == 0 else hw // 2
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        pygame.draw.polygon(surface, color, pts)
    elif shape_type == "triangle":
        pygame.draw.polygon(surface, color, [(cx, cy - hh), (cx - hw, cy + hh), (cx + hw, cy + hh)])
    elif shape_type == "octagon":
        q = hw // 2
        pygame.draw.polygon(surface, color, [(cx - q, cy - hh), (cx + q, cy - hh), (cx + hw, cy - q), (cx + hw, cy + q),
                                             (cx + q, cy + hh), (cx - q, cy + hh), (cx - hw, cy + q),
                                             (cx - hw, cy - q)])
    else:
        pygame.draw.rect(surface, color, rect)
    if shape_type != "rect": pygame.draw.circle(surface, (0, 0, 0), (cx, cy), hw, 1)


# Pathfinding
def get_path(start_pos, target_pos, walls, grid_size=20):
    start = (start_pos[0] // grid_size, start_pos[1] // grid_size)
    target = (target_pos[0] // grid_size, target_pos[1] // grid_size)
    if start == target: return []
    queue_pf, came_from, cost_so_far = [], {start: None}, {start: 0}
    heapq.heappush(queue_pf, (0, start))

    while queue_pf:
        current = heapq.heappop(queue_pf)[1]
        if current == target: break
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            next_node = (current[0] + dx, current[1] + dy)
            if not (0 <= next_node[0] < WIDTH // grid_size and 0 <= next_node[1] < HEIGHT // grid_size): continue
            if pygame.Rect(next_node[0] * grid_size, next_node[1] * grid_size, grid_size, grid_size).collidelist(
                    walls) != -1: continue
            new_cost = cost_so_far[current] + 1
            if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                cost_so_far[next_node] = new_cost
                priority = new_cost + abs(target[0] - next_node[0]) + abs(target[1] - next_node[1])
                heapq.heappush(queue_pf, (priority, next_node))
                came_from[next_node] = current
    if target not in came_from: return []
    path, current = [], target
    while current != start:
        path.append((current[0] * grid_size + grid_size // 2, current[1] * grid_size + grid_size // 2))
        current = came_from[current]
    path.reverse()
    return path


def has_line_of_sight(pos1, pos2, walls):
    for wall in walls:
        if wall.clipline(pos1, pos2): return False
    return True


# --- Main Game Loop ---
running = True

while running:
    # 1. Delta Time (dt) Calculation
    real_current_time = pygame.time.get_ticks()
    real_delta_time = real_current_time - last_real_time
    last_real_time = real_current_time

    dt = min(real_delta_time / 1000.0, 0.1)

    if game_state == "playing":
        game_time += real_delta_time

    current_bot_speed_pps = base_bot_speed_pps * (1.3 if current_level >= 26 else 1.0)
    normal_bot_hp = 5 if current_level >= 26 else (
        4 if current_level >= 20 else (3 if current_level >= 13 else (2 if current_level >= 5 else 1)))
    normal_bot_damage = 1 + ((current_level - 1) // 8)
    spawn_mult = 2.0 if peaceful_mode else 1.0

    # 2. Global Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "menu":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if start_button_rect.collidepoint(mouse_pos):
                    game_state = "playing"
                    pygame.display.set_caption(f"Light Caster | Level {current_level}")
                    game_time = game_start_time = last_heal_time = last_pickup_spawn_time = last_pickup_decay_time = 0
                    last_spawn_time = last_demon_spawn_time = last_ghost_spawn_time = last_curse_spawn_time = 0
                    last_judgement_time = -35000
                    show_judgement_blast = 0
                    pending_judgement_time = 0
                    reloads_left = max_reloads
                    revives_left = max_revives
                    is_reloading = False
                if desc_button_rect.collidepoint(mouse_pos): game_state = "description"
                if peaceful_button_rect.collidepoint(mouse_pos): peaceful_mode = not peaceful_mode

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_state = "playing"
                pygame.display.set_caption(f"Light Caster | Level {current_level}")
                game_time = game_start_time = last_heal_time = last_pickup_spawn_time = last_pickup_decay_time = 0
                last_spawn_time = last_demon_spawn_time = last_ghost_spawn_time = last_curse_spawn_time = 0
                last_judgement_time = -35000
                show_judgement_blast = 0
                pending_judgement_time = 0
                reloads_left = max_reloads
                revives_left = max_revives
                is_reloading = False

        elif game_state == "description":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button_rect.collidepoint(pygame.mouse.get_pos()): game_state = "menu"

        elif game_state == "playing":
            is_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            is_space = event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE

            if not game_over and not game_won and (is_click or is_space) and not is_reloading:
                if phase == "madness" or light_left > 0:
                    if phase != "madness": light_left -= 1
                    b_dx_pps, b_dy_pps = player_aim_x * light_speed_pps, player_aim_y * light_speed_pps
                    bx = player_rect.centerx + (player_aim_x * (player_size // 2 + 5))
                    by = player_rect.centery + (player_aim_y * (player_size // 2 + 5))

                    player_lights.append({
                        "float_x": float(bx - light_size // 2),
                        "float_y": float(by - light_size // 2),
                        "rect": pygame.Rect(bx - light_size // 2, by - light_size // 2, light_size, light_size),
                        "dx": b_dx_pps, "dy": b_dy_pps
                    })

            # Player Interactions (Reload, Judgement, Revive)
            if not game_over and not game_won and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and light_left < max_light and not is_reloading and reloads_left > 0:
                    is_reloading = True
                    reload_end_time = game_time + 2500  # Reload time increased to 2.5s
                    reloads_left -= 1

                if event.key == pygame.K_a and game_time - last_judgement_time >= judgement_cooldown and pending_judgement_time == 0:
                    last_judgement_time = game_time
                    pending_judgement_time = game_time
                    judgement_delay = random.randint(2000, 5000)  # Random delay between 2-5 seconds

            if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r and revives_left > 0:
                game_over = False
                player_hp = max_hp
                light_left = max_light
                is_reloading = False
                reloads_left = max_reloads  # Reset reloads on revive to be fair
                shield_active = True
                shield_end_time = game_time + 5000
                player_energy = max_energy
                revives_left -= 1

    # --- Gameplay Logic (Only when playing) ---
    if game_state == "playing":

        # Check death
        if player_hp <= 0 and not game_over:
            game_over = True

        if not game_over and not game_won:

            # Handle Reloading
            if is_reloading and game_time >= reload_end_time:
                light_left = max_light
                is_reloading = False

            # Handle Pending Supreme Judgement Execution
            if pending_judgement_time > 0 and game_time >= pending_judgement_time + judgement_delay:
                shield_active = True
                shield_end_time = game_time + 5000

                for i in range(len(bots) - 1, -1, -1):
                    bot = bots[i]
                    dist = math.hypot(bot["rect"].centerx - player_rect.centerx,
                                      bot["rect"].centery - player_rect.centery)
                    if dist <= judgement_radius:
                        if bot["type"] == "orange":
                            blue_dots.append(
                                {"rect": pygame.Rect(bot["rect"].centerx - 6, bot["rect"].centery - 6, 12, 12)})
                        else:
                            bot_kill_count += 1
                        bots.pop(i)

                for b in bosses[:]:
                    dist = math.hypot(b["rect"].centerx - player_rect.centerx, b["rect"].centery - player_rect.centery)
                    if dist <= judgement_radius:
                        b["hp"] -= random.randint(7, 13)
                        if b["hp"] <= 0:
                            protector_idx = next((i for i, b_bot in enumerate(bots) if b_bot["type"] == "multi_stage"),
                                                 -1)
                            if protector_idx != -1:
                                bots.pop(protector_idx)
                                b["hp"] = b.get("max_hp", 18)
                            else:
                                bosses.remove(b)
                                if not bosses:
                                    game_won = True
                                    current_level = increment_level(current_level)

                show_judgement_blast = game_time + 400
                pending_judgement_time = 0

            # Phase Transitions
            if phase == "normal":
                elapsed_time = game_time - game_start_time
                remaining_ms = countdown_duration - elapsed_time
                if remaining_ms <= 0:
                    if current_level <= 3:
                        game_won = True
                        current_level = increment_level(current_level)
                    else:
                        phase = "madness"
                        madness_start_time = game_time
                        spawn_delay = max(500, spawn_delay // 2)
            elif phase == "madness":
                elapsed_time = game_time - madness_start_time
                remaining_ms = madness_duration - elapsed_time
                if remaining_ms <= 0:
                    if current_level <= 6:
                        game_won = True
                        current_level = increment_level(current_level)
                    else:
                        phase = "boss"
                        bots.clear();
                        blue_dots.clear();
                        blind_zones.clear();
                        boss_hazards.clear()
                        player_hp = max_hp;
                        light_left = max_light;
                        shield_active = False;
                        bosses.clear()

                        if current_level == 31:
                            num_bosses, b_size = 2, 50
                            bx1, by1 = (WIDTH // 3) - (b_size // 2), (HEIGHT // 2) - (b_size // 2)
                            bx2, by2 = (2 * WIDTH // 3) - (b_size // 2), (HEIGHT // 2) - (b_size // 2)
                            bosses.append({"rect": pygame.Rect(bx1, by1, b_size, b_size), "float_x": float(bx1),
                                           "float_y": float(by1), "last_shot_time": game_time,
                                           "last_hazard_time": game_time, "hp": 18, "max_hp": 18,
                                           "last_shield_time": game_time, "shield_active": False, "shield_end_time": 0})
                            bosses.append({"rect": pygame.Rect(bx2, by2, b_size, b_size), "float_x": float(bx2),
                                           "float_y": float(by2), "last_shot_time": game_time,
                                           "last_hazard_time": game_time, "hp": 18, "max_hp": 18,
                                           "last_shield_time": game_time, "shield_active": False, "shield_end_time": 0})
                        else:
                            num_bosses, b_size = 1, 80
                            bx, by = (WIDTH - b_size) // 2, (HEIGHT - b_size) // 2
                            bosses.append({"rect": pygame.Rect(bx, by, b_size, b_size), "float_x": float(bx),
                                           "float_y": float(by), "last_shot_time": game_time,
                                           "last_hazard_time": game_time, "hp": 18, "max_hp": 18,
                                           "last_shield_time": game_time, "shield_active": False, "shield_end_time": 0})

                        for _ in range(num_bosses * 3):
                            while True:
                                sx, sy = random.randint(0, WIDTH - bot_size), random.randint(0, HEIGHT - bot_size)
                                new_rect = pygame.Rect(sx, sy, bot_size, bot_size)
                                if new_rect.collidelist(walls) == -1 and not new_rect.colliderect(player_rect): break
                            bots.append({"rect": new_rect, "float_x": float(sx), "float_y": float(sy), "path": [],
                                         "path_timer": 0, "type": "multi_stage", "stage": 0,
                                         "color": SPECIAL_STAGES[0]["color"], "hp": SPECIAL_STAGES[0]["hp"],
                                         "max_hp": SPECIAL_STAGES[0]["hp"]})
            else:
                remaining_ms = 0

            if shield_active and game_time >= shield_end_time: shield_active = False

            # Pickup Management
            if game_time - last_pickup_spawn_time >= 12000:
                for _ in range(random.randint(1, 3)):
                    px, py = random.randint(0, WIDTH - pickup_size), random.randint(0, HEIGHT - pickup_size)
                    pickup_rect = pygame.Rect(px, py, pickup_size, pickup_size)
                    if pickup_rect.collidelist(walls) == -1: pickups.append({"rect": pickup_rect})
                last_pickup_spawn_time = game_time

            if game_time - last_pickup_decay_time >= 1000:
                for pickup in pickups[:]:
                    if random.randint(1, 100) <= 20: pickups.remove(pickup)
                last_pickup_decay_time = game_time

            for pickup in pickups[:]:
                if player_rect.colliderect(pickup["rect"]):
                    pickups.remove(pickup);
                    light_left = min(light_left + random.randint(1, 4), max_light)

            for b_dot in blue_dots[:]:
                if player_rect.colliderect(b_dot["rect"]):
                    blue_dots.remove(b_dot);
                    shield_active = True;
                    shield_end_time = game_time + 20000

            # Player Movement & Energy Drain/Regen
            is_sprinting = pygame.mouse.get_pressed()[2] and player_energy > 0
            if player_energy <= 0:
                player_speed_pps = current_bot_speed_pps - 20
            elif is_sprinting:
                player_speed_pps = current_bot_speed_pps * 2.25
            else:
                player_speed_pps = current_bot_speed_pps + 30
                # Auto-regen energy when not sprinting
                if player_energy < max_energy and game_time - last_energy_regen > 500:
                    player_energy += 1
                    last_energy_regen = game_time

            mx, my = pygame.mouse.get_pos()
            dir_x, dir_y = mx - player_rect.centerx, my - player_rect.centery
            dist = math.hypot(dir_x, dir_y)
            if dist > 0: player_aim_x, player_aim_y = dir_x / dist, dir_y / dist

            frame_movement = player_speed_pps * dt
            move_x, move_y = (player_aim_x * frame_movement,
                              player_aim_y * frame_movement) if dist > frame_movement else (dir_x,
                                                                                            dir_y) if dist > 0 else (0,
                                                                                                                     0)

            player_float_x += move_x
            player_rect.x = int(player_float_x)
            if player_rect.collidelist(walls) != -1: player_float_x -= move_x; player_rect.x = int(player_float_x)

            player_float_y += move_y
            player_rect.y = int(player_float_y)
            if player_rect.collidelist(walls) != -1: player_float_y -= move_y; player_rect.y = int(player_float_y)

            player_rect.clamp_ip(screen_rect)
            player_float_x, player_float_y = float(player_rect.x), float(player_rect.y)

            if is_sprinting and dist > 0:
                sprint_time_accumulator += real_delta_time
                while sprint_time_accumulator >= 2500:
                    player_energy -= 1;
                    sprint_time_accumulator -= 2500
                    if player_energy <= 0: player_energy = 0; sprint_time_accumulator = 0; break

            # Projectile Logic
            for light_proj in player_lights[:]:
                light_proj["float_x"] += light_proj["dx"] * dt
                light_proj["float_y"] += light_proj["dy"] * dt
                light_proj["rect"].x, light_proj["rect"].y = int(light_proj["float_x"]), int(light_proj["float_y"])

                hit_wall = light_proj["rect"].collidelist(walls) != -1
                hit_bounds = not screen_rect.contains(light_proj["rect"])
                hit_bot_index = light_proj["rect"].collidelist([b["rect"] for b in bots])
                hit_boss_obj = next(
                    (b for b in bosses if phase == "boss" and light_proj["rect"].colliderect(b["rect"])), None)

                if hit_wall or hit_bounds or hit_bot_index != -1 or hit_boss_obj:
                    player_lights.remove(light_proj)
                    if hit_bot_index != -1:
                        hit_bot = bots[hit_bot_index]
                        if not (hit_bot["type"] == "ghost" and (game_time - hit_bot["spawn_time"]) % 10000 < 5000):
                            hit_bot["hp"] -= 1
                        if hit_bot["hp"] <= 0:
                            if hit_bot["type"] == "multi_stage":
                                hit_bot["stage"] += 1
                                if hit_bot["stage"] < len(SPECIAL_STAGES):
                                    hit_bot["color"] = SPECIAL_STAGES[hit_bot["stage"]]["color"]
                                    hit_bot["hp"] = hit_bot["max_hp"] = SPECIAL_STAGES[hit_bot["stage"]]["hp"]
                                else:
                                    bot_kill_count += 1;
                                    bots.pop(hit_bot_index)
                            else:
                                if hit_bot["type"] == "orange":
                                    blue_dots.append({"rect": pygame.Rect(hit_bot["rect"].centerx - 6,
                                                                          hit_bot["rect"].centery - 6, 12, 12)})
                                else:
                                    bot_kill_count += 1;
                                    player_hp = min(player_hp + 3, max_hp) if phase == "normal" else player_hp;
                                    light_left = min(light_left + 1, max_light)
                                bots.pop(hit_bot_index)

                                if bot_kill_count >= 5 and current_level >= 2:
                                    bot_kill_count = 0
                                    o_x, o_y = random.randint(0, WIDTH - bot_size), random.randint(0, HEIGHT - bot_size)
                                    bots.append(
                                        {"rect": pygame.Rect(o_x, o_y, bot_size, bot_size), "float_x": float(o_x),
                                         "float_y": float(o_y), "path": [], "path_timer": 0, "color": C_ORANGE,
                                         "type": "orange", "hp": normal_bot_hp, "max_hp": normal_bot_hp})
                    elif hit_boss_obj and not hit_boss_obj.get("shield_active", False):
                        hit_boss_obj["hp"] -= 1
                        if hit_boss_obj["hp"] <= 0:
                            protector_idx = next((i for i, b in enumerate(bots) if b["type"] == "multi_stage"), -1)
                            if protector_idx != -1:
                                bots.pop(protector_idx);
                                hit_boss_obj["hp"] = hit_boss_obj.get("max_hp", 18)
                            else:
                                bosses.remove(hit_boss_obj)
                                if not bosses:
                                    game_won = True
                                    current_level = increment_level(current_level)

            for gb in enemy_lights[:]:
                gb["float_x"] += gb["dx"] * dt
                gb["float_y"] += gb["dy"] * dt
                gb["rect"].x, gb["rect"].y = int(gb["float_x"]), int(gb["float_y"])

                hit_wall = gb["rect"].collidelist(walls) != -1
                hit_bounds = not screen_rect.contains(gb["rect"])
                hit_player = gb["rect"].colliderect(player_rect)
                hit_bot_index = gb["rect"].collidelist([b["rect"] for b in bots])

                if hit_wall or hit_bounds or hit_player or hit_bot_index != -1:
                    if gb in enemy_lights: enemy_lights.remove(gb)
                    if hit_player:
                        if not shield_active:
                            player_hp -= random.randint(1, 8);
                            last_damage_time = game_time
                            if player_hp < 1: player_hp = 0
                    elif hit_bot_index != -1:
                        hit_bot = bots[hit_bot_index]
                        if not (hit_bot["type"] == "ghost" and (game_time - hit_bot["spawn_time"]) % 10000 < 5000):
                            hit_bot["hp"] -= 1
                            if hit_bot["hp"] <= 0:
                                if hit_bot["type"] == "multi_stage":
                                    hit_bot["stage"] += 1
                                    if hit_bot["stage"] < len(SPECIAL_STAGES):
                                        hit_bot["color"] = SPECIAL_STAGES[hit_bot["stage"]]["color"]
                                        hit_bot["hp"] = hit_bot["max_hp"] = SPECIAL_STAGES[hit_bot["stage"]]["hp"]
                                    else:
                                        bot_kill_count += 1;
                                        bots.pop(hit_bot_index)
                                else:
                                    if hit_bot["type"] == "orange":
                                        blue_dots.append({"rect": pygame.Rect(hit_bot["rect"].centerx - 6,
                                                                              hit_bot["rect"].centery - 6, 12, 12)})
                                    else:
                                        bot_kill_count += 1
                                    bots.pop(hit_bot_index)

            # Spawns
            if current_level >= 15 and game_time - last_ghost_spawn_time > ghost_spawn_delay:
                gx, gy = random.randint(0, WIDTH - ghost_size), random.randint(0, HEIGHT - ghost_size)
                bots.append(
                    {"rect": pygame.Rect(gx, gy, ghost_size, ghost_size), "float_x": float(gx), "float_y": float(gy),
                     "path": [], "path_timer": 0, "type": "ghost", "spawn_time": game_time, "color": C_GHOST,
                     "hp": normal_bot_hp, "max_hp": normal_bot_hp})
                last_ghost_spawn_time = game_time
                ghost_spawn_delay = (random.randint(15000, 25000) if phase != "boss" else random.randint(4000,
                                                                                                         7000)) * spawn_mult

            if phase in ["normal", "madness"]:
                if current_level >= 9 and game_time - last_demon_spawn_time > demon_spawn_delay:
                    demon_rect = pygame.Rect(WIDTH // 2 - bot_size // 2, HEIGHT // 2 - bot_size // 2, bot_size,
                                             bot_size)
                    bots.append(
                        {"rect": demon_rect, "float_x": float(demon_rect.x), "float_y": float(demon_rect.y), "path": [],
                         "path_timer": 0, "color": C_DEMON, "type": "demon", "last_blind_cast": game_time,
                         "hp": normal_bot_hp, "max_hp": normal_bot_hp})
                    last_demon_spawn_time = game_time
                    demon_spawn_delay = (random.randint(10000, 35000) if phase == "madness" else random.randint(20000,
                                                                                                                40000)) * spawn_mult

                if current_level >= 12 and game_time - last_curse_spawn_time > (13000 * spawn_mult):
                    bot_x, bot_y = random.randint(0, WIDTH - bot_size), random.randint(0, HEIGHT - bot_size)
                    new_bot_rect = pygame.Rect(bot_x, bot_y, bot_size, bot_size)
                    if new_bot_rect.collidelist(walls) == -1 and not new_bot_rect.colliderect(player_rect):
                        bots.append({"rect": new_bot_rect, "float_x": float(bot_x), "float_y": float(bot_y), "path": [],
                                     "path_timer": 0, "color": C_PURPLE, "type": "curse", "last_shot_time": game_time,
                                     "hp": normal_bot_hp, "max_hp": normal_bot_hp})
                        last_curse_spawn_time = game_time

                if game_time - last_spawn_time > spawn_delay:
                    bot_x, bot_y = random.randint(0, WIDTH - bot_size), random.randint(0, HEIGHT - bot_size)
                    new_bot_rect = pygame.Rect(bot_x, bot_y, bot_size, bot_size)
                    if new_bot_rect.collidelist(walls) == -1 and not new_bot_rect.colliderect(player_rect):
                        type_roll = random.randint(1, 100)
                        bot_color, bot_type = C_RED, "red"
                        if current_level >= 3 and type_roll > 85:
                            bot_color, bot_type = C_PINK, "pink"
                        elif current_level >= 2 and type_roll > 60:
                            bot_color, bot_type = C_GREEN, "green"

                        bots.append({"rect": new_bot_rect, "float_x": float(bot_x), "float_y": float(bot_y), "path": [],
                                     "path_timer": 0, "color": bot_color, "type": bot_type, "last_shot_time": game_time,
                                     "hp": normal_bot_hp, "max_hp": normal_bot_hp})
                        last_spawn_time = game_time
                        spawn_delay = (random.randint(2000, 4000) if phase == "madness" else random.randint(4000,
                                                                                                            7500)) * spawn_mult

            # Universal Bot AI
            for bot in bots:
                if bot["type"] == "ghost":
                    bot["color"] = C_GHOST if (game_time - bot["spawn_time"]) % 10000 < 5000 else DARK_BLUE
                    dir_x, dir_y = player_rect.centerx - bot["rect"].centerx, player_rect.centery - bot["rect"].centery
                    dist = math.hypot(dir_x, dir_y)
                    if dist != 0:
                        bot["float_x"] += (dir_x / dist) * current_bot_speed_pps * dt
                        bot["float_y"] += (dir_y / dist) * current_bot_speed_pps * dt
                        bot["rect"].x, bot["rect"].y = int(bot["float_x"]), int(bot["float_y"])
                    continue

                if bot["type"] == "demon" and game_time - bot["last_blind_cast"] >= 20000:
                    for _ in range(3): blind_zones.append({"pos": (random.randint(0, WIDTH), random.randint(0, HEIGHT)),
                                                           "radius": random.randint(120, 200),
                                                           "end_time": game_time + 15000})
                    bot["last_blind_cast"] = game_time

                if bot["type"] == "orange":
                    dir_x, dir_y = bot["rect"].centerx - player_rect.centerx, bot["rect"].centery - player_rect.centery
                    dist = math.hypot(dir_x, dir_y)
                    if dist != 0:
                        bot["float_x"] += (dir_x / dist) * (current_bot_speed_pps * 0.5) * dt
                        bot["float_y"] += (dir_y / dist) * (current_bot_speed_pps * 0.5) * dt
                        bot["rect"].x, bot["rect"].y = int(bot["float_x"]), int(bot["float_y"])
                        bot["rect"].clamp_ip(screen_rect)
                    continue

                if bot["type"] == "green" and game_time - last_damage_time > damage_cooldown and game_time - bot[
                    "last_shot_time"] >= 7000:
                    gx, gy = bot["rect"].centerx, bot["rect"].centery
                    px, py = player_rect.centerx, player_rect.centery
                    if (abs(py - gy) <= 5 or abs(px - gx) <= 5) and has_line_of_sight((gx, gy), (px, py), walls):
                        b_dx_pps, b_dy_pps = (light_speed_pps if px > gx else -light_speed_pps, 0) if abs(
                            py - gy) <= 5 else (0, light_speed_pps if py > gy else -light_speed_pps)
                        enemy_lights.append({
                            "float_x": float(gx + (1 if b_dx_pps > 0 else (-1 if b_dx_pps < 0 else 0)) * (
                                        bot_size // 2 + 5) - light_size // 2),
                            "float_y": float(gy + (1 if b_dy_pps > 0 else (-1 if b_dy_pps < 0 else 0)) * (
                                        bot_size // 2 + 5) - light_size // 2),
                            "rect": pygame.Rect(gx + (1 if b_dx_pps > 0 else (-1 if b_dx_pps < 0 else 0)) * (
                                        bot_size // 2 + 5) - light_size // 2,
                                                gy + (1 if b_dy_pps > 0 else (-1 if b_dy_pps < 0 else 0)) * (
                                                            bot_size // 2 + 5) - light_size // 2, light_size,
                                                light_size),
                            "dx": b_dx_pps, "dy": b_dy_pps
                        })
                        bot["last_shot_time"] = game_time

                bot["path_timer"] += 1
                if bot["path_timer"] > 30 or not bot["path"]:
                    target = player_rect.center
                    if bot["type"] == "green":
                        tx, ty = (player_rect.centerx, bot["rect"].centery), (bot["rect"].centerx, player_rect.centery)
                        lx, ly = has_line_of_sight(tx, player_rect.center, walls), has_line_of_sight(ty,
                                                                                                     player_rect.center,
                                                                                                     walls)
                        dx, dy = abs(player_rect.centerx - bot["rect"].centerx), abs(
                            player_rect.centery - bot["rect"].centery)
                        target = tx if (lx and ly and dx < dy) or lx else (ty if ly else player_rect.center)
                    bot["path"] = get_path(bot["rect"].center, target, walls)
                    bot["path_timer"] = 0

                if bot["path"]:
                    tx, ty = bot["path"][0]
                    dist = math.hypot(tx - bot["rect"].centerx, ty - bot["rect"].centery)
                    frame_move = current_bot_speed_pps * dt
                    if dist < frame_move:
                        bot["path"].pop(0)
                    elif dist != 0:
                        bot["float_x"] += ((tx - bot["rect"].centerx) / dist) * frame_move
                        bot["float_y"] += ((ty - bot["rect"].centery) / dist) * frame_move
                        bot["rect"].x, bot["rect"].y = int(bot["float_x"]), int(bot["float_y"])

            # Boss AI
            if phase == "boss":
                for b in bosses:
                    if player_rect.colliderect(b["rect"]) and not shield_active: player_hp = 0
                    if not b.get("shield_active", False):
                        if game_time - b.get("last_shield_time", game_time) >= 45000:
                            b["shield_active"] = True;
                            b["shield_end_time"] = game_time + 5000;
                            b["last_shield_time"] = game_time
                    elif game_time >= b.get("shield_end_time", 0):
                        b["shield_active"] = False

                    dist = math.hypot(player_rect.centerx - b["rect"].centerx, player_rect.centery - b["rect"].centery)
                    if dist != 0:
                        b["float_x"] += ((player_rect.centerx - b["rect"].centerx) / dist) * boss_speed_pps * dt
                        b["float_y"] += ((player_rect.centery - b["rect"].centery) / dist) * boss_speed_pps * dt
                        b["rect"].x, b["rect"].y = int(b["float_x"]), int(b["float_y"])

                    if game_time - b["last_shot_time"] >= 10000:
                        fb_dist = math.hypot(player_rect.centerx - b["rect"].centerx,
                                             player_rect.centery - b["rect"].centery)
                        if fb_dist != 0:
                            fireballs.append({
                                "float_x": float(b["rect"].centerx - fireball_size // 2),
                                "float_y": float(b["rect"].centery - fireball_size // 2),
                                "rect": pygame.Rect(b["rect"].centerx - fireball_size // 2,
                                                    b["rect"].centery - fireball_size // 2, fireball_size,
                                                    fireball_size),
                                "dx": ((player_rect.centerx - b["rect"].centerx) / fb_dist) * fireball_speed_pps,
                                "dy": ((player_rect.centery - b["rect"].centery) / fb_dist) * fireball_speed_pps
                            })
                        b["last_shot_time"] = game_time
                    if game_time - b["last_hazard_time"] >= 20000:
                        boss_hazards.append(
                            {"pos": (random.randint(30, WIDTH - 30), random.randint(30, HEIGHT - 30)), "radius": 25,
                             "end_time": game_time + 10000})
                        b["last_hazard_time"] = game_time

            for hazard in boss_hazards[:]:
                if game_time >= hazard["end_time"]: boss_hazards.remove(hazard); continue
                if math.hypot(hazard["pos"][0] - player_rect.centerx, hazard["pos"][1] - player_rect.centery) < (
                        player_size // 2 + hazard["radius"]):
                    if not shield_active and game_time - last_damage_time > damage_cooldown:
                        player_hp -= random.randint(3, 12);
                        last_damage_time = game_time
                        if player_hp < 1: player_hp = 0

            for fireball in fireballs[:]:
                fireball["float_x"] += fireball["dx"] * dt
                fireball["float_y"] += fireball["dy"] * dt
                fireball["rect"].x, fireball["rect"].y = int(fireball["float_x"]), int(fireball["float_y"])
                if not screen_rect.contains(fireball["rect"]): fireballs.remove(fireball); continue
                if fireball["rect"].colliderect(player_rect):
                    if not shield_active:
                        player_hp -= 13
                        if player_hp < 1: player_hp = 0
                    last_damage_time = game_time;
                    fireballs.remove(fireball)

            # Bot Collision
            hit_bot_index = player_rect.collidelist([b["rect"] for b in bots])
            if hit_bot_index != -1 and game_time - last_damage_time > damage_cooldown:
                hit_bot = bots[hit_bot_index]
                if hit_bot["type"] != "orange" and not shield_active:
                    if hit_bot["type"] == "pink":
                        light_left = max(0, light_left - 4)
                    elif hit_bot["type"] == "curse":
                        light_left = max(0, light_left - 15);
                        player_hp -= 9;
                        bots.pop(hit_bot_index)
                        if player_hp < 1: player_hp = 0
                    else:
                        player_hp -= normal_bot_damage
                        if player_hp < 1: player_hp = 0
                last_damage_time = game_time

    # 8. Rendering
    if game_state == "menu":
        screen.fill(BG_COLOR)

        shadow_surf = font_large.render("LIGHT CASTER", True, GRAY)
        title_surf = font_large.render("LIGHT CASTER", True, TEXT_COLOR)
        screen.blit(shadow_surf, (WIDTH // 2 - 208, 102))
        screen.blit(title_surf, (WIDTH // 2 - 210, 100))

        level_y = HEIGHT // 2 - 50
        screen.blit(font_small.render(f"Current Abyssal Depth (Level): {current_level}", True, PLAYER_COLOR),
                    (WIDTH // 2 - 130, level_y))

        start_button_rect = pygame.Rect(WIDTH // 2 - 120, level_y + 40, 240, 50)
        pygame.draw.rect(screen, PLAYER_COLOR, start_button_rect, border_radius=8)
        s_text = ui_font.render("START GAME", True, WHITE)
        screen.blit(s_text, s_text.get_rect(center=start_button_rect.center))

        peaceful_button_rect = pygame.Rect(WIDTH // 2 - 120, level_y + 110, 240, 40)
        pygame.draw.rect(screen, HP_GREEN if peaceful_mode else TEXT_COLOR, peaceful_button_rect, border_radius=8)
        p_text = ui_font.render("Peaceful Mode: ON" if peaceful_mode else "Peaceful Mode: OFF", True, WHITE)
        screen.blit(p_text, p_text.get_rect(center=peaceful_button_rect.center))

        desc_button_rect = pygame.Rect(WIDTH // 2 - 120, level_y + 170, 240, 40)
        pygame.draw.rect(screen, WALL_COLOR, desc_button_rect, border_radius=8)
        desc_text = ui_font.render("How to Play", True, WHITE)
        screen.blit(desc_text, desc_text.get_rect(center=desc_button_rect.center))

    elif game_state == "description":
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, HP_RED, back_button_rect, border_radius=5)
        back_text = ui_font.render("BACK", True, WHITE)
        screen.blit(back_text, back_text.get_rect(center=back_button_rect.center))
        screen.blit(font_large.render("How to Play & Enemy Guide", True, TEXT_COLOR), (WIDTH // 2 - 320, 15))

        controls_y = 70
        screen.blit(font_medium.render("Controls:", True, PLAYER_COLOR), (40, controls_y))
        for i, text in enumerate(["Aim & Move: Mouse Cursor", "Cast Light: Left Mouse Button OR Spacebar",
                                  "Sprint: Hold Right Mouse Button",
                                  "Reload Light: Press 'R' (takes 2.5s, Max 5 uses)",
                                  "Supreme Judgement: Press 'A' to charge a delayed holy blast",
                                  "Revive: Press 'R' when dead to consume a revive (2 Max)"]):
            screen.blit(font_small.render(f"- {text}", True, TEXT_COLOR), (60, controls_y + 35 + (i * 22)))

        enemy_y = controls_y + 190
        screen.blit(font_medium.render("Abyssal Entities:", True, HP_RED), (40, enemy_y))
        y_offset = enemy_y + 35
        for shape, color, name, desc in [("circle", C_RED, "Red Doubt:", "Basic chaser entity."),
                                         ("diamond", C_GREEN, "Green Deceiver:", "Fires projectiles if it sees you."),
                                         ("hexagon", C_PINK, "Pink Thief:",
                                          "Drains your Light (Ammo) when it hits you."),
                                         ("cross", C_ORANGE, "Orange Blessing:",
                                          "Catch it for a shield buff & Resolve."),
                                         ("star", C_DEMON, "Dark Shadow (Lvl 9):",
                                          "Spawns massive dark blind-zones periodically."),
                                         ("star", C_PURPLE, "Curse (Lvl 12):",
                                          "Causes massive Resolve & Light damage on touch!"),
                                         ("triangle", C_GHOST, "Phantom (Lvl 15):",
                                          "Alternates between vulnerable and invincible states.")]:
            draw_shape(screen, shape, color, pygame.Rect(60, y_offset, 30, 30))
            screen.blit(font_small.render(name, True, color), (110, y_offset + 5))
            screen.blit(font_small.render(desc, True, TEXT_COLOR), (280, y_offset + 5))
            y_offset += 35

    else:
        screen.fill(BG_COLOR)
        for wall in walls: pygame.draw.rect(screen, WALL_COLOR, wall, border_radius=8)
        for hazard in boss_hazards: pygame.draw.circle(screen, ENERGY_YELLOW, hazard["pos"],
                                                       hazard["radius"]); pygame.draw.circle(screen, C_ORANGE,
                                                                                             hazard["pos"],
                                                                                             hazard["radius"], 3)
        for pickup in pickups: pygame.draw.circle(screen, ENERGY_YELLOW, pickup["rect"].center, pickup_size // 2)
        for b_dot in blue_dots: pygame.draw.circle(screen, SHIELD_COLOR, b_dot["rect"].center, pickup_size // 2)
        for light_proj in player_lights: pygame.draw.rect(screen, BLACK, light_proj["rect"])
        for gb in enemy_lights: pygame.draw.rect(screen, C_GREEN, gb["rect"])
        for fireball in fireballs: pygame.draw.rect(screen, C_ORANGE, fireball["rect"])

        for bot in bots:
            draw_shape(screen,
                       {"red": "circle", "green": "diamond", "pink": "hexagon", "orange": "cross", "demon": "star",
                        "ghost": "triangle", "curse": "star", "multi_stage": "rect"}[bot["type"]], bot["color"],
                       bot["rect"])
            pygame.draw.rect(screen, HP_RED, (bot["rect"].x, bot["rect"].y - 8, bot["rect"].width, 5))
            pygame.draw.rect(screen, HP_GREEN, (bot["rect"].x, bot["rect"].y - 8, int(
                bot["rect"].width * max(0, bot["hp"] / bot.get("max_hp", normal_bot_hp))), 5))
            pygame.draw.rect(screen, BLACK, (bot["rect"].x, bot["rect"].y - 8, bot["rect"].width, 5), 1)

        if phase == "boss":
            for b in bosses:
                draw_shape(screen, "octagon", C_BOSS, b["rect"])
                if b.get("shield_active", False): pygame.draw.rect(screen, ENERGY_YELLOW, b["rect"].inflate(16, 16), 4)

        if not game_over and not game_won:
            if shield_active or game_time - last_damage_time > damage_cooldown or (game_time // 100) % 2 == 0:
                pygame.draw.rect(screen, PLAYER_COLOR, player_rect, border_radius=5)
            pygame.draw.line(screen, TEXT_COLOR, player_rect.center,
                             (player_rect.centerx + player_aim_x * (player_size // 2 + 15),
                              player_rect.centery + player_aim_y * (player_size // 2 + 15)), 6)
            if shield_active: pygame.draw.circle(screen, SHIELD_COLOR, player_rect.center, 30, 3)

            # Supreme Judgement Brewing Visual
            if pending_judgement_time > 0:
                brew_text = font_small.render("Supreme Judgement descending...", True, C_ORANGE)
                screen.blit(brew_text, (player_rect.centerx - brew_text.get_width() // 2, player_rect.top - 20))

            # Supreme Judgement Blast Visual
            if game_time < show_judgement_blast:
                pygame.draw.circle(screen, ENERGY_YELLOW, player_rect.center, judgement_radius, 5)
                pygame.draw.circle(screen, WHITE, player_rect.center, judgement_radius - 15, 2)

        for zone in blind_zones[:]:
            if game_time >= zone["end_time"]:
                blind_zones.remove(zone)
            else:
                pygame.draw.circle(screen, BLACK, zone["pos"], zone["radius"])

        # UI Overlay - Stats
        pygame.draw.rect(screen, HP_RED, (20, 20, 150, 20))
        pygame.draw.rect(screen, HP_GREEN, (20, 20, int((player_hp / max_hp) * 150), 20))
        pygame.draw.rect(screen, BLACK, (20, 20, 150, 20), 2)
        screen.blit(ui_font.render(f"Resolve: {player_hp}/{max_hp}", True, TEXT_COLOR), (180, 20))

        pygame.draw.rect(screen, WALL_COLOR, (20, HEIGHT - 40, 150, 20))
        pygame.draw.rect(screen, ENERGY_YELLOW, (20, HEIGHT - 40, int((player_energy / max_energy) * 150), 20))
        pygame.draw.rect(screen, BLACK, (20, HEIGHT - 40, 150, 20), 2)
        screen.blit(ui_font.render(f"Endurance: {player_energy}/{max_energy}", True, TEXT_COLOR), (20, HEIGHT - 70))

        # UI Overlay - Supreme Judgement
        judgement_charge = min(1.0, (game_time - last_judgement_time) / judgement_cooldown)
        bar_w, bar_h = 200, 20
        bar_x, bar_y = WIDTH // 2 - bar_w // 2, 20
        pygame.draw.rect(screen, WALL_COLOR, (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, ENERGY_YELLOW, (bar_x, bar_y, int(bar_w * judgement_charge), bar_h))
        pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_w, bar_h), 2)

        a_text = "Judgement: READY (A)" if judgement_charge >= 1.0 else f"Judgement: {int(judgement_charge * 100)}%"
        a_color = C_BOSS if judgement_charge >= 1.0 else TEXT_COLOR
        a_surf = font_small.render(a_text, True, a_color)
        screen.blit(a_surf, a_surf.get_rect(center=(WIDTH // 2, bar_y + bar_h // 2)))

        remaining_seconds = max(0, remaining_ms) // 1000
        if phase == "normal":
            timer_text = ui_font.render(f"Time: {remaining_seconds}s", True, TEXT_COLOR)
            screen.blit(timer_text, timer_text.get_rect(topright=(WIDTH - 20, 20)))
        elif phase == "madness":
            timer_text = ui_font.render(f"MADNESS: {remaining_seconds}s", True, HP_RED)
            screen.blit(timer_text, timer_text.get_rect(topright=(WIDTH - 20, 20)))
        else:
            for i, b in enumerate(bosses):
                pygame.draw.rect(screen, HP_RED, (WIDTH - 170, 20 + (i * 30), 150, 20))
                pygame.draw.rect(screen, HP_GREEN,
                                 (WIDTH - 170, 20 + (i * 30), int(150 * max(0, b["hp"] / b.get("max_hp", 18))), 20))
                pygame.draw.rect(screen, BLACK, (WIDTH - 170, 20 + (i * 30), 150, 20), 2)
                boss_text = boss_hp_font.render(f"BOSS HP: {b['hp']}/{b.get('max_hp', 18)}", True, WHITE)
                screen.blit(boss_text, boss_text.get_rect(center=(WIDTH - 95, 30 + (i * 30))))

        if is_reloading:
            ammo_text = ui_font.render("RELOADING...", True, C_ORANGE)
        else:
            ammo_text = ui_font.render(
                f"Light: {'INFINITE' if phase == 'madness' else light_left} (Press R - {reloads_left} left)", True,
                TEXT_COLOR if light_left > 0 else HP_RED)

        screen.blit(ammo_text, ammo_text.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20)))

        # End Game Overlays
        if game_over or game_won:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))

            if game_over:
                screen.blit(game_over_font.render("GAME OVER", True, HP_RED),
                            game_over_font.render("GAME OVER", True, HP_RED).get_rect(
                                center=(WIDTH // 2, HEIGHT // 2 - 100)))
                revive_hint = ui_font.render(f"Press 'R' to consume Revive! ({revives_left} left)", True,
                                             WHITE) if revives_left > 0 else ui_font.render(
                    "No revives left! Restart game.", True, WALL_COLOR)
                screen.blit(revive_hint, revive_hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
            elif game_won:
                win_text = win_font.render(f"LEVEL {current_level} COMPLETE!" if current_level < 31 else "VICTORY!",
                                           True, HP_GREEN)
                screen.blit(win_text, win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()