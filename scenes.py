import pygame
import utilities
import geometry as geo
import colors
import numpy as np
import time
import copter
import driving
from collections import defaultdict

class SceneBase:
    def __init__(self):
        self.next = self
        self.initialized = False

    # only needs to be called once throughout main loop
    def initGraphics(self, screen):
        self.screen = screen
        self.initialized = True

    def ProcessInput(self, events, pressed_keys):
        print("uh-oh, you didn't override this in the child class")

    def Update(self):
        print("uh-oh, you didn't override this in the child class")

    def Render(self):
        print("uh-oh, you didn't override this in the child class")

    def SwitchToScene(self, next_scene):
        self.next = next_scene

    def Terminate(self):
        self.SwitchToScene(None)


class Start(SceneBase):
    BUTTON_DELAY = 0.15

    def __init__(self):
        SceneBase.__init__(self)

        self.options = ['Drive', 'Copter', 'Test', 'Quit']
        self.buttons = pygame.sprite.Group()
        self.startTime = time.time()

    def initGraphics(self, screen):
        SceneBase.initGraphics(self, screen)

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        font = pygame.font.Font('freesansbold.ttf', 20)

        for i, option in enumerate(self.options):
            rect = pygame.Rect(int(screenWidth / 2) - 50,
                               int(screenHeight / 2) - 100 + i * 50, 100, 30)
            passive_color = colors.BLACK
            active_color = colors.RED

            if i == 0:
                def action():
                    self.SwitchToScene(DrivingScene())
            elif i == 1:
                def action():
                    self.SwitchToScene(CopterScene())
            elif i == 2:
                def action():
                    self.SwitchToScene(TestScene())
            elif i == 3:
                def action():
                    self.Terminate()

            button = Button(rect, action, font, active_color, option,
                            colors.WHITE, passive_color, option, colors.WHITE)

            self.buttons.add(button)

    def ProcessInput(self, events, pressed_keys):
        pass

    def Update(self):
        if time.time() - self.startTime > self.BUTTON_DELAY:
            self.buttons.update()

    def Render(self):
        self.screen.fill(colors.WHITE)
        self.buttons.draw(self.screen)
        pygame.display.flip()


class Button(pygame.sprite.Sprite):
    def __init__(self, rect, action, font, active_color, active_text, active_textcolor, passive_color, passive_text, passive_textcolor):
        # Call the parent class (Sprite) constructor
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.Surface((rect[2], rect[3]))

        self.rect = rect

        self.font = font

        self.action = action

        self.active_color = active_color
        self.active_text = active_text
        self.active_textcolor = active_textcolor
        self.passive_color = passive_color
        self.passive_text = passive_text
        self.passive_textcolor = passive_textcolor

    def update(self):
        mouseX, mouseY = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()[0]

        if self.rect.x <= mouseX <= self.rect.x + self.rect.w \
                and self.rect.y <= mouseY <= self.rect.y + self.rect.h:
            self.image.fill(self.active_color)
            self.renderButtonText(self.active_text, self.active_textcolor)

            if pressed:
                self.action()
        else:
            self.image.fill(self.passive_color)
            self.renderButtonText(self.passive_text, self.passive_textcolor)

    def renderButtonText(self, text, color):
        textsurf = self.font.render(text, True, color)
        textrect = textsurf.get_rect()
        # Put text in the middle of button
        textrect.left = self.rect.width/2 - textrect.width/2
        textrect.top = self.rect.height/2 - textrect.height/2
        self.image.blit(textsurf, textrect)


class CheckExit(SceneBase):
    def __init__(self, paused):
        SceneBase.__init__(self)
        self.next = self
        self.paused = paused
        self.options = ["Yes", "No"]
        self.buttons = pygame.sprite.Group()

    # only needs to be called once throughout main loop
    def initGraphics(self, screen):
        SceneBase.initGraphics(self, screen)
        self.screen = self.paused.screen
        self.background = pygame.Surface([self.screen.get_width(),
                                         self.screen.get_height()],
                                         flags=pygame.SRCALPHA)
        self.background.fill([255, 255, 255, 180])  # translucent white bg
        self.screen.blit(self.background, self.background.get_rect())
        self.warningText = pygame.font.SysFont('Arial', 25)
        font = pygame.font.Font('freesansbold.ttf', 20)

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        for i, option in enumerate(self.options):
            rect = pygame.Rect(int(screenWidth / 2) - 50,
                               int(screenHeight / 2 - 75) + i * 50,
                               100, 30)
            passive_color = colors.BLACK
            active_color = colors.RED

            if i == 0:
                def action():
                    self.SwitchToScene(Start())
            else:
                def action():
                    self.SwitchToScene(self.paused)
                    self.paused.next = self.paused

            button = Button(rect, action, font, active_color, option, colors.WHITE, passive_color, option, colors.WHITE)

            self.buttons.add(button)

    def ProcessInput(self, events, pressed_keys):
        pass

    def Update(self):
        self.buttons.update()

    def Render(self):
        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h
        promptSurf = self.warningText.render("Quit without saving?",
                                             True, (0, 0, 0))
        promptRect = promptSurf.get_rect()
        promptRect.center = screenWidth / 2, 50
        self.screen.blit(promptSurf, promptRect)

        self.buttons.draw(self.screen)
        pygame.display.flip()

    def SwitchToScene(self, next_scene):
        super().SwitchToScene(next_scene)
        if isinstance(next_scene, TestScene):
            next_scene.starttime = time.time()


class Pause(SceneBase):
    def __init__(self, paused):
        SceneBase.__init__(self)
        self.next = self
        self.paused = paused
        self.options = ["Resume", "Quit"]
        self.buttons = pygame.sprite.Group()

    # only needs to be called once throughout main loop
    def initGraphics(self, screen):
        SceneBase.initGraphics(self, screen)
        self.screen = self.paused.screen
        self.background = pygame.Surface([self.screen.get_width(),
                                         self.screen.get_height()],
                                         flags=pygame.SRCALPHA)
        self.background.fill([255, 255, 255, 180])  # translucent white bg
        self.screen.blit(self.background, self.background.get_rect())
        self.pauseText = pygame.font.SysFont('Arial', 25)
        font = pygame.font.Font('freesansbold.ttf', 20)

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        for i, option in enumerate(self.options):
            rect = pygame.Rect(int(screenWidth / 2) - 50,
                               int(screenHeight / 2) + i * 50, 100, 30)
            passive_color = colors.BLACK
            active_color = colors.RED

            if i == 0:
                def action():
                    self.SwitchToScene(self.paused)
                    self.paused.next = self.paused
            else:
                def action():
                    self.SwitchToScene(Start())

            button = Button(rect, action, font, active_color, option, colors.WHITE, passive_color, option, colors.WHITE)

            self.buttons.add(button)

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                alt_pressed = pressed_keys[pygame.K_LALT] or \
                              pressed_keys[pygame.K_RALT]
                if event.key == pygame.K_p:
                    self.SwitchToScene(self.paused)
                    self.paused.next = self.paused


    def Update(self):
        self.buttons.update()

    def Render(self):
        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h
        promptSurf = self.pauseText.render("PAUSED", True, (0, 0, 0))
        promptRect = promptSurf.get_rect()
        promptRect.center = screenWidth/2, 50
        self.screen.blit(promptSurf, promptRect)

        self.buttons.draw(self.screen)
        pygame.display.flip()

    def SwitchToScene(self, next_scene):
        super().SwitchToScene(next_scene)
        if isinstance(next_scene, TestScene):
            next_scene.starttime = time.time()


class DrivingScene(SceneBase):
    LAP_LIMIT = 3  # number of laps to complete game
    SAVE_FILE = "racing-time.save"  # save location
    CPU_COLLISION_RADIUS = 20  # CPU collision radius
    CPU_TARGET_RADIUS = 10  # CPU target radius to randomize over
    START_COUNTDOWN = 3  # countdown before starting

    def __init__(self):
        SceneBase.__init__(self)
        # initialize RNG
        self.rng = np.random.default_rng()

        self.started = False  # whether race has begun
        self.bestTime = self.loadScore(self.SAVE_FILE)
        self.finished = []  # cars that finished by rank
        self.startTime = time.time()

    # only needs to be called once throughout main loop
    def initGraphics(self, screen):
        SceneBase.initGraphics(self, screen)

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        self.cars = utilities.DrawGroup()
        self.player = driving.Car((10, screenHeight / 2), 90, colors.RED, 'Red (You)')
        self.cars.add(self.player)
        cpu = driving.Car((50, screenHeight / 2), 90, colors.BLUE, 'Blue', isCPU=True)
        self.cars.add(cpu)
        cpu = driving.Car((50, screenHeight / 2), 90, colors.GREEN, 'Green', isCPU=True)
        self.cars.add(cpu)
        cpu = driving.Car((50, screenHeight / 2), 90, colors.YELLOW, 'Yellow', isCPU=True)
        self.cars.add(cpu)
        self.spaceoutCars(0, 0.2 * screenWidth / 2, True)

        self.powerups = utilities.DrawGroup()

        self.terrain = utilities.DrawGroup()
        mid_grass = driving.Grass((screenWidth / 2, screenHeight / 2),
                          0.8 * screenWidth, 0.8 * screenHeight)
        self.terrain.add(mid_grass)
        mid_barrier = driving.Barrier((screenWidth / 2, screenHeight / 2),
                              0.75 * screenWidth, 0.75 * screenHeight)
        self.terrain.add(mid_barrier)

        checkpointTopLeft = driving.Checkpoint((0.125 * screenWidth / 2,
                                        0.125 * screenHeight / 2),
                                       0.125 * screenWidth,
                                       0.125 * screenHeight, True)
        self.terrain.add(checkpointTopLeft)
        checkpointTopRight = driving.Checkpoint((screenWidth - 0.125 * screenWidth / 2,
                                        0.125 * screenHeight / 2),
                                        0.125 * screenWidth,
                                        0.125 * screenHeight, False)
        self.terrain.add(checkpointTopRight)
        checkpointBottomRight = driving.Checkpoint((screenWidth - 0.125 * screenWidth / 2,
                                           screenHeight - 0.125 * screenHeight / 2),
                                           0.125 * screenWidth,
                                           0.125 * screenHeight, True)
        self.terrain.add(checkpointBottomRight)
        checkpointBottomLeft = driving.Checkpoint((0.125 * screenWidth / 2,
                                          screenHeight - 0.125 * screenHeight / 2),
                                          0.125 * screenWidth,
                                          0.125 * screenHeight, False)
        self.terrain.add(checkpointBottomLeft)
        finishline = driving.FinishLine((0.125 * screenWidth / 2,
                                screenHeight / 2),
                                0.125 * screenWidth,
                                10)
        self.terrain.add(finishline)

        self.checkpoints = [finishline, checkpointTopLeft, checkpointTopRight,
                            checkpointBottomRight, checkpointBottomLeft]

        self.lapText = pygame.font.Font('freesansbold.ttf', 20)
        self.timeText = pygame.font.Font('freesansbold.ttf', 20)
        self.rankText = pygame.font.Font('freesansbold.ttf', 20)
        self.startText = pygame.font.Font('freesansbold.ttf', 20)

        buttonRect = pygame.Rect(int(screenWidth / 2) - 50,
                                 int(screenHeight / 2) + 100, 100, 30)
        buttonFont = pygame.font.Font('freesansbold.ttf', 20)

        def action():
            self.SwitchToScene(Start())

        self.quitButton = Button(buttonRect, action, buttonFont,
                                 colors.RED, "Quit", colors.WHITE,
                                 colors.BLACK, "Quit", colors.WHITE)

    def spaceoutCars(self, lb, ub, horizontal=True):
        ncars = len(self.cars)
        for i, car in enumerate(self.cars):
            newpos = lb + (i + 1) * (ub - lb) / (ncars + 1)
            if horizontal:
                car.rect.left = newpos - car.rect.width / 2
            else:
                car.rect.top = newpos - car.rect.height / 2

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                alt_pressed = pressed_keys[pygame.K_LALT] or \
                              pressed_keys[pygame.K_RALT]
                if event.key == pygame.K_p:
                    self.SwitchToScene(Pause(self))
                if event.key == pygame.K_SPACE:
                    self.player.activatePower()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.player.deactivatePower()

    def Update(self):
        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        if not self.started:
            if time.time() - self.startTime > self.START_COUNTDOWN:
                self.started = True
                self.startTime = time.time()
            return

        self.getPowerupsFromCheckpoints()

        # check is car is within radius of checkpoint's center
        def collideCPU(car, checkpoint):
            carPos = geo.Vector2D(*car.rect.center)
            checkpointPos = geo.Vector2D(*checkpoint.rect.center)
            dr = checkpointPos - carPos
            return dr.length() <= self.CPU_COLLISION_RADIUS

        for car in self.cars:
            self.drive(car)

            # Powerups collision
            powerupsHit = pygame.sprite.spritecollide(car,
                                                      self.powerups, True,
                                                      collided=pygame
                                                      .sprite.collide_rect)
            for power in powerupsHit:
                car.givePower(power)

            self.checkOutOfBounds(car, screenWidth, screenHeight)

            # Terrain collision
            if car.isCPU:
                # Check for smaller collision if CPU controlled
                terrainHit = pygame.sprite.spritecollide(car, self.terrain,
                                                         False,
                                                         collided=collideCPU)
            else:
                terrainHit = pygame.sprite.spritecollide(car, self.terrain,
                                                         False,
                                                         collided=pygame
                                                         .sprite.collide_rect)

            car.slowed = False  # by default, Car isn't slowed
            for terrain in terrainHit:
                if issubclass(type(terrain), driving.Checkpoint):
                    self.checkCheckpoints(car, terrain)
                elif type(terrain) is driving.Grass:
                    car.slowed = True
                elif type(terrain) is driving.Barrier:
                    self.checkBarrierCollision(car, terrain)

            if car not in self.finished and car.laps == self.LAP_LIMIT:
                if car == self.player:
                    self.Finish()

                self.finished.append(car)

        self.powerups.update()
        self.cars.update()
        self.terrain.update()

    def Render(self):
        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        self.screen.fill(colors.GRAY)
        self.terrain.draw(self.screen)
        self.powerups.draw(self.screen)
        self.cars.draw(self.screen)

        if not self.started:
            timeElapsed = time.time() - self.startTime
            timeLeft = self.START_COUNTDOWN - timeElapsed
            timeSurf = self.startText.render("Countdown: {0:.0f}"
                                             .format(np.ceil(timeLeft)),
                                             True, colors.WHITE)
            timeRect = timeSurf.get_rect()
            timeRect.center = screenWidth / 2, screenHeight / 2
            self.screen.blit(timeSurf, timeRect)
        else:
            if self.player not in self.finished:
                self.timeElapsed = time.time() - self.startTime
                lapSurf = self.lapText.render("Lap: {0}/{1}"
                                              .format(self.player.laps,
                                                      self.LAP_LIMIT),
                                              True, colors.WHITE)
                lapRect = lapSurf.get_rect()
                lapRect.center = screenWidth / 2, screenHeight / 2
                self.screen.blit(lapSurf, lapRect)

                self.drawCrossHairs()
            else:
                timeSurf = self.timeText.render("Best-time: {0:.3f} seconds"
                                                .format(self.bestTime),
                                                True, colors.WHITE)
                timeRect = timeSurf.get_rect()
                timeRect.center = screenWidth / 2, screenHeight / 2
                self.screen.blit(timeSurf, timeRect)

                self.screen.blit(self.quitButton.image, self.quitButton.rect)

            timeSurf = self.timeText.render("Time: {0:.3f} seconds"
                                            .format(self.timeElapsed),
                                            True, colors.WHITE)
            timeRect = timeSurf.get_rect()
            timeRect.center = screenWidth / 2, screenHeight / 2 - 50
            self.screen.blit(timeSurf, timeRect)

            if len(self.finished) > 0:
                ranks = ["{0}: {1}".format(i + 1, car.name)
                         for (i, car) in enumerate(self.finished)]
                rankStr = ", ".join(ranks)
                rankSurf = self.rankText.render(rankStr,
                                                True, colors.WHITE)
                fullRanks = ["{0}, {1}".format(i, car.name)
                             for (i, car) in enumerate(self.cars.sprites())]
                fullRankStr = ", ".join(fullRanks)
                fullRankSurf = self.rankText.render(fullRankStr,
                                                    True, colors.WHITE)
                fullRankRect = fullRankSurf.get_rect()
                rankRect = rankSurf.get_rect()
                rankRect.center = screenWidth / 2, screenHeight / 2 + 50
                rankRect.left = screenWidth / 2 - fullRankRect.width / 2
                self.screen.blit(rankSurf, rankRect)

        pygame.display.flip()

    def drawCrossHairs(self):
        mouse = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()

        offset = 5
        length = 10
        if pressed[0]:
            pygame.draw.line(self.screen,
                             colors.GREEN,
                             (mouse[0], mouse[1] - offset),
                             (mouse[0], mouse[1] - length))
            pygame.draw.line(self.screen,
                             colors.GREEN,
                             (mouse[0], mouse[1] + offset),
                             (mouse[0], mouse[1] + length))
            pygame.draw.line(self.screen,
                             colors.GREEN,
                             (mouse[0] - offset, mouse[1]),
                             (mouse[0] - length, mouse[1]))
            pygame.draw.line(self.screen,
                             colors.GREEN,
                             (mouse[0] + offset, mouse[1]),
                             (mouse[0] + length, mouse[1]))
        elif pressed[2]:
            pygame.draw.line(self.screen,
                             colors.RED,
                             (mouse[0], mouse[1] - offset),
                             (mouse[0], mouse[1] - length))
            pygame.draw.line(self.screen,
                             colors.RED,
                             (mouse[0], mouse[1] + offset),
                             (mouse[0], mouse[1] + length))
            pygame.draw.line(self.screen,
                             colors.RED,
                             (mouse[0] - offset, mouse[1]),
                             (mouse[0] - length, mouse[1]))
            pygame.draw.line(self.screen,
                             colors.RED,
                             (mouse[0] + offset, mouse[1]),
                             (mouse[0] + length, mouse[1]))
        else:
            pygame.draw.line(self.screen,
                             colors.BLACK,
                             (mouse[0], mouse[1] - offset),
                             (mouse[0], mouse[1] - length))
            pygame.draw.line(self.screen,
                             colors.BLACK,
                             (mouse[0], mouse[1] + offset),
                             (mouse[0], mouse[1] + length))
            pygame.draw.line(self.screen,
                             colors.BLACK,
                             (mouse[0] - offset, mouse[1]),
                             (mouse[0] - length, mouse[1]))
            pygame.draw.line(self.screen,
                             colors.BLACK,
                             (mouse[0] + offset, mouse[1]),
                             (mouse[0] + length, mouse[1]))

    def checkBarrierCollision(self, car, barrier):
        if car.rect.bottom > barrier.rect.top and car.rect.top < barrier.rect.bottom \
            and (car.rect.right <= barrier.rect.left + car.v.x or car.rect.left >= barrier.rect.right + car.v.x):
            if car.v.x > 0:
                car.rect.right = barrier.rect.left
            if car.v.x < 0:
                car.rect.left = barrier.rect.right
        if car.rect.right > barrier.rect.left and car.rect.left < barrier.rect.right \
            and (car.rect.bottom <= barrier.rect.top + car.v.y or car.rect.top >= barrier.rect.bottom + car.v.y):
            if car.v.y > 0:
                car.rect.bottom = barrier.rect.top
            if car.v.y < 0:
                car.rect.top = barrier.rect.bottom

    def checkOutOfBounds(self, car, screenWidth, screenHeight):
        if car.rect.top < 0:
            car.rect.top = 0
        if car.rect.bottom > screenHeight:
            car.rect.bottom = screenHeight
        if car.rect.left < 0:
            car.rect.left = 0
        if car.rect.right > screenWidth:
            car.rect.right = screenWidth

    def checkCheckpoints(self, car, checkpoint):
        # current checkpoint
        checkpointIndex = self.checkpoints.index(checkpoint)
        # correct previous checkpoint
        lastCheckpointIndex = (checkpointIndex - 1) \
            % len(self.checkpoints)
        # check that this terrain checkpoint is the correct checkpoint
        if car.checkpoint == lastCheckpointIndex:
            # if start is reached correctly
            if(car.laps < self.LAP_LIMIT and checkpointIndex == 0):
                car.laps += 1
            car.checkpoint = checkpointIndex

    def getPowerupsFromCheckpoints(self):
        for checkpoint in self.checkpoints:
            powerupsInside = pygame.sprite.spritecollide(checkpoint,
                                                         self.powerups,
                                                         False,
                                                         collided=pygame.sprite.collide_rect)
            # only add it if there's not already one inside
            if len(powerupsInside) == 0:
                # adds the generated powerup if available
                powerup = checkpoint.getPowerup()
                if powerup:
                    self.powerups.add(powerup)

    def drive(self, car):
        if self.player not in self.finished and car == self.player:
            self.drivePlayer()
        else:
            self.driveCPU(car)

    def drivePlayer(self):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        mousePos = geo.Vector2D(*mouse)
        # follow mouse drag
        if click[0]:  # left click
            self.player.driveTowards(mousePos)
        elif click[2]:  # right click
            self.player.driveAwayFrom(mousePos)
        else:
            self.player.idle()

    def driveCPU(self, car):
        nextCheckpointIndex = (car.checkpoint + 1)\
            % len(self.checkpoints)
        nextCheckpoint = self.checkpoints[nextCheckpointIndex]
        # randomize target around a circle
        target = geo.Vector2D(*nextCheckpoint.rect.center)
        target += geo.Vector2D.create_from_angle(self.rng.random() * 2 * np.pi,
                                                 self.rng.random() * self.CPU_TARGET_RADIUS)
        car.driveTowards(target)
        self.quitButton.update()

    def saveScore(self, filename):
        with open(filename, 'w') as f:
            f.write("Best-time,{0:.3f}".format(self.bestTime))

    def loadScore(self, filename):
        try:
            with open(filename, 'r') as f:
                scoreline = f.readline()
                score = scoreline.split(',')[1]
        except (OSError, IndexError):
            score = np.inf

        return float(score)

    def Finish(self):
        self.player.isCPU = True
        if self.timeElapsed < self.bestTime:
            self.bestTime = self.timeElapsed
            self.saveScore(self.SAVE_FILE)


class CopterScene(SceneBase):
    GAP_FRACTION = 0.7  # the starting fraction of gap space
    GAP_CLEARANCE = 0.05  # how much clearance gap has between screen borders
    FLUCTUATION = 3  # how much the gap position fluctuates
    NARROWING_INTERVAL = 10  # how long before the gap narrows
    FLUCTUATION_INTERVAL = 5  # how long before gap increases fluctuation
    MAX_FLUCTUATION = 15  # maximum amount of fluctuation
    EXPONENTIAL_GENERATORS = ['bats', 'obstacles', 'powerups', 'balloons']
    SPAWN_INTERVAL = {}
    SPAWN_INTERVAL['bats'] = 8
    SPAWN_INTERVAL['obstacles'] = 10
    SPAWN_INTERVAL['powerups'] = 12
    SPAWN_INTERVAL['balloons'] = 8
    SAVE_FILE = 'copter-score.save'  # save file name

    def __init__(self):
        SceneBase.__init__(self)
        self.fly = False
        self.rng = np.random.default_rng()
        self.starttime = time.time()
        self.lastnarrow = self.starttime
        self.lastfluct = self.starttime
        self.highscore = self.loadScore(self.SAVE_FILE)
        self.projectiles = utilities.DrawGroup()
        self.obstacles = utilities.DrawGroup()
        self.powerups = utilities.DrawGroup()
        self.explosions = utilities.DrawGroup()
        self.score = 0
        self.timeUntilGeneration = {generator: self.rng.exponential(self.SPAWN_INTERVAL[generator])
                                    for generator in self.EXPONENTIAL_GENERATORS}
        self.lastUpdateTime = defaultdict(lambda: self.starttime)

    def initGraphics(self, screen):
        SceneBase.initGraphics(self, screen)

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        self.copter = copter.Copter([screenWidth / 4, screenHeight / 2])

        self.walls = utilities.DrawGroup()
        self.generateWalls()

        self.scoreText = pygame.font.Font('freesansbold.ttf', 20)
        self.highscoreText = pygame.font.Font('freesansbold.ttf', 12)

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                alt_pressed = pressed_keys[pygame.K_LALT] or \
                              pressed_keys[pygame.K_RALT]
                if event.key == pygame.K_p:
                    self.SwitchToScene(Pause(self))

    def Update(self):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        spacebar = pygame.key.get_pressed()[pygame.K_SPACE]
        self.score = time.time() - self.starttime

        if self.score > self.highscore:
            self.highscore = self.score

        # fly if spacebar
        if spacebar:
            self.copter.fly()
        else:
            self.copter.drop()

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        self.checkOutOfBounds()

        self.checkCollisions()

        for wall in self.walls:
            # if wall goes out of bounds
            if wall.rect.right < 0:
                wall.kill()

                # create upper wall if the dead wall is upper
                new = self.generateWall(wall.rect.top == 0)
                self.walls.add(new)

        for generator in self.EXPONENTIAL_GENERATORS:
            # if time to generate is reached
            if self.timeUntilGeneration[generator] <= 0:
                self.spawn(generator)
            else:  # remove time from generator
                now = time.time()
                self.timeUntilGeneration[generator] -= now\
                    - self.lastUpdateTime[generator]
                self.lastUpdateTime[generator] = now

        for ob in self.obstacles:
            # if obstacle is a bat, fly the bat
            if type(ob) is copter.Bat:
                nearestWalls = []
                for wall in self.walls:
                    batX = ob.rect.x
                    wallX = wall.rect.x
                    if abs(batX - wallX) <= copter.Wall.WIDTH:
                        nearestWalls.append(wall)
                        if len(nearestWalls) == 2:
                            break
                if len(nearestWalls) > 0:
                    top, bottom = sorted(nearestWalls,
                                         key=lambda wall: wall.rect.y)
                    roof, ground = top.rect.bottom, bottom.rect.top
                    ob.fly(roof, ground)
            # if obstacle flies off-screen, delete it
            if self.isOutOfBounds(ob.rect):
                ob.kill()

        for pup in self.powerups:
            # if powerup flies off-screen, delete it
            if self.isOutOfBounds(pup.rect):
                pup.kill()

        # Powerups collision
        self.checkPowerupsHit()

        if click[0]:
            if self.copter.readyToShoot():
                bullet = self.copter.shootTowards(mouse)
                self.projectiles.add(bullet)

        for p in self.projectiles:
            # if projectile flies off-screen
            if self.isOutOfBounds(p.rect):
                p.kill()
            self.checkProjectileHit(p)

        self.copter.update()
        self.walls.update()
        self.obstacles.update()
        self.powerups.update()
        self.projectiles.update()
        self.explosions.update()

    def Render(self):
        self.screen.fill((255, 255, 255))
        self.copter.draw(self.screen)
        self.obstacles.draw(self.screen)
        self.powerups.draw(self.screen)
        self.walls.draw(self.screen)
        self.explosions.draw(self.screen)
        self.projectiles.draw(self.screen)

        scoreSurf = self.scoreText.render("Time: {0:.2f}".format(self.score), True, (0, 0, 0))
        scoreRect = scoreSurf.get_rect()
        scoreRect.left, scoreRect.top = 50, 50
        self.screen.blit(scoreSurf, scoreRect)

        scoreSurf = self.highscoreText.render("High-score: {0:.2f}".format(self.highscore), True, (0, 0, 0))
        scoreRect = scoreSurf.get_rect()
        scoreRect.left, scoreRect.top = 50, 75
        self.screen.blit(scoreSurf, scoreRect)

        self.drawCrossHairs()

        pygame.display.flip()

    def drawCrossHairs(self):
        mouse = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()

        offset = 5
        length = 10
        if pressed[0]:
            pygame.draw.line(self.screen,
                             colors.RED,
                             (mouse[0], mouse[1] - offset),
                             (mouse[0], mouse[1] - length))
            pygame.draw.line(self.screen,
                             colors.RED,
                             (mouse[0], mouse[1] + offset),
                             (mouse[0], mouse[1] + length))
            pygame.draw.line(self.screen,
                             colors.RED,
                             (mouse[0] - offset, mouse[1]),
                             (mouse[0] - length, mouse[1]))
            pygame.draw.line(self.screen,
                             colors.RED,
                             (mouse[0] + offset, mouse[1]),
                             (mouse[0] + length, mouse[1]))
        else:
            pygame.draw.line(self.screen,
                             colors.BLACK,
                             (mouse[0], mouse[1] - offset),
                             (mouse[0], mouse[1] - length))
            pygame.draw.line(self.screen,
                             colors.BLACK,
                             (mouse[0], mouse[1] + offset),
                             (mouse[0], mouse[1] + length))
            pygame.draw.line(self.screen,
                             colors.BLACK,
                             (mouse[0] - offset, mouse[1]),
                             (mouse[0] - length, mouse[1]))
            pygame.draw.line(self.screen,
                             colors.BLACK,
                             (mouse[0] + offset, mouse[1]),
                             (mouse[0] + length, mouse[1]))

    def EndGame(self):
        self.saveScore(self.SAVE_FILE)
        self.SwitchToScene(Start())

    def saveScore(self, filename):
        with open(filename, 'w') as f:
            f.write("High-score,{0:.2f}".format(self.highscore))

    def loadScore(self, filename):
        try:
            with open(filename, 'r') as f:
                scoreline = f.readline()
                score = scoreline.split(',')[1]
        except (OSError, IndexError):
            score = 0
            print("No save data found.")

        return float(score)

    def checkPowerupsHit(self):
        powerupsHit = pygame.sprite.spritecollide(self.copter,
                                                  self.powerups, True,
                                                  collided=pygame.sprite.collide_rect)
        for power in powerupsHit:
            self.copter.givePower(power)

    def checkProjectileHit(self, projectile):
        if type(projectile) is not copter.Laser:
            collided_objects = pygame.sprite.spritecollide(projectile, self.walls, False, collided=pygame.sprite.collide_rect)
            for obj in collided_objects:
                projectile.kill()

        collided_objects = pygame.sprite.spritecollide(projectile, self.obstacles, False, collided=projectile.collided)
        for obj in collided_objects:
            dead = obj.hurt()
            projectile.kill()
            if dead:
                self.starttime -= obj.AWARD

    def spawn(self, generator):
        if generator == 'obstacles':
            self.spawnObstacle()
        elif generator == 'bats':
            self.spawnBat()
        elif generator == 'powerups':
            self.spawnPowerup()
        elif generator == 'balloons':
            self.spawnBalloon()
        self.timeUntilGeneration[generator] = self.rng.exponential(
            self.SPAWN_INTERVAL[generator])

    def spawnObstacle(self):
        gap_pos = self.gap_pos[-1]
        gap_height = self.gap_lastheight
        roof, ground = gap_pos - gap_height / 2,\
            gap_pos + gap_height / 2
        height = copter.Obstacle.MIN_HEIGHT + self.rng.random() * 0.4 * gap_height
        top = self.rng.random() * (gap_height - height) + roof
        obstacle = copter.Obstacle(top, height)
        self.obstacles.add(obstacle)

    def spawnBat(self):
        gap_pos = self.gap_pos[-1]
        gap_height = self.gap_lastheight
        roof, ground = gap_pos - gap_height / 2,\
            gap_pos + gap_height / 2
        y = self.rng.random() * 0.8 * (gap_height - 32) + 1.1 * roof
        bat = copter.Bat(y)
        self.obstacles.add(bat)
        self.SPAWN_INTERVAL['bats'] = max(5,
                                          self.SPAWN_INTERVAL['bats'] * 0.95)

    def spawnBalloon(self):
        gap_pos = self.gap_pos[-1]
        gap_height = self.gap_lastheight
        roof, ground = gap_pos - gap_height / 2,\
            gap_pos + gap_height / 2
        y = self.rng.random() * 0.6 * gap_height + 1.4 * roof
        balloon = copter.Balloon(y)
        self.obstacles.add(balloon)
        self.SPAWN_INTERVAL['balloons'] = max(5,
                                              self.SPAWN_INTERVAL['balloons'] * 0.95)

    def spawnPowerup(self):
        gap_pos = self.gap_pos[-1]
        gap_height = self.gap_lastheight
        roof, ground = gap_pos - gap_height / 2,\
            gap_pos + gap_height / 2
        top = self.rng.random() * 0.6\
            * (gap_height - copter.Powerup.SIDE_LENGTH)\
            + roof + 0.2 * gap_height
        powerupType = copter.PowerupType(int(self.rng.random() * copter.PowerupType.NUMBER_POWERUPS.value))
        powerup = copter.Powerup(top, powerupType)
        self.powerups.add(powerup)

    def generateWalls(self):
        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h
        # number of walls
        N = int(np.ceil(screenWidth / copter.Wall.WIDTH)) + 3

        # generate walls
        gap_height = self.GAP_FRACTION * screenHeight
        gap_pos = self.rng.random() \
            * (screenHeight * (1 - 2 * self.GAP_CLEARANCE - self.GAP_FRACTION)) \
            + screenHeight * (self.GAP_CLEARANCE + 0.5 * self.GAP_FRACTION)

        self.gap_lastheight = gap_height
        self.gap_heights = np.ones(N) * gap_height
        self.gap_pos = np.zeros(N)
        self.gap_pos[0] = gap_pos

        gap_roof = round(gap_pos - gap_height / 2)
        gap_floor = round(gap_pos + gap_height / 2)

        for i in range(1, N):
            gap_pos += self.FLUCTUATION * self.rng.standard_normal()
            gap_pos = utilities.bound(
                gap_height / 2 + self.GAP_CLEARANCE * screenHeight,
                gap_pos,
                (1 - self.GAP_CLEARANCE) * screenHeight - gap_height / 2)

            self.gap_pos[i] = gap_pos

        for i in range(N - 1):
            last_gap_roof = gap_roof
            last_gap_floor = gap_floor
            gap_roof = round(self.gap_pos[i] - self.gap_heights[i] / 2)
            gap_floor = round(self.gap_pos[i] + self.gap_heights[i] / 2)
            next_gap_roof = round(self.gap_pos[i+1] - self.gap_heights[i+1] / 2)
            next_gap_floor = round(self.gap_pos[i+1] + self.gap_heights[i+1] / 2)

            NW, NE, SW, SE = 0, 0,\
                round((last_gap_roof + gap_roof) / 2), round((gap_roof + next_gap_roof) / 2)
            top = copter.Wall(NW, NE, SE, SW)
            NW, NE, SW, SE = round((last_gap_floor + gap_floor) / 2),\
                round((gap_floor + next_gap_floor) / 2),\
                screenHeight, screenHeight
            bottom = copter.Wall(NW, NE, SE, SW)
            x = i * copter.Wall.WIDTH
            top.rect.x = x
            bottom.rect.x = x
            if abs(x - self.copter.rect.x) < copter.Wall.WIDTH:
                self.copterIndex = i
            self.walls.add(top)
            self.walls.add(bottom)

    def generateWall(self, top=True):
        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        if top:
            if (time.time() - self.lastnarrow) >= self.NARROWING_INTERVAL:
                self.gap_lastheight = max(0.95 * self.gap_lastheight, 3 * self.copter.rect.height)
                self.gap_heights[0] = self.gap_lastheight
                self.lastnarrow = time.time()
            if (time.time() - self.lastfluct) >= self.FLUCTUATION_INTERVAL:
                self.FLUCTUATION = min(self.FLUCTUATION + 1, self.MAX_FLUCTUATION)
                self.lastfluct = time.time()
            self.gap_pos[0] = self.gap_pos[-1] + self.FLUCTUATION * self.rng.standard_normal()
            self.gap_pos[0] = utilities.bound(self.gap_lastheight / 2 + self.GAP_CLEARANCE * screenHeight,
                                 self.gap_pos[0],
                                 (1 - self.GAP_CLEARANCE) * screenHeight - self.gap_lastheight / 2)
            self.gap_heights[0] = self.gap_lastheight
            # roll gap arrays
            self.gap_pos = np.roll(self.gap_pos, -1)
            self.gap_heights = np.roll(self.gap_heights, -1)

        def roof(index):
            return round(self.gap_pos[index] - self.gap_heights[index] / 2)

        def floor(index):
            return round(self.gap_pos[index] + self.gap_heights[index] / 2)
        last_gap_roof = roof(-3)
        last_gap_floor = floor(-3)
        gap_roof = roof(-2)
        gap_floor = floor(-2)
        next_gap_roof = roof(-1)
        next_gap_floor = floor(-1)

        if top:
            NW, NE, SW, SE = 0, 0,\
                round((last_gap_roof + gap_roof) / 2),\
                round((gap_roof + next_gap_roof) / 2)
        else:
            NW, NE, SW, SE = round((last_gap_floor + gap_floor) / 2),\
                round((gap_floor + next_gap_floor) / 2),\
                screenHeight, screenHeight
        new = copter.Wall(NW, NE, SE, SW)

        return new

    def checkOutOfBounds(self):
        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h
        # if ceiling is hit
        if self.copter.rect.top < 0:
            self.EndGame()

        # if floor is hit
        if self.copter.rect.bottom > screenHeight:
            self.EndGame()

    def checkCollisions(self):
        for wall in pygame.sprite.spritecollide(self.copter, self.walls,
                                                False, collided=pygame.sprite.collide_mask):
            if not self.copter.invincible():
                self.takeCopterLife()
            break

        for ob in pygame.sprite.spritecollide(self.copter, self.obstacles,
                                              False, collided=pygame.sprite.collide_rect):
            if self.copter.hasPower(copter.PowerupType.SHIELD):
                ob.destroy()
            else:
                if not self.copter.invincible():
                    self.takeCopterLife()
            break

    def takeCopterLife(self):
        dead = self.copter.hurt()
        explosion = copter.Explosion(self.copter.rect.center)
        self.explosions.add(explosion)
        if dead:
            self.EndGame()
        else:
            self.copter.rect.top = self.gap_pos[self.copterIndex]

    def isOutOfBounds(self, rect):
        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        return rect.left > screenWidth \
            or rect.right < 0 \
            or rect.top > screenHeight \
            or rect.bottom < 0


class TestScene(SceneBase):
    DELAY = 0.1

    def __init__(self):
        SceneBase.__init__(self)
        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        self.ball = utilities.load_image('ball.png')
        self.ball.set_colorkey(colors.WHITE)
        self.ballrect = self.ball.get_rect()
        self.v = geo.Vector2D.zero()
        self.g = geo.Vector2D(0, 1)
        self.elasticity = 0.8
        self.friction = 0.1

        size = 20
        self.obj = pygame.Surface([size, size])
        self.obj.fill(colors.RED)
        self.objrect = pygame.Rect(screenWidth / 2,
                                   screenHeight / 2,
                                   size, size)
        self.hitLast = False

        self.starttime = time.time()

    def initGraphics(self, screen):
        SceneBase.initGraphics(self, screen)

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                alt_pressed = pressed_keys[pygame.K_LALT] or \
                              pressed_keys[pygame.K_RALT]
                if event.key == pygame.K_p:
                    self.SwitchToScene(Pause(self))

    def Update(self):
        if time.time() - self.starttime < self.DELAY:
            return

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        info = pygame.display.Info()
        screenWidth, screenHeight = info.current_w, info.current_h

        ballmask = pygame.mask.from_surface(self.ball)
        objmask = pygame.mask.from_surface(self.obj)
        x = self.objrect.x - self.ballrect.x
        y = self.objrect.y - self.ballrect.y
        dx = ballmask.overlap_area(objmask, (x + 1, y))\
            - ballmask.overlap_area(objmask, (x - 1, y))
        dy = ballmask.overlap_area(objmask, (x, y + 1))\
            - ballmask.overlap_area(objmask, (x, y - 1))
        normal = geo.Vector2D(dx, dy)
        hit = (normal != geo.Vector2D.zero())
        if hit:
            if not self.hitLast:
                self.hitLast = True
                self.v = -geo.Vector2D.reflect(self.v * self.elasticity,
                                               -normal)
                self.ballrect.move_ip(*self.v)
        else:
            self.hitLast = False
            # follow mouse drag
            if click[0]:
                currentPos = geo.Vector2D(*mouse)
                self.v = currentPos - self.lastPos
                self.lastPos = currentPos
                self.ballrect.center = mouse
                if self.ballrect.left < 0:
                    self.ballrect.left = 0
                if self.ballrect.right > screenWidth:
                    self.ballrect.right = screenWidth
                if self.ballrect.top < 0:
                    self.ballrect.top = 0
                if self.ballrect.bottom > screenHeight:
                    self.ballrect.bottom = screenHeight
            else:
                self.lastPos = geo.Vector2D(*mouse)
                self.v += self.g
                self.ballrect.move_ip(*self.v)
                if self.ballrect.left < 0:
                    self.v.x = -self.v.x * self.elasticity
                    self.ballrect.left = 0
                if self.ballrect.right > screenWidth:
                    self.v.x = -self.v.x * self.elasticity
                    self.ballrect.right = screenWidth
                if self.ballrect.top < 0:
                    self.v.y = -self.v.y * self.elasticity
                    self.ballrect.top = 0
                if self.ballrect.bottom > screenHeight:
                    self.v.y = int(-self.v.y * self.elasticity)
                    if self.v.x > 0:
                        self.v.x = int(self.v.x - self.friction)
                    elif self.v.x < 0:
                        self.v.x = int(self.v.x + self.friction)

                    self.ballrect.bottom = screenHeight

    def Render(self):
        # For the sake of brevity, the title scene is a blank black screen
        self.screen.fill(colors.WHITE)

        self.screen.blit(self.ball, self.ballrect)
        self.screen.blit(self.obj, self.objrect)
        pygame.display.flip()
