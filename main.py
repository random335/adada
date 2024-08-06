import pygame, time, math, secrets

global carnivores

global plants
plants = []

global cam_offset
cam_offset = [0, 0]

global overall_time
overall_time = time.time()

global deaths
deaths = 0

global death_anims
death_anims = []

global num_packs
num_packs = 1

def angle_between(points):
    return math.atan2(points[1][1] - points[0][1], points[1][0] - points[0][0])*180/math.pi

def scale_image(img, factor=4.0):
    size = round(img.get_width() * factor), round(img.get_height() * factor)
    return pygame.transform.scale(img, size).convert()

def rotate_towards_point(image, image_rect, target_point):
    # Calculate the angle
    dx, dy = target_point[0] - image_rect.centerx, target_point[1] - image_rect.centery
    angle = math.degrees(math.atan2(-dy, dx))  # Negative dy because Pygame's y-axis is inverted

    # Rotate the image
    rotated_image = pygame.transform.rotate(image, angle)

    return rotated_image

def swap_color(img, col1, col2):
    pygame.transform.threshold(img, img, col1, (10, 10, 10), col2, 1, None, True)

win = pygame.display.set_mode([0,0], pygame.FULLSCREEN)

class PlantManager:
    def __init__(self):
        self.plants = [[secrets.choice(range(-1250, win.get_width() + 1250)), secrets.choice(range(-1250, win.get_height() + 1250))] for i in range(500)]
        self.delay = time.time()
        self.sprite = scale_image(pygame.image.load("plant.png").convert())
        self.sprite.set_colorkey([255, 255, 255])
        self.mask = pygame.mask.from_surface(self.sprite)
        self.win_rect = pygame.Rect(0, 0, win.get_width(), win.get_height())
    def update(self):
        for plant in self.plants:
            if self.win_rect.collidepoint((plant[0] + cam_offset[0], plant[1] + cam_offset[1])):
                win.blit(self.sprite, (plant[0] + cam_offset[0], plant[1] + cam_offset[1]))

        while len(self.plants) < 500:
            pos = [secrets.choice(range(-1250, win.get_width() + 1250)), secrets.choice(range(-1250, win.get_height() + 1250))]
            for carnivore in carnivores:
                while math.dist((pos[0], pos[1]), (carnivore.x, carnivore.y)) <= 225:
                    pos = [secrets.choice(range(-1250, win.get_width() + 1250)), secrets.choice(range(-1250, win.get_height() + 1250))]
            self.plants.append(pos)
            
class SpriteSheet:
    def __init__(self, sheet, size, colorkey = [0, 0, 0]):
        self.spritesheet = sheet
        self.colorkey = colorkey
        self.size = [self.spritesheet.get_width()/size[0], self.spritesheet.get_height()/size[1]]
        self.sheet = []
        for i in range(size[1]):
            self.sheet.append([])
            for j in range(size[0]):
                image = pygame.Surface((self.size))
                image.set_colorkey(self.colorkey)
                image.blit(self.spritesheet, (0, 0), [j*self.size[0], i*self.size[1], self.size[0], self.size[1]])
                self.sheet[i].append(image)
    def get(self, loc):
        return self.sheet[loc[1]][loc[0]]
    
class DeathParticleManger:
    def __init__(self, size, positions, colors):
        self.textures = [pygame.Surface(size) for _ in colors]
        [texture.fill(colors[count]) for count, texture in enumerate(self.textures)]
        self.alpha = 255
        self.positions = positions
        self.range = (-3, -2, -1, 0, 1, 2, 3)
    def update(self):
        if self.alpha > 0:
            self.alpha -= 6.5
        for count, texture in enumerate(self.textures):
            texture.set_alpha(self.alpha)
        
            flutter = secrets.choice(self.range)    
            self.positions[count][0] += flutter 
            
            win.blit(texture, [self.positions[count][0] + cam_offset[0], self.positions[count][1] + cam_offset[1]])
            
            self.positions[count][0] -= flutter
            self.positions[count][1]
            
plant_manager = PlantManager()

carnivore_image = scale_image(pygame.image.load("carnivore.png").convert())
swap_color(carnivore_image, [0, 0, 0], [1, 1, 1])
carnivore_image.set_colorkey([255, 255, 255])

carnivore_images = [pygame.transform.rotate(carnivore_image, i) for i in range(0, 361)]
carnivore_masks = [pygame.mask.from_surface(carnivore_images[i]) for i in range(0, 361)]

herbivore_image = scale_image(pygame.image.load("herbivore.png").convert(), 4)
swap_color(herbivore_image, [0, 0, 0], [1, 1, 1])
herbivore_image.set_colorkey([255, 255, 255])

herbivore_images = [pygame.transform.rotate(herbivore_image, i) for i in range(0, 361)]
herbivore_masks = [pygame.mask.from_surface(herbivore_images[i]) for i in range(0, 361)]

class Carnivore:
    def __init__(self, x, y, _type_, traits, generation):
        self.x = x
        self.y = y

        self.type = _type_
        self.traits = traits
        self.food_requirement = traits[2]

        self.hunger = (self.food_requirement/1.8)
        self.delay = time.time()
        self.vital_status = 1

        self.vel = [0, 0]
        self.speed = traits[3]
        self.move_angle = secrets.choice(range(-180, 180))
        self.shown_angle = self.move_angle
        self.r_angle = secrets.choice(range(-180, 180))
        self.move_delay = time.time()

        self.rect = pygame.rect.Rect(x - self.traits[1], y - self.traits[1], self.traits[1]*2, self.traits[1]*2)

        self.prey_target = None
        self.prey = None
        self.prey_timer = time.time()

        self.target = None
        self.target_creature = None
        
        self.life_timer = time.time()
        
        self.gen = generation
        self.new_timer = time.time()
        self.rest_timer = time.time()

        self.pack_leader = None
        self.pack = []

        self.to_rest = False
        self.difference = 0

        self.rest_duration = 2.5
        self.breed_interval = 3.5
        
        self.image = scale_image(carnivore_image, self.traits[1]/10)
        swap_color(self.image, [127, 15, 15], self.traits[0])
        self.final_image = self.image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.outline = self.mask.outline()
        
    def new(self):
        global carnivores
        
        if self.target == None:
            dists = [[], []]
            
            for count, creature in enumerate(carnivores):
                if creature.type == self.type and creature.vital_status == 1 and creature.hunger <= creature.food_requirement/2 and creature.__hash__() != self.__hash__():  
                    dists[0].append(count)
                    dists[1].append(math.dist([self.x, self.y], [creature.x, creature.y]))
                    
            if dists[1] != []:

                    self.target = dists[0][dists[1].index(min(dists[1]))]
                    self.target_creature = carnivores[self.target]
                    carnivores[self.target].target = carnivores.index(self)
                    carnivores[self.target].target_creature = self
                    carnivores[dists[0][dists[1].index(min(dists[1]))]].target = carnivores.index(self)
                        
        if self.target != None:
            if self.target_creature in carnivores:
                self.target = carnivores.index(self.target_creature)
                if carnivores[self.target].target != carnivores.index(self):
                    self.target = None
                    self.target_creature = None
                    return
                self.move_angle = angle_between([(self.x, self.y), (carnivores[self.target].x, carnivores[self.target].y)])

                if self.rect.colliderect(carnivores[self.target].rect):
                    new_color = secrets.choice([carnivores[self.target].traits[0], self.traits[0]])
                    new_radius = secrets.choice([carnivores[self.target].traits[1], self.traits[1]])
                    new_hunger = secrets.choice([carnivores[self.target].traits[2], self.traits[2]])
                    new_speed = secrets.choice([carnivores[self.target].traits[3], self.traits[3]])

                    to_vary = secrets.randbelow(7)

                    if to_vary == 2:

                        variation = secrets.randbelow(4)

                        if variation == 1:
                            addon = secrets.choice(range(-2, 2))

                            while addon == 0:
                                addon = secrets.choice(range(-2, 2))
                                
                            new_radius += addon * 2
                            
                            if addon > 0:
                                new_hunger -= addon
                                new_speed -= addon/3.5
                                
                            if addon < 0:
                                new_hunger += addon
                                new_speed += addon/5

                        if variation == 3:
                            addon = secrets.choice(range(-2, 2))

                            while addon == 0:
                                addon = secrets.choice(range(-2, 2))

                            new_speed += addon/5
                            if addon > 0:
                                new_hunger += addon
                            if addon < 0:
                                new_speed -= addon


                    recombined_traits = [new_color, new_radius, new_hunger, new_speed]
                    child = Carnivore(self.x, self.y, self.type, recombined_traits, self.gen + 1)

                    if self.pack_leader != None:
                        child.pack_leader = self.pack_leader
                        for carnivore in carnivores:
                            if carnivore.__hash__() == self.pack_leader:
                                carnivore.pack.append(child.__hash__())
                    else:
                        self.pack.append(child.__hash__())
                        child.pack_leader = self.__hash__()

                    #child.traits[0] = self.traits[0]
                    
                    carnivores.append(child)
                    self.hunger += 4
                    carnivores[self.target].hunger += 4
                    carnivores[self.target].target = None
                    carnivores[self.target].target_creature = None
                    self.target = None
                    self.new_timer = time.time()
            else:
                self.target = None
                self.target_creature = None
                
    def search_prey(self, creatures):
        global deaths
        if self.prey_target == None:
            dists = [math.dist((self.x, self.y), (creature.x, creature.y)) for creature in creatures]

            if len(dists) > 0:
                self.prey_target = dists.index(min(dists))
                self.prey = creatures[self.prey_target]
                self.prey_timer = time.time()
            
        else:
            if self.prey in creatures:
                self.prey_target = creatures.index(self.prey)
                self.move_angle = angle_between([(self.x, self.y), (creatures[self.prey_target].x, creatures[self.prey_target].y)])
                
                if math.dist((self.x, self.y), (creatures[self.prey_target].x, creatures[self.prey_target].y)) > 225:
                    self.prey_target = None
                    self.prey = None
                    return
                
                self.r_angle = self.move_angle
                if self.r_angle >= 360:
                    self.r_angle = self.r_angle - 360
                if self.r_angle < 0:
                    self.r_angle = 360 + self.r_angle
                    
                if self.mask.overlap(creatures[self.prey_target].mask, ((creatures[self.prey_target].x - self.x), (creatures[self.prey_target].y - self.y))):
                    creatures[self.prey_target].vital_status = 0
                    deaths += 1
                    self.hunger = 1 
                    self.prey_target = None
                    
                for creature in creatures:
                    if math.dist((self.x, self.y), (creature.x, creature.y)) < 100:
                        
                        self.r_angle = self.move_angle
                        if self.r_angle >= 360:
                            self.r_angle = self.r_angle - 360
                        if self.r_angle < 0:
                            self.r_angle = 360 + self.r_angle
                            
                        if self.mask.overlap(creature.mask, ((creature.x - self.x), (creature.y - self.y))):
                            creature.vital_status = 0
                            deaths += 1
                            self.hunger = 1 
                            self.prey_target = None
                            self.prey = None
                            return
                    #print('d')
            else:
                self.prey_target = None
                self.prey = None

    def update(self, creatures):
        global num_packs
        
        self.r_angle = self.move_angle
        if self.r_angle >= 360:
            self.r_angle = self.r_angle - 360
        if self.r_angle < 0:
            self.r_angle = 360 + self.r_angle 
            
        if self.shown_angle < self.r_angle:
            self.shown_angle += 3.5
        if self.shown_angle > self.r_angle:
            self.shown_angle -= 3.5
            
        self.final_image = pygame.transform.rotate(self.image, self.shown_angle)
        win.blit(self.final_image, (self.x + cam_offset[0], self.y + cam_offset[1]))
        self.mask = pygame.mask.from_surface(self.final_image)
        
        self.rect.x = self.x - self.traits[1]
        self.rect.y = self.y - self.traits[1]

        if time.time() - self.move_delay >= 0.25:
            self.move_angle += secrets.choice(range(-5, 5))

        if time.time() - self.delay >= 1.65:
            self.hunger += 1
            self.delay = time.time()

        if self.hunger > self.food_requirement:
            self.vital_status = 0
            particle_sheet = SpriteSheet(self.final_image, [self.final_image.get_width()//4, self.final_image.get_height()//4], [255, 255, 255])

            colors = []
            positions = []
            for j, sheet in enumerate(particle_sheet.sheet):
                    for i, surf in enumerate(sheet):
                        colors.append(surf.get_at([0, 0]))
                        if not (colors[-1].r == 0 and colors[-1].g == 0 and colors[-1].b == 0):
                            positions.append([self.x + (i*4), self.y + (j*4)])
                        else:
                            colors.pop()
                        
            death_anims.append(DeathParticleManger((4, 4), positions, colors))
            
            if self.pack_leader == None:
                count = []
                sizes = []

                for c, carnivore in enumerate(carnivores):
                    if carnivore.__hash__() in self.pack:
                        sizes.append(carnivore.traits[1])
                        count.append(c)

                if len(sizes) > 0:
                    new_leader = count[sizes.index(max(sizes))]
                    carnivores[new_leader].pack_leader = None

                    self.pack.remove(carnivores[new_leader].__hash__())
                    count.remove(new_leader)

                    carnivores[new_leader].pack = self.pack + []

                    for i in count:
                        carnivores[i].pack_leader = carnivores[new_leader].__hash__()
                
        if self.hunger > self.food_requirement*2/3:
            self.search_prey(creatures)
            
        if self.hunger < self.food_requirement/2 and (time.time() - self.new_timer >= self.breed_interval):
            self.new()
        else:
            self.target = None

        self.vel = [self.speed*math.cos(math.radians(self.move_angle)), self.speed*math.sin(math.radians(self.move_angle))]

        if time.time() - self.rest_timer <= self.rest_duration:
            self.vel = [0, 0]
            self.target = None
            self.target_creature = None
            self.new_timer = time.time()
            self.hunger = 1

        if self.pack_leader != None:
            for carnivore in carnivores:
                if carnivore.__hash__() == self.pack_leader and self.hunger < (self.food_requirement*2/3):
                    if math.dist((self.x, self.y), (carnivore.x, carnivore.y)) > 300:
                        self.move_angle = angle_between(((self.x, self.y), (carnivore.x, carnivore.y)))
                        self.vel = [self.speed*math.cos(math.radians(self.move_angle)), self.speed*math.sin(math.radians(self.move_angle))]

                        if time.time() - self.rest_timer <= self.rest_duration:
                            self.to_rest = True
                            self.difference = time.time()
                        
                    else:
                        if self.to_rest:
                            self.rest_timer = self.rest_timer + (time.time() - self.difference)
                            self.to_rest = False
                    break
            
        else:
            
            avg_hunger = 0
            avg_req = 0
            
            for carnivore in carnivores:
                if carnivore.__hash__() in self.pack:
                    avg_hunger += carnivore.hunger
                    avg_req += carnivore.food_requirement
                    
            avg_hunger /= len(self.pack)
            avg_req /= len(self.pack)
            
            if avg_hunger > avg_req*2/3:
                self.rest_timer = time.time()
                
            if len(self.pack) > 20:

                count = []
                sizes = []

                for c, carnivore in enumerate(carnivores):
                    if carnivore.__hash__() in self.pack:
                        sizes.append(carnivore.traits[1])
                        count.append(c)

                new_leader = count[sizes.index(max(sizes))]

                carnivores[new_leader].pack = self.pack[9:(len(self.pack)-1)]
                carnivores[new_leader].pack_leader = None

                count = count[9:(len(count)-1)]

                if new_leader in count:
                    count.remove(new_leader)

                rand_color = [secrets.randbelow(255), secrets.randbelow(255), secrets.randbelow(255)]

                carnivores[new_leader].traits[0] = rand_color

                for i in count:
                    carnivores[i].pack_leader = carnivores[new_leader].__hash__()
                    carnivores[i].traits[0] = rand_color

                self.pack = self.pack[:10]
                
                if carnivores[new_leader].__hash__() in self.pack:
                    self.pack.remove(carnivores[new_leader].__hash__())

                if carnivores[new_leader].__hash__() in carnivores[new_leader].pack:
                    carnivores[new_leader].pack.remove(carnivores[new_leader].__hash__())

                num_packs += 1

        self.x += self.vel[0]
        self.y += self.vel[1]

        if self.x <= -1300 or self.y <= -1300:
            self.move_angle -= 180

            self.x -= self.vel[0]*2
            self.y -= self.vel[1]*2

        if self.x >= win.get_width() + 1300 or self.y >= win.get_height() + 1300:
            self.move_angle -= 180

            self.x -= self.vel[0]*2
            self.y -= self.vel[1]*2
            
start_traits = [[125, 0, 0], 10, 18, 6]

carnivores = [Carnivore(secrets.choice(range(win.get_width() - 300, win.get_width() + 300)), secrets.choice(range(win.get_height() - 300, win.get_height() + 300)), secrets.randbelow(3), start_traits, 0) for i in range(10)]
carnivores[0].pack = [carnivore.__hash__() for carnivore in carnivores[1:]]
for carnivore in carnivores[1:]:
    carnivore.pack_leader = carnivores[0].__hash__()
    
start_traits[0] = [0, 255, 0]
    
carnivores_2 = [Carnivore(secrets.choice(range(win.get_width() - 800, win.get_width() + 800)), secrets.choice(range(win.get_height() - 800, win.get_height() + 800)), secrets.randbelow(3), start_traits, 0) for i in range(10)]
carnivores_2[0].pack = [carnivore.__hash__() for carnivore in carnivores_2[1:]]
for carnivore in carnivores_2[1:]:
    carnivore.pack_leader = carnivores_2[0].__hash__()

carnivores = carnivores + carnivores_2

sin_table = [math.sin(math.radians(i)) for i in range(360)]
cos_table = [math.cos(math.radians(i)) for i in range(360)]

pygame.mixer.init()
songs = [pygame.mixer.Sound("song_" + str(i) + ".ogg") for i in range(1, 4)]
song_channel = pygame.mixer.Channel(0)
current_song = secrets.randbelow(3)
song_channel.play(songs[current_song])

class Button:
    def __init__(self, position, textures, function):
        self.textures = textures
        self.onlick = function[0]
        self.args = function[1]
        self.pos = position
        self.current = 0
        self.rect = self.textures[self.current].get_rect(topleft=self.pos)
        self.click_delay = 0
        self.max_delay = 500
        self.delaying = False
        self.clicksound = pygame.mixer.Sound("click.ogg")
    def update(self):
        self.current = 0
        if self.delaying:
            self.click_delay += 1
        if self.click_delay >= self.max_delay:
            self.delaying = False
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            if pygame.mouse.get_pressed()[0]:
                if not self.delaying:
                    self.onlick(self.args)
                    self.clicksound.play()
            self.current = 1
        win.blit(self.textures[self.current], self.pos)
        self.rect = self.textures[self.current].get_rect(topleft=self.pos)

start_button_sheet = scale_image(pygame.image.load("start_buttons.png").convert(), 1.5)
stats_button_sheet = scale_image(pygame.image.load("stats_buttons.png").convert(), 1.5)
exit_button_sheet = scale_image(pygame.image.load("exit_buttons.png").convert(), 1.5)

start_button_spritesheet = SpriteSheet(start_button_sheet, [2, 1], [255, 255, 255]).sheet[0]
stats_button_spritesheet = SpriteSheet(stats_button_sheet, [2, 1], [255, 255, 255]).sheet[0]
exit_button_spritesheet = SpriteSheet(exit_button_sheet, [2, 1], [255, 255, 255]).sheet[0]

def set_state(x):
    global game_state
    game_state = 1
    
    
global show_stats
show_stats = False

def show_stats(x):
    global show_stats
    show_stats = not show_stats
    pygame.mouse.set_pos((pygame.mouse.get_pos()[0] + 100, pygame.mouse.get_pos()[1] + 100))

start_button = Button(((win.get_width()/2) - (start_button_sheet.get_width()/4), (win.get_height()/2) - (start_button_sheet.get_height()/4)), start_button_spritesheet, [set_state, 1])
stats_button = Button((15, 15), stats_button_spritesheet, [show_stats, 1])
exit_button = Button(((win.get_width()/2) - (exit_button_sheet.get_width()/4), (win.get_height()/2) - (exit_button_sheet.get_height()/4) + 96), exit_button_spritesheet, [lambda x: exit(), 1])

class Herbivore:
    def __init__(self, x, y, _type_, traits, generation):
        self.x = x
        self.y = y

        self.type = _type_
        self.traits = traits
        self.food_requirement = traits[2]

        self.hunger = (self.food_requirement/1.8)
        self.delay = time.time()
        self.vital_status = 1

        self.vel = [0, 0]
        self.speed = traits[3]
        self.move_angle = secrets.choice(range(-180, 180))
        self.move_delay = time.time()
        self.shown_angle = self.move_angle

        self.target = None
        self.plant_target = None
        self.plant = None
        self.target_creature = None
        
        self.life_timer = time.time()
        
        self.gen = generation
        
        self.image = scale_image(herbivore_image, self.traits[1]/10)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        
        self.calculation_timer = time.time()
        self.run_angle = 0
        self.destination = [0, 0]
        
        self.final_image = None
        
    def new(self):
        if self.target == None:
            dists = [[], []]
            for count, creature in enumerate(creatures):
                if creature.type == self.type and creature.vital_status == 1 and creature.hunger <= creature.food_requirement/2 and creature.__hash__() != self.__hash__():  
                    dists[0].append(count)
                    dists[1].append(math.dist([self.x, self.y], [creature.x, creature.y]))
            if dists[1] != []:

                    self.target = dists[0][dists[1].index(min(dists[1]))]
                    self.target_creature = creatures[self.target]
                    creatures[self.target].target = creatures.index(self)
                    creatures[self.target].target_creature = self
                    creatures[dists[0][dists[1].index(min(dists[1]))]].target = creatures.index(self)

        
        if self.target != None:
            if self.target_creature in creatures:
                self.target = creatures.index(self.target_creature)
                if creatures[self.target].target != creatures.index(self):
                    self.target = None
                    self.target_creature = None
                    return
                self.move_angle = angle_between([(self.x, self.y), (creatures[self.target].x, creatures[self.target].y)])
                self.destination = [creatures[self.target].x, creatures[self.target].y]

                if self.rect.colliderect(creatures[self.target].rect):
                    new_color = secrets.choice([creatures[self.target].traits[0], self.traits[0]])
                    new_radius = secrets.choice([creatures[self.target].traits[1], self.traits[1]])
                    new_hunger = secrets.choice([creatures[self.target].traits[2], self.traits[2]])
                    new_speed = secrets.choice([creatures[self.target].traits[3], self.traits[3]])

                    to_vary = secrets.randbelow(7)

                    if to_vary == 2:

                        variation = secrets.randbelow(4)

                        if variation == 1:
                            addon = secrets.choice(range(-2, 2))

                            while addon == 0:
                                addon = secrets.choice(range(-2, 2))
                                
                            new_radius += addon * 2
                            
                            if addon > 0:
                                new_hunger -= addon
                                new_speed -= addon/3.5
                                
                            if addon < 0:
                                new_hunger += addon
                                new_speed += addon/5

                        if variation == 3:
                            addon = secrets.choice(range(-2, 2))

                            while addon == 0:
                                addon = secrets.choice(range(-2, 2))

                            new_speed += addon/5
                            if addon > 0:
                                new_hunger += addon
                            if addon < 0:
                                new_speed -= addon


                    recombined_traits = [new_color, new_radius, new_hunger, new_speed]
                    child = Herbivore(self.x, self.y, self.type, recombined_traits, self.gen + 1)
                    creatures.append(child)
                    self.hunger += 5
                    creatures[self.target].hunger += 5
                    creatures[self.target].target = None
                    self.target = None
            else:
                self.target = None
                self.target_creature = None
    def search_plants(self):
        if self.plant_target == None:
            dists = [math.dist((self.x, self.y), plant) for plant in plant_manager.plants]
       
            if len(dists) > 0:
                for i in range(25):
                    self.plant_target = dists.index(min(dists))
                    self.plant = plant_manager.plants[self.plant_target]
                    for carnivore in carnivores:
                        if math.dist((self.x, self.y), (carnivore.x, carnivore.y)) <= (min(dists)+200):
                            if math.dist(self.plant, (carnivore.x, carnivore.y)) <= 200:
                                dists[self.plant_target] = 10000
            
        else:
            if self.plant in plant_manager.plants:
                self.move_angle = angle_between([(self.x, self.y), self.plant])
                self.destination = self.plant
                if self.mask.overlap(plant_manager.mask, [self.plant[0] - self.x, self.plant[1] - self.y]):
                    plant_manager.plants.remove(self.plant)
                    self.hunger -= 4
            
                    if self.hunger <= 0:
                        self.hunger = 1
                        
                    self.plant_target = None
            else:
                self.plant_target = None
                self.plant = None

    def update(self):

        if time.time() - self.move_delay >= 0.25:
            self.move_angle += secrets.choice(range(-5, 5))

        if time.time() - self.delay >= 1.5:
            self.hunger += 1
            self.delay = time.time()

        if self.hunger > self.food_requirement:
            self.vital_status = 0
            
        
        if self.vital_status == 0:
            particle_sheet = SpriteSheet(self.final_image, [self.final_image.get_width()//4, self.final_image.get_height()//4], [255, 255, 255])

            colors = []
            positions = []
            for j, sheet in enumerate(particle_sheet.sheet):
                    for i, surf in enumerate(sheet):
                        colors.append(surf.get_at([0, 0]))
                        if not (colors[-1].r == 0 and colors[-1].g == 0 and colors[-1].b == 0):
                            positions.append([self.x + (i*4), self.y + (j*4)])
                        else:
                            colors.pop()
                        
            death_anims.append(DeathParticleManger((4, 4), positions, colors))
            
        self.search_plants()
            
        if self.hunger < self.food_requirement/2:
            self.new()
        else:
            self.target = None

        dists = [math.dist((self.x, self.y), (carnivore.x, carnivore.y)) for carnivore in carnivores]
        
        if min(dists) <= 200:
            
            best_average_dist = 0
            if (time.time() - self.calculation_timer) >= 0.5:
                for i in range(0, 360, 4):
                    check_point = [self.x + self.speed*cos_table[i]*30, self.y + self.speed*sin_table[i]*30]
                    avg_dist = 0
                    if check_point[0] <= - 1300 or check_point[0] >= win.get_width() + 1300:
                        avg_dist = -1000000
                        
                    if check_point[1] <= - 1300 or check_point[1] >= win.get_height() + 1300:
                        avg_dist = -1000000    
                                            
                    num_enemies = 0
                    for carnivore in carnivores:
                        if math.dist((self.x, self.y), (carnivore.x, carnivore.y)) <= 200:
                            avg_dist += math.dist(check_point, (carnivore.x, carnivore.y))
                            num_enemies += 1

                    avg_dist /= num_enemies
                    if avg_dist > best_average_dist:
                        best_average_dist = avg_dist
                        self.move_angle = i
                        self.destination = check_point
                        self.run_angle = i
                self.calculation_timer = time.time()
            else:
                self.move_angle = self.run_angle
                
            for plant in plant_manager.plants:
                if math.dist((self.x, self.y), plant) <= 35 and (self.hunger > (self.food_requirement*2/3)):
                    self.move_angle = angle_between([(self.x, self.y), plant])
                    self.destination = plant
                    self.plant = plant
                        
                    if self.mask.overlap(plant_manager.mask, [self.plant[0] - self.x, self.plant[1] - self.y]):
                        
                        plant_manager.plants.remove(plant)
                        
                        self.hunger -= 4
                        if self.hunger <= 0:
                            self.hunger = 1
                            
                        self.plant_target = None
                        self.plant = None
                        break
                    
        if self.shown_angle < self.move_angle:
            self.shown_angle += 3.5
        if self.shown_angle > self.move_angle:
            self.shown_angle -= 3.5
            
        new_image = pygame.transform.rotate(self.image, self.shown_angle + 90)
        self.final_image = new_image
        win.blit(new_image, (self.x + cam_offset[0], self.y + cam_offset[1]))
        self.mask = pygame.mask.from_surface(new_image)
        self.rect = new_image.get_rect(topleft=(self.x, self.y))
        
        #pygame.draw.line(win, [255, 255, 255], (self.x + cam_offset[0], self.y + cam_offset[1]), [self.destination[0] + cam_offset[0], self.destination[1] + cam_offset[1]], 8)
        
            
        self.vel = [self.speed*math.cos(math.radians(self.move_angle)), self.speed*math.sin(math.radians(self.move_angle))]

        self.x += self.vel[0]
        self.y += self.vel[1]
        
        if self.x <= -1300 or self.y <= -1300:
            self.move_angle -= 180

            self.x -= self.vel[0]*2
            self.y -= self.vel[1]*2

        if self.x >= win.get_width() + 1300 or self.y >= win.get_height() + 1300:
            self.move_angle -= 180

            self.x -= self.vel[0]*2
            self.y -= self.vel[1]*2
            


pygame.init()

#traits[1] is radius
#traits[2] is food requirement
#traits[3] is speed
creatures = [Herbivore(secrets.choice(range(-1250, win.get_width() + 1250)), secrets.choice(range(-1250, win.get_height() + 1250)), secrets.randbelow(3), [[0, 0, 125], 10, 15, 5], 0) for i in range(100)]

font = pygame.font.Font("yoster.ttf", 32)
clock = pygame.Clock()
global game_state
game_state = 0

bg = pygame.image.load("bg.png").convert()
stats_font = pygame.font.Font("yoster.ttf", 24)
stats_table = scale_image(pygame.image.load("stats.png").convert(), 2)
title = scale_image(pygame.image.load("title.png").convert(), 2)
title.set_colorkey([255, 255, 255])
swap_color(title, [0, 0, 0], [254, 254, 254])
carnivore_deaths = 0
paused = False
paused_text = scale_image(font.render("PAUSED", False, [255, 255, 255], [0, 0, 0]), 2)
paused_text.set_colorkey((0, 0, 0))
pressed = False

while True:
    win.fill((0, 0, 255))
    clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

    if not song_channel.get_busy():
        current_song = secrets.randbelow(3)
        song_channel.play(songs[current_song])

    if game_state == 0:
        win.blit(bg, (0, 0))
        win.blit(title, ((win.get_width() - title.get_width())/2, (win.get_height() - title.get_height())/2 - 128))
        start_button.update()
        exit_button.update()
    else:
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            game_state = 0
            
            plant_manager = PlantManager()
            creatures.clear()
            creatures = [Herbivore(secrets.choice(range(-1250, win.get_width() + 1250)), secrets.choice(range(-1250, win.get_height() + 1250)), secrets.randbelow(3), [[0, 0, 125], 10, 15, 5], 0) for i in range(100)]
            
            start_traits = [[125, 0, 0], 10, 18, 6]
            
            carnivores = [Carnivore(secrets.choice(range(win.get_width() - 300, win.get_width() + 300)), secrets.choice(range(win.get_height() - 300, win.get_height() + 300)), secrets.randbelow(3), start_traits, 0) for i in range(10)]
            carnivores[0].pack = [carnivore.__hash__() for carnivore in carnivores[1:]]
            for carnivore in carnivores[1:]:
                carnivore.pack_leader = carnivores[0].__hash__()
                
            start_traits[0] = [0, 255, 0]
                
            carnivores_2 = [Carnivore(secrets.choice(range(win.get_width() - 800, win.get_width() + 800)), secrets.choice(range(win.get_height() - 800, win.get_height() + 800)), secrets.randbelow(3), start_traits, 0) for i in range(10)]
            carnivores_2[0].pack = [carnivore.__hash__() for carnivore in carnivores_2[1:]]
            for carnivore in carnivores_2[1:]:
                carnivore.pack_leader = carnivores_2[0].__hash__()

            carnivores = carnivores + carnivores_2
            
            death_anims.clear()
            
            deaths = 0
            
            carnivore_deaths = 0
            
            continue
        
        plant_manager.update()

        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            cam_offset[0] -= 8
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            cam_offset[0] += 8

        if pygame.key.get_pressed()[pygame.K_UP]:
            cam_offset[1] += 8
        if pygame.key.get_pressed()[pygame.K_DOWN]:
            cam_offset[1] -= 8

        if not paused:
            [creature.update() for creature in creatures]
            
            for count, creature in enumerate(creatures):
                if creature.vital_status == 0:
                    creatures.pop(count)
                    deaths += 1
                    
            [carnivore.update(creatures) for carnivore in carnivores]
            
            for count, carnivore in enumerate(carnivores):
                if carnivore.vital_status == 0:
                    carnivores.pop(count)
                    carnivore_deaths += 1
            
            for anim in death_anims:
                anim.update()
                if anim.alpha <= 10:
                    death_anims.remove(anim)
        else:
            
            for creature in creatures:
                win.blit(creature.final_image, (creature.x + cam_offset[0], creature.y + cam_offset[1]))
                
            for carnivore in carnivores:
                win.blit(carnivore.final_image, (carnivore.x + cam_offset[0], carnivore.y + cam_offset[1]))
                
            for anim in death_anims:
                anim.update()
                anim.alpha += 6.5
                if anim.alpha <= 10:
                    death_anims.remove(anim)
                    
            win.blit(paused_text, ((win.get_width() - paused_text.get_width())/2, win.get_height() - (paused_text.get_height() + 12)))
        stats_button.update()
        
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            
            if not pressed:
                paused = not paused
                pressed = True
            
        else:
            pressed = False
        
        if show_stats:
            
            win.blit(stats_table, [15, 111])
            
            h_pop_text = stats_font.render(str(len(creatures)), False, [127, 127, 127], [0, 0, 0])
            c_pop_text = stats_font.render(str(len(carnivores)), False, [127, 127, 127], [0, 0, 0])
            win.blit(h_pop_text, [247, 160])
            win.blit(c_pop_text, [464, 160])
            
            h_size_text = stats_font.render(str(round(sum([c.traits[1] for c in creatures])/len(creatures), 2)), False, [127, 127, 127], [0, 0, 0])
            c_size_text = stats_font.render(str(round(sum([c.traits[1] for c in carnivores])/len(carnivores), 2)), False, [127, 127, 127], [0, 0, 0])
            win.blit(h_size_text, [247, 205])
            win.blit(c_size_text, [464, 205])
            
            h_speed_text = stats_font.render(str(round(sum([c.speed for c in creatures])/len(creatures), 2)), False, [127, 127, 127], [0, 0, 0])
            c_speed_text = stats_font.render(str(round(sum([c.speed for c in carnivores])/len(carnivores), 2)), False, [127, 127, 127], [0, 0, 0])
            win.blit(h_speed_text, [247, 250])
            win.blit(c_speed_text, [464, 250])
            
            h_req_text = stats_font.render(str(round(sum([c.traits[-2] for c in creatures])/len(creatures), 2)), False, [127, 127, 127], [0, 0, 0])
            c_req_text = stats_font.render(str(round(sum([c.traits[-2] for c in carnivores])/len(carnivores), 2)), False, [127, 127, 127], [0, 0, 0])
            win.blit(h_req_text, [247, 295])
            win.blit(c_req_text, [464, 295])
            
            h_deaths_text = stats_font.render(str(deaths), False, [127, 127, 127], [0, 0, 0])
            c_deaths_text = stats_font.render(str(carnivore_deaths), False, [127, 127, 127], [0, 0, 0])
            win.blit(h_deaths_text, [252, 335])
            win.blit(c_deaths_text, [464, 335])
        
    pygame.display.update()