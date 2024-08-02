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
            self.positions[count][1] -= 1.5
            
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