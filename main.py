import cv2 as cv
import numpy as np
import pygame
import random
import os

pygame.init()
pygame.font.init()

# Size of windows 
WIDTH, HEIGHT = 800, 600 # Pygmae
WIDTH_CV, HEIGHT_CV = 640, 480 # opencv

WHITE = (255, 255, 255)

FPS = 60

# PYGAME
class Entity(pygame.sprite.Sprite):
    def __init__(self, screen, sprite_path):
        pygame.sprite.Sprite.__init__(self)
        scn_width, scn_heigth = screen.get_size()
        resized_image_width = scn_width * 11 / 100 # 11 % of width
        resized_image_height = scn_heigth * 27 / 100 # 27 % of height

        self.sprite = pygame.image.load(sprite_path).convert_alpha()
        self.edited_sprite = pygame.transform.scale(self.sprite, (resized_image_width, resized_image_height))
        
        self.image = self.edited_sprite
        self.position = [random.randint(60, WIDTH-60), HEIGHT + random.randint(40, 70)]
        self.rect = self.image.get_rect(center = self.position)

        self.hit = False
        self.rotate_sprite = True
        self.speed = random.randint(5, 11)

    def move(self):
        if not self.hit:
            self.rect.centery -= self.speed
        else:
            if self.rotate_sprite:
                self.image = pygame.transform.rotate(self.image, 180)
                self.rotate_sprite = False
            self.rect.centery += 30

        if self.rect.centery < 0 or self.rect.centery > HEIGHT + 70:
            self.set_entity_parametrs()

    def set_entity_parametrs(self):
        self.position = [random.randint(60, WIDTH-60), HEIGHT + random.randint(40, 70)]
        self.rect.center = self.position
        self.hit = False
        self.rotate_sprite = True
        self.image = self.edited_sprite

    def check_ball_hit(self, x, y, radius): # I dont use radius but you can do with radius anything
        if self.rect.x < x < self.rect.topright[0] and \
                self.rect.y < y < self.rect.bottomright[1]:
            self.hit = True
            return True
        return False
        
    def update(self, respawn=False):
        self.move()

        # That for respawn mobs in games when user press ESC button and redirect to game menu
        if respawn:
            self.set_entity_parametrs()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('BallShouter')

# create mobs in game
count_mobs = 5

all_sprites = pygame.sprite.Group()
for mob in range(count_mobs):
    sprite_entity = random.choice(['static/dog1.png', 'static/dog2.png', 'static/dog3.png'])
    entity = Entity(screen, sprite_entity)
    all_sprites.add(entity)

# menu button
button_image = pygame.image.load('static/button.png').convert_alpha()
button_image= pygame.transform.scale(button_image, (WIDTH * 0.2, HEIGHT * 0.1))

# text logo
logo_font = pygame.font.SysFont('Arial', 64)
score_font = pygame.font.SysFont('Arial', 32)
text_surface = logo_font.render('Ball Shouter', False, (0, 0, 0))

# COMPUTER VISION PART
points = [[10,10], [WIDTH_CV-10,10], [WIDTH_CV-10, HEIGHT_CV-10], [10, HEIGHT_CV-10]]
converted_points = [[0, 0], [WIDTH_CV, 0], [WIDTH_CV, HEIGHT_CV], [0, HEIGHT_CV]]
num_point = 0


# Fucntion for work with SET AREA window 
def mouse_events(event, x, y, flags, params):
    global num_point
    global points

    if event == cv.EVENT_MOUSEWHEEL:
        if flags > 0:
            num_point = (num_point + 1) % 4
        else:
            if num_point == 0:
                num_point = 3
            else:
                num_point -= 1
    elif event == cv.EVENT_LBUTTONDOWN:
        points[num_point] = [x, y]
    elif event == cv.EVENT_RBUTTONDBLCLK:
        points = [[10,10], [WIDTH_CV-10,10], [WIDTH_CV-10, HEIGHT_CV-10], [10, HEIGHT_CV-10]]


cv.namedWindow("Camera")
cv.namedWindow("Set Area")
cv.setMouseCallback("Set Area", mouse_events)

cap = cv.VideoCapture(0)

lower_green = np.array([40, 50, 50])
upper_green = np.array([80, 255, 255])
lower_yellow = np.array([20, 100, 100])
upper_yellow = np.array([30, 255, 255])
lower_blue = np.array([100, 50, 50])
upper_blue = np.array([140, 255, 255])
lower_red1 = np.array([0, 50, 50])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([170, 50, 50])
upper_red2 = np.array([180, 255, 255])

game_menu = True
game_score = 0
last_game_score = -1

game_run = True
while game_run:
    # Computer vision Part
    success, frame = cap.read()
    if not success: break
    frame = cv.flip(frame, 1)

    ## Set Game Area surface 
    set_area_frame = frame.copy()
    cv.putText(set_area_frame, str(num_point+1), (100, 100), 1, 5, (255, 255, 255), 2)

    for i, point in enumerate(points):

        # Connect points by lines
        current_point = points[i]
        next_point = points[(i + 1) % 4]
        cv.line(set_area_frame, current_point, next_point, (255, 255, 255), 2)

        # Draw points and selected point
        if i == num_point:
            color = (0, 0, 255)
        else:
            color = (255, 255, 255)
        cv.circle(set_area_frame, point, 10, color, 2)
        cv.circle(set_area_frame, point, 3, color, -1)

    cv.imshow("Set Area", set_area_frame)
    
    ## IMAGE PREPROCESSING 
    detail = cv.detailEnhance(frame, sigma_s = 20, sigma_r = 0.15)
    frame_preprocess = cv.GaussianBlur(detail, (5, 5), 0)
    frame_preprocess = cv.cvtColor(frame_preprocess, cv.COLOR_BGR2HSV)

    ## Transform game surface
    matrix = cv.getPerspectiveTransform(np.float32(points), np.float32(converted_points))
    output = cv.warpPerspective(frame_preprocess, matrix, (WIDTH_CV, HEIGHT_CV))
    output = output.astype(np.uint8)

    # Use hsv inRange mask for findCounter
    mask_green = cv.inRange(output, lower_green, upper_green)
    mask_yellow = cv.inRange(output, lower_yellow, upper_yellow)
    mask_blue = cv.inRange(output, lower_blue, upper_blue)
    mask_red1 = cv.inRange(output, lower_red1, upper_red1)
    mask_red2 = cv.inRange(output, lower_red2, upper_red2)
    mask_red = cv.bitwise_or(mask_red1, mask_red2)
    mask = cv.bitwise_or(mask_green, mask_yellow)
    mask = cv.bitwise_or(mask, mask_blue)
    mask = cv.bitwise_or(mask, mask_red)
    
    ## FINDING THE BALLS (YELLOW/GREEN/BLUE/RED)
    contours, _ = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        (x, y), radius = cv.minEnclosingCircle(contour)
        center = (int(x), int(y))
        radius = int(radius)
        if radius > 10:
            cv.circle(output, center, radius, (0, 255, 0), 3)
            cv.circle(output, center, 5, (0, 255, 255), -1)
        else:
            continue

        # check detection with ball (might be optimizing)
        for i, mob in enumerate(all_sprites):
            if mob.check_ball_hit(x, y, radius):
                game_score += 1
        
    cv.imshow("Camera", output)
    cv.waitKey(15)

    # PYGAME PART
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_run = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_menu = True
                last_game_score = game_score
                game_score = 0
        elif game_menu and event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if 60 < mouse_x < 60 + WIDTH * 0.2 and 300 < mouse_y < 300 + HEIGHT * 0.1:
                game_menu = False

    screen.fill(WHITE)
    
    if game_menu:
        screen.blit(button_image, (60, 300))
        screen.blit(text_surface, (60, 200))
        if last_game_score > 0:
            last_score_surface = score_font.render(f"Last score: {last_game_score}", False, (0,0,0))
            screen.blit(last_score_surface, (500, 260))


    else:
        all_sprites.draw(screen)
        # text score
        score_surface = score_font.render(f'Score: {game_score}', False, (0, 0, 0))
        screen.blit(score_surface, (25, 25))


    all_sprites.update(game_menu)
    pygame.display.flip()
    pygame.time.Clock().tick(FPS)


cap.release()
cv.destroyAllWindows()
