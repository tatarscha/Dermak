import pygame
from setting import *
from support import import_folder

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups,obstacle_sprites,create_attack,destroy_attack,create_magic):
        super().__init__(groups)
        self.image = pygame.image.load('Dermak-main/1 - level/graphics/test/player.png').convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0,-26)

        #graphics setup
        self.import_player_assets()
        self.status = 'down'
        self.frame_index = 0
        self.animation_speed = 0.15

        #movement
        self.direction = pygame.math.Vector2()
        self.attacking = False
        self.attack_cooldown = 400
        self.attacking_time = None
        self.obstacle_sprites = obstacle_sprites

        # weapon
        self.create_attack = create_attack
        self.destroy_attack = destroy_attack
        self.weapon_index = 0
        self.weapon = list(weapon_data.keys())[self.weapon_index]
        self.can_switch_weapon = True
        self.weapon_switch_time = None
        self.switch_duration_cooldown = 200

        # magic
        self.create_magic = create_magic
        #self.destroy_magic = magic
        self.magic_index = 0
        self.magic = list(magic_data.keys())[self.magic_index]
        self.can_switch_magic = True
        self.magic_switch_time = None
        #self.switch_duration_cooldown = 200


        # stats
        self.stats = {'health': 100, 'energy': 60, 'attack': 10, 'magic': 4, 'speed': 5}
        self.health = self.stats['health'] * 0.5
        self.energy = self.stats['energy'] * 0.8
        self.exp = 123
        self.speed = self.stats['speed']

        # gamepad
        pygame.joystick.init()  # Инициализируем модуль джойстика
        self.joystick = None
        if pygame.joystick.get_count() > 0:  # Проверяем, есть ли подключенные геймпады
            self.joystick = pygame.joystick.Joystick(0)  # Берем первый геймпад
            self.joystick.init()  # Инициализируем его
            print(f"Геймпад подключен: {self.joystick.get_name()}")
        else:
            print("Геймпад не найден")

    def import_player_assets(self):
        character_path = 'Dermak-main/1 - level/graphics/player/'
        self.animations = {'up': [], 'down': [], 'left': [], 'right': [],
                           'right_idle': [], 'left_idle': [], 'up_idle': [], 'down_idle': [],
                           'right_attack': [], 'left_attack': [], 'up_attack': [], 'down_attack': []}

        for animation in self.animations.keys():
            full_path = character_path + animation
            frames = import_folder(full_path)
            self.animations[animation] = frames
            #print(f"Animation '{animation}': {len(frames)} frames loaded")


    def input(self):
        if not self.attacking:
            keys = pygame.key.get_pressed()

            # movement input (клавиатура или левый стик геймпада)
            # Сначала сбрасываем направление
            self.direction.x = 0
            self.direction.y = 0

            # Клавиатура
            if keys[pygame.K_UP] or keys[pygame.K_w]:  # W или стрелка вверх
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:  # S или стрелка вниз
                self.direction.y = 1
                self.status = 'down'

            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:  # D или стрелка вправо
                self.direction.x = 1
                self.status = 'right'
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]:  # A или стрелка влево
                self.direction.x = -1
                self.status = 'left'

            # Левый стик геймпада
            if self.joystick:
                # Ось X (горизонтальное движение)
                axis_x = self.joystick.get_axis(0)
                # Ось Y (вертикальное движение)
                axis_y = self.joystick.get_axis(1)

                # Добавляем мертвую зону (dead zone), чтобы избежать случайных движений
                dead_zone = 0.2
                if abs(axis_x) > dead_zone:
                    self.direction.x = axis_x
                    self.status = 'right' if axis_x > 0 else 'left'
                if abs(axis_y) > dead_zone:
                    self.direction.y = axis_y
                    self.status = 'down' if axis_y > 0 else 'up'

            # Нормализация направления (чтобы скорость не увеличивалась при диагональном движении)
            if self.direction.x != 0 and self.direction.y != 0:
                magnitude = (self.direction.x ** 2 + self.direction.y ** 2) ** 0.5
                self.direction.x /= magnitude
                self.direction.y /= magnitude

            # attack input (пробел, левая кнопка мыши или кнопка X на геймпаде)
            if (keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0] or
                    (self.joystick and self.joystick.get_button(2))):  # Кнопка X (Button 2)
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()
                self.create_attack()
                # print('attack')

            # magic input (LCTRL, правая кнопка мыши или кнопка Y на геймпаде)
            if (keys[pygame.K_LCTRL] or pygame.mouse.get_pressed()[2] or
                    (self.joystick and self.joystick.get_button(3))):  # Кнопка Y (Button 3)
                self.attacking = True
                self.attack_time = pygame.time.get_ticks()
                style = list(magic_data.keys())[self.magic_index]
                strength = list(magic_data.values())[self.magic_index]['strength'] + self.stats['magic']
                cost = list(magic_data.values())[self.magic_index]['cost']
                self.create_magic(style, strength, cost)
                # print('magic')

            # Переключение оружия (Q или D-Pad вверх)
            if (keys[pygame.K_q] or (self.joystick and self.joystick.get_hat(0)[1] == 1)) and self.can_switch_weapon:
                self.can_switch_weapon = False
                self.weapon_switch_time = pygame.time.get_ticks()
                self.weapon_index = (self.weapon_index + 1) % len(weapon_data)
                self.weapon = list(weapon_data.keys())[self.weapon_index]

            # Переключение магии (E или D-Pad вниз)
            if (keys[pygame.K_e] or (self.joystick and self.joystick.get_hat(0)[1] == -1)) and self.can_switch_magic:
                self.can_switch_magic = False
                self.magic_switch_time = pygame.time.get_ticks()
                self.magic_index = (self.magic_index + 1) % len(magic_data)
                self.magic = list(magic_data.keys())[self.magic_index]

    def get_status(self):

        #idle status
        if self.direction.x == 0 and self.direction.y == 0:
            if not 'idle' in self.status and not 'attack' in self.status:
                self.status = self.status + '_idle'

        if self.attacking:
            self.direction.x = 0
            self.direction.y = 0
            if not 'attack' in self.status:
                if 'idle' in self.status:
                    self.status.replace('_idle','_attack')
                else:
                    self.status = self.status + '_attack'
        else:
            if 'attack' in self.status:
                self.status = self.status.replace('_attack','')

    def move(self,speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        self.hitbox.x += self.direction.x * speed
        self.collusion('horizontal')
        self.hitbox.y += self.direction.y * speed
        self.collusion('vertical')
        self.rect.center = self.hitbox.center

    def collusion(self,direction):
        if direction == 'horizontal':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    if self.direction.x > 0: # moving right
                        self.hitbox.right = sprite.hitbox.left
                    if self.direction.x < 0: # moving left
                        self.hitbox.left = sprite.hitbox.right

        if direction == 'vertical':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    if self.direction.y > 0: # moving down
                        self.hitbox.bottom = sprite.hitbox.top
                    if self.direction.y < 0: # moving up
                        self.hitbox.top = sprite.hitbox.bottom

    def cooldowns(self):
        current_time = pygame.time.get_ticks()

        if self.attacking:
            if current_time - self.attack_time >= self.attack_cooldown:
                self.attacking = False
                self.destroy_attack()

        if not self.can_switch_weapon:
            if current_time - self.weapon_switch_time >= self.switch_duration_cooldown:
                self.can_switch_weapon = True

        if not self.can_switch_magic:
            if current_time - self.magic_switch_time >= self.switch_duration_cooldown:
                self.can_switch_magic = True

    def animate(self):
        animation = self.animations[self.status]

        #loop over the frame index
        self.frame_index += self.animation_speed
        if self.frame_index >= len(animation):
            self.frame_index = 0

        # set the image
        self.image = animation[int(self.frame_index)]
        self.rect = self.image.get_rect(center = self.hitbox.center)

    def update(self):
        self.input()
        self.cooldowns()
        self.get_status()
        self.animate()
        self.move(self.speed)