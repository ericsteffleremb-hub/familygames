
IP = "127.0.0.3"
PORT = 5000

import pygame
import math
import sys
import random

#import threading
import time
from queue import Queue

import socket
import threading
import json

server_socket = None
incoming_messages = []

# Shared queue
q = Queue()

pygame.init()

WIDTH, HEIGHT = 900, 700
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hex Rings with Player Pieces")

CLOCK = pygame.time.Clock()

HEX_RADIUS = 60
CENTER_CIRCLE_RADIUS = 18

HEX_COLORS = [
    (255, 255, 0),
    (255, 0, 0),
    (75, 75, 75),
    (25, 125, 75),
    (255, 255, 255),
    (224, 208, 158)#(194, 178, 128),
]

PLAYER_COLORS = [
    (0, 0, 0),
    (255, 255, 255),
    (255, 165, 0),
    (0, 0, 255),
    (0, 255, 255),
    (128, 0, 128),
]

OUTLINE_COLOR = (100, 100, 100)

FONT = pygame.font.SysFont(None, 24)
BIG_FONT = pygame.font.SysFont(None, 32)

DIRECTIONS = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
]

class Counter:
    def __init__(self, x, y, color):
        self.value = 0
        self.color = color
        self.rect = pygame.Rect(x, y, 120, 50)

        # + and - buttons
        self.plus_rect = pygame.Rect(x + 125, y, 40, 24)
        self.minus_rect = pygame.Rect(x + 125, y + 26, 40, 24)

    def draw(self, surf):
        # counter background
        pygame.draw.rect(surf, self.color, self.rect)
        pygame.draw.rect(surf, (0,0,0), self.rect, 2)

        # value text
        txt = FONT.render(str(self.value), True, (0,0,0))
        surf.blit(txt, txt.get_rect(center=self.rect.center))

        # + button
        pygame.draw.rect(surf, (255,255,255), self.plus_rect)
        pygame.draw.rect(surf, (0,0,0), self.plus_rect, 2)
        plus_txt = FONT.render("+", True, (0,0,0))
        surf.blit(plus_txt, plus_txt.get_rect(center=self.plus_rect.center))

        # - button
        pygame.draw.rect(surf, (255,255,255), self.minus_rect)
        pygame.draw.rect(surf, (0,0,0), self.minus_rect, 2)
        minus_txt = FONT.render("-", True, (0,0,0))
        surf.blit(minus_txt, minus_txt.get_rect(center=self.minus_rect.center))

    def handle_click(self, pos):
        if self.plus_rect.collidepoint(pos):
            self.value += 1
        elif self.minus_rect.collidepoint(pos):
            self.value -= 1

def axial_to_pixel(q, r, radius):
    x = radius * (math.sqrt(3) * q + math.sqrt(3)/2 * r)
    y = radius * (1.5 * r)
    return x, y


def hex_points(center, radius):
    cx, cy = center
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        pts.append((cx + radius * math.cos(angle),
                    cy + radius * math.sin(angle)))
    return pts


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if ((y1 > y) != (y2 > y)) and \
           (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1):
            inside = not inside
    return inside


def distance_point_to_segment(px, py, x1, y1, x2, y2):
    vx, vy = x2 - x1, y2 - y1
    wx, wy = px - x1, py - y1
    seg_len_sq = vx * vx + vy * vy
    if seg_len_sq == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0, min(1, (wx * vx + wy * vy) / seg_len_sq))
    proj_x = x1 + t * vx
    proj_y = y1 + t * vy
    return math.hypot(px - proj_x, py - proj_y)


def draw_text_center(text, y, color=(255, 255, 255)):
    surf = FONT.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, y))
    SCREEN.blit(surf, rect)


def choose_player_color(prompt):
    while True:
        SCREEN.fill((30, 30, 30))
        draw_text_center(prompt, HEIGHT // 2 - 40)
        for i, col in enumerate(PLAYER_COLORS):
            label = f"{i+1}: {['Black','White','Orange','Blue','Cyan','Purple'][i]}"
            surf = FONT.render(label, True, col)
            rect = surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10 + i * 25))
            SCREEN.blit(surf, rect)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                idx = event.key - pygame.K_1
                if 0 <= idx < len(PLAYER_COLORS):
                    return PLAYER_COLORS[idx]

def choose_hex_value(prompt):
    numVal = 0
    while True:
        SCREEN.fill((30, 30, 30))
        draw_text_center(prompt, HEIGHT // 2 - 40)
        
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                #print(event.key)
                if event.key >= 48 and event.key <= 57:
                    #print("in ascii num ", numVal)
                    if numVal != 0:
                        numVal = numVal*10 + (event.key - 48)
                        return numVal
                    else:
                        #print("in else")
                        numVal = (event.key - 48)
                else:
                    return numVal

                

def choose_vertex_shape_and_color():
    shape = None
    color = None

    while shape is None:
        SCREEN.fill((30, 30, 30))
        draw_text_center("Press S for square, R for rectangle", HEIGHT // 2)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    shape = "square"
                elif event.key == pygame.K_r:
                    shape = "rectangle"

    while color is None:
        SCREEN.fill((30, 30, 30))
        draw_text_center(f"Shape: {shape}. Press 1-6 for color", HEIGHT // 2 - 40)
        for i, col in enumerate(PLAYER_COLORS):
            label = f"{i+1}: {['Black','White','Orange','Blue','Cyan','Purple'][i]}"
            surf = FONT.render(label, True, col)
            rect = surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10 + i * 25))
            SCREEN.blit(surf, rect)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                idx = event.key - pygame.K_1
                if 0 <= idx < len(PLAYER_COLORS):
                    color = PLAYER_COLORS[idx]

    return shape, color


class HexTile:
    def __init__(self, q, r, center):
        self.q = q
        self.r = r
        self.center = center
        self.points = hex_points(center, HEX_RADIUS)
        self.color_index = 0

        self.edge_pieces = [None] * 6
        self.vertex_pieces = [None] * 6
        #print("HexTile Center ", center)
        self.number = random.randint(2, 12)

    @property
    def color(self):
        return HEX_COLORS[self.color_index]

    def cycle_color(self):
        self.color_index = (self.color_index + 1) % len(HEX_COLORS)

    def draw_hex(self, surf):
        pygame.draw.polygon(surf, self.color, self.points)
        pygame.draw.polygon(surf, (0, 0, 0), self.points, 2)

    def draw_center_circle(self, surf, isRobber):
        pygame.draw.circle(surf, (0, 0, 0), self.center, CENTER_CIRCLE_RADIUS, 2)

        # Draw number
        if isRobber:
            num_surf = BIG_FONT.render("R", True, (0, 0, 0))
        else:
            num_surf = BIG_FONT.render(str(self.number), True, (0, 0, 0))
        rect = num_surf.get_rect(center=self.center)
        surf.blit(num_surf, rect)

    def draw_edge_pieces(self, surf):
        for i, piece in enumerate(self.edge_pieces):
            if piece is None:
                continue
            p1 = self.points[i]
            p2 = self.points[(i + 1) % 6]
            x1, y1 = p1
            x2, y2 = p2
            vx, vy = x2 - x1, y2 - y1
            length = math.hypot(vx, vy)
            ux, uy = vx / length, vy / length

            rect_len = 0.8 * length
            rect_wid = 0.3 * rect_len

            midx = (x1 + x2) / 2
            midy = (y1 + y2) / 2

            px, py = -uy, ux
            half_len = rect_len / 2
            half_wid = rect_wid / 2

            c1 = (midx - ux * half_len + px * half_wid,
                  midy - uy * half_len + py * half_wid)
            c2 = (midx + ux * half_len + px * half_wid,
                  midy + uy * half_len + py * half_wid)
            c3 = (midx + ux * half_len - px * half_wid,
                  midy + uy * half_len - py * half_wid)
            c4 = (midx - ux * half_len - px * half_wid,
                  midy - uy * half_len - py * half_wid)

            pygame.draw.polygon(surf, piece['color'], [c1, c2, c3, c4])
            pygame.draw.polygon(surf, OUTLINE_COLOR, [c1, c2, c3, c4], 2)
    def SetNumber(self, x):
        self.number = x
        

    def draw_vertex_pieces(self, surf):
        for i, piece in enumerate(self.vertex_pieces):
            if piece is None:
                continue
            vx, vy = self.points[i]
            size = 20
            color = piece['color']

            if piece['shape'] == "square":
                rect = pygame.Rect(0, 0, size, size)
            else:
                rect = pygame.Rect(0, 0, size * 2, size)

            rect.center = (vx, vy)
            pygame.draw.rect(surf, color, rect)
            pygame.draw.rect(surf, OUTLINE_COLOR, rect, 2)
    def to_dict(self):
        return {
            "q": self.q,
            "r": self.r,
            "center": self.center,
            "color_index": self.color_index,
            "number": self.number,
            "edge_pieces": self.edge_pieces,
            "vertex_pieces": self.vertex_pieces
        }
    @classmethod
    def from_dict(cls, data):
        tile = cls(data["q"], data["r"], tuple(data["center"]))
        tile.color_index = data["color_index"]
        tile.number = data["number"]
        tile.edge_pieces = data["edge_pieces"]
        tile.vertex_pieces = data["vertex_pieces"]
        return tile

class HintCircle:
    def __init__(self, x, y, radius, text, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.text = text
        self.color = color

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (self.x, self.y), self.radius)
        #pygame.draw.circle(surf, (0,0,0), (self.x, self.y), self.radius, 1)

    def is_hovered(self, mouse_pos):
        mx, my = mouse_pos
        return math.hypot(mx - self.x, my - self.y) <= self.radius


def CenterFree(tileArray, center):
    for i in tileArray:
        if i.center == center:
            return False
    return True
    
def generate_hex_rings():
    tiles = []
    cx0, cy0 = (WIDTH // 2 + 120), (HEIGHT // 2 - 40)

    tiles.append(HexTile(0, 0, (cx0, cy0)))

    for dq, dr in DIRECTIONS:
        q, r = dq, dr
        px, py = axial_to_pixel(q, r, HEX_RADIUS)
        if CenterFree(tiles, (cx0 + px, cy0 + py)):
            tiles.append(HexTile(q, r, (cx0 + px, cy0 + py)))

    for dq, dr in DIRECTIONS:
        q1, r1 = dq, dr
        q2, r2 = q1 + dq, r1 + dr
        px, py = axial_to_pixel(q2, r2, HEX_RADIUS)
        if CenterFree(tiles, (cx0 + px, cy0 + py)):
            tiles.append(HexTile(q2, r2, (cx0 + px, cy0 + py)))

        left_dir = DIRECTIONS[(DIRECTIONS.index((dq, dr)) - 1) % 6]
        right_dir = DIRECTIONS[(DIRECTIONS.index((dq, dr)) + 1) % 6]

        ql, rl = q1 + left_dir[0], r1 + left_dir[1]
        qr, rr = q1 + right_dir[0], r1 + right_dir[1]

        px, py = axial_to_pixel(ql, rl, HEX_RADIUS)
        if CenterFree(tiles, (cx0 + px, cy0 + py)):
            tiles.append(HexTile(ql, rl, (cx0 + px, cy0 + py)))

        px, py = axial_to_pixel(qr, rr, HEX_RADIUS)
        if CenterFree(tiles, (cx0 + px, cy0 + py)):
            tiles.append(HexTile(qr, rr, (cx0 + px, cy0 + py)))
    #print("TilesLength: ", len(tiles))
    return tiles


def find_clicked_hex(tiles, pos):
    for tile in tiles:
        if point_in_polygon(pos, tile.points):
            return tile
    return None


def classify_click(tile, pos):
    px, py = pos

    if math.hypot(px - tile.center[0], py - tile.center[1]) < CENTER_CIRCLE_RADIUS:
        return "center", None

    min_v = float('inf')
    v_idx = None
    for i, (vx, vy) in enumerate(tile.points):
        d = math.hypot(px - vx, py - vy)
        if d < min_v:
            min_v = d
            v_idx = i
    if min_v < HEX_RADIUS * 0.25:
        return "vertex", v_idx

    min_e = float('inf')
    e_idx = None
    for i in range(6):
        x1, y1 = tile.points[i]
        x2, y2 = tile.points[(i + 1) % 6]
        d = distance_point_to_segment(px, py, x1, y1, x2, y2)
        if d < min_e:
            min_e = d
            e_idx = i
    if min_e < HEX_RADIUS * 0.25:
        return "edge", e_idx

    return None, None


def randomize_numbers(tiles):
    for tile in tiles:
        tile.number = random.randint(2, 12)

def producer_thread():
    """Thread B: produces items and puts them in the queue."""
    while True:
        if q.empty():
            for i in range(10):
                print("Producer adding:", i)
                q.put(i)
                time.sleep(0.2)         # simulate data arriving over time
        
def network_thread():
    global incoming_messages
    while True:
        raw = server_socket.recv(4096)
        if not raw:
            break

        for line in raw.split(b"\n"):
            if not line.strip():
                continue
            msg = json.loads(line.decode())
            incoming_messages.append(msg)

def connect_to_server(ip=IP, port=PORT): 
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((ip, port))
    threading.Thread(target=network_thread, daemon=True).start()

    # request full board state
    send_message({"type": "request_full_state"})

def send_message(msg):
    server_socket.sendall(json.dumps(msg).encode() + b"\n")

def main():
    hover_text = None
    connect_to_server()
    RobberIndex = 0
    # Create threads
    #t1 = threading.Thread(target=producer_thread, daemon=True)
    #t1.start()
    tiles = generate_hex_rings()
    for i in range(0, len(tiles)):
        tiles[i].SetNumber(i)
    
    random_button = pygame.Rect(20, 20, 180, 40)#pygame.Rect(WIDTH//2 - 80, 20, 180, 40)
    shiftX = -10
    shiftY = 0
    resourceCounters = 100
    bottomCounters = 630
    counters = [
        Counter(20, 120 + shiftY, HEX_COLORS[0]),
        Counter(20, 200 + shiftY, HEX_COLORS[1]),
        Counter(20, 280 + shiftY, HEX_COLORS[2]),
        Counter(20, 360 + shiftY, HEX_COLORS[3]),
        Counter(20, 440 + shiftY, HEX_COLORS[4]),
        
        Counter(20 + shiftX, bottomCounters, HEX_COLORS[4]),
        Counter(200 + shiftX, bottomCounters, HEX_COLORS[4]),
        Counter(380 + shiftX, bottomCounters, HEX_COLORS[4]),
        Counter(560 + shiftX, bottomCounters, HEX_COLORS[4]),
        Counter(740 + shiftX, bottomCounters, HEX_COLORS[4]),

    ]

    hint_circles = [
        HintCircle(427, 73, 10, "3:1", (0,0,0)),
        HintCircle(608, 67, 10, "2:1", HEX_COLORS[0]),
        HintCircle(762, 159, 10, "2:1", HEX_COLORS[2]),
        HintCircle(850, 307, 10, "3:1", (0,0,0)),
        HintCircle(763, 464, 10, "2:1", HEX_COLORS[4]),
        HintCircle(606, 553, 10, "3:1", (0,0,0)),
        HintCircle(421, 544, 10, "3:1", (0,0,0)),
        HintCircle(338, 399, 10, "2:1", HEX_COLORS[1]),
        HintCircle(337, 215, 10, "2:1", HEX_COLORS[3])
    ]


    running = True
    while running:
        CLOCK.tick(60)
        
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                # Check counter clicks first
                for c in counters:
                    if c.plus_rect.collidepoint(pos) or c.minus_rect.collidepoint(pos):
                        c.handle_click(pos)
                        break

                if random_button.collidepoint(pos):
                    randomize_numbers(tiles)
                    continue

                tile = find_clicked_hex(tiles, pos)

                if tile:
                    region, idx = classify_click(tile, pos)

                    if region == "center":
                        tile.cycle_color()

                    elif region == "edge":
                        if tile.edge_pieces[idx] is None:
                            color = choose_player_color("Choose color for edge piece")
                            tile.edge_pieces[idx] = {'color': color}
                        else:
                            tile.edge_pieces[idx] = None

                    elif region == "vertex":
                        if tile.vertex_pieces[idx] is None:
                            shape, color = choose_vertex_shape_and_color()
                            tile.vertex_pieces[idx] = {
                                'shape': shape,
                                'color': color
                            }
                        else:
                            tile.vertex_pieces[idx] = None
                    send_message({
                        "type": "update_tile",
                        "tile": tile.to_dict()
                    })
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                pos = event.pos
                tile = find_clicked_hex(tiles, pos)
                #print("Right Click", pos)

                if tile:
                    region, idx = classify_click(tile, pos)

                    if region == "center":
                        HvalReturn = choose_hex_value("enter value for center, and press enter")
                        if 0 != HvalReturn:
                            tile.SetNumber(HvalReturn)
                            for i in range(0, len(tiles)):
                                if tile == tiles[i]:
                                    send_message({
                                        "type": "SN",
                                        "I" : i,
                                        "N": HvalReturn
                                    })
                        else:
                            for i in range(0, len(tiles)):
                                if tile == tiles[i]:
                                    RobberIndex = i
                                    send_message({
                                        "type": "RI",
                                        "I": RobberIndex
                                    })
                                    break
                    elif region == "edge":
                        if tile.edge_pieces[idx] is not None:
                            tile.edge_pieces[idx] = None

                    elif region == "vertex":
                        if tile.vertex_pieces[idx] is not None:
                            tile.vertex_pieces[idx] = None
                    send_message({
                        "type": "update_tile",
                        "tile": tile.to_dict()
                    })
            mouse_pos = pygame.mouse.get_pos()
            hover_text = None
            for hc in hint_circles:
                if hc.is_hovered(mouse_pos):
                    hover_text = hc.text
                    break
        SCREEN.fill((50, 50, 70))

        pygame.draw.rect(SCREEN, (180, 180, 180), random_button)
        pygame.draw.rect(SCREEN, (0, 0, 0), random_button, 2)
        txt = FONT.render("Randomize Numbers", True, (0, 0, 0))
        SCREEN.blit(txt, txt.get_rect(center=random_button.center))

        resourceLabels = [
            FONT.render("Hay", True, HEX_COLORS[0]),
            FONT.render("Brick", True, HEX_COLORS[1]),
            FONT.render("Ore", True, HEX_COLORS[2]),
            FONT.render("Trees", True, HEX_COLORS[3]),
            FONT.render("Sheep", True, HEX_COLORS[4])
        ]
        xBegin = 25
        yBegin = resourceCounters
        for i in resourceLabels:
            SCREEN.blit(i, (xBegin, yBegin + shiftY))
            yBegin = yBegin + 80
        cardLabels = [
            FONT.render("Knight", True, (255, 255, 255)),
            FONT.render("Victory Point", True, (255, 255, 255)),
            FONT.render("Monopoly", True, (255, 255, 255)),
            FONT.render("Road Building", True, (255, 255, 255)),
            FONT.render("Year of Plenty", True, (255, 255, 255))
        ]

        xBegin = 25
        yBegin = bottomCounters + 50
        for i in cardLabels:
            SCREEN.blit(i, (xBegin + shiftX, yBegin))
            xBegin = xBegin + 180
        for c in counters:
            c.draw(SCREEN)

        for tile in tiles:
            tile.draw_hex(SCREEN)
        
        for i in range(0, len(tiles)):
            if RobberIndex == i:
                tiles[i].draw_center_circle(SCREEN, True)
            else:
                tiles[i].draw_center_circle(SCREEN, False)

        for tile in tiles:
            tile.draw_edge_pieces(SCREEN)

        for tile in tiles:
            tile.draw_vertex_pieces(SCREEN)
        
        for hc in hint_circles:
            hc.draw(SCREEN)
        
        if hover_text is not None:
            # simple tooltip near mouse
            mx, my = mouse_pos
            tip_surf = FONT.render(hover_text, True, (255, 255, 255))
            tip_rect = tip_surf.get_rect(topleft=(mx + 10, my + 10))
            pygame.draw.rect(SCREEN, (0, 0, 0), tip_rect.inflate(6, 6))
            SCREEN.blit(tip_surf, tip_rect)

        
        pygame.display.flip()

        while incoming_messages:
            msg = incoming_messages.pop(0)

            if msg["type"] == "full_state":
                tiles = [HexTile.from_dict(t) for t in msg["tiles"]]

            elif msg["type"] == "update_tile":
                data = msg["tile"]
                for t in tiles:
                    if t.q == data["q"] and t.r == data["r"]:
                        t.color_index = data["color_index"]
                        t.number = data["number"]
                        t.edge_pieces = data["edge_pieces"]
                        t.vertex_pieces = data["vertex_pieces"]
            elif msg["type"] == "RI":
                RobberIndex = msg["I"]
            elif msg["type"] == "SN":
                tiles[msg["I"]].SetNumber(msg["N"])
            elif msg["type"] == 1:
                send_message({"type": 1})


    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
