from kivy.app import App
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.animation import Animation
from random import randint
import sqlite3, json, time


class Ball(Image):
    def __init__(self):
        super().__init__()
        wind = str(Window.size)
        self.wid = int(wind[1:wind.find(',')])
        self.hei = int(wind[wind.find(' ') + 1:-1])
        self.razm = self.wid / self.hei
        self.source = 'ball0.png'
        self.size_hint = (0.02, 0.02 * self.razm)
        self.pos = (0.49 * self.wid, 0.025 * self.wid)
        self.last_move = ''
        self.angle = 1
        self.speed = 500
        self.bust = 0


class MyApp(App):
    def __init__(self):
        super().__init__()
        wind = str(Window.size)
        self.wid = int(wind[1:wind.find(',')])
        self.hei = int(wind[wind.find(' ') + 1:-1])
        self.razm = self.wid / self.hei
        # self.platform = Button(background_color=[1, 1, 1, 1], background_down='', background_normal='',
        #                        size_hint=(0.1, 0.02 * self.razm), pos=(0.45 * self.wid, 0))
        self.platform = Image(source='platform0.png', size_hint=(0.1, 0.02 * self.razm), pos=(0.45 * self.wid, 0))
        self.platform.bind(on_touch_move=self.move)
        # self.ball = Button(background_down='ball.png', background_normal='ball.png',
        #                    size_hint=(0.01, 0.01 * self.razm), pos=(0.495 * self.wid, 0.035 * self.wid))
        # self.balls = [Image(source='ball0.png', size_hint=(0.02, 0.02 * self.razm),
        #                     pos=(0.49 * self.wid, 0.025 * self.wid))]
        self.balls = [Ball()]
        '''self.second_ball = Image(source='ball0.png', size_hint=(0.02, 0.02 * self.razm),
                                 pos=(0.49 * self.wid, 0.025 * self.wid))'''
        self.time = "day" if int(time.strftime('%H', time.localtime(time.time()))) in range(7, 19) else "night"
        self.background = Image(source=f"{self.time}_sky.png", size_hint=(1, 1), fit_mode="fill")
        self.anch_pause = AnchorLayout(anchor_x="left", anchor_y="top", opacity=0.5)
        self.img_pause = Image(source=f"pause_{self.time}.png", size_hint=(60/self.wid, 60/self.hei))
        self.anch_pause.add_widget(self.img_pause)
        self.img_pause.bind(on_touch_down=self.pause)
        self.sound_brick = SoundLoader.load('brick_s2.mp3')
        self.sound_brick.loop = False
        self.sound_background = SoundLoader.load('background.mp3')
        self.sound_background.volume = 0.5
        self.sound_background.loop = True
        self.sound_platform = SoundLoader.load('ball_and_platform.mp3')
        self.sound_platform.volume = 0.1
        self.sound_platform.loop = False
        self.sound_chain = SoundLoader.load('chain.mp3')
        self.sound_chain.loop = False
        self.fl = FloatLayout()
        self.blocks = []
        self.game_status = 0
        self.online_status = 1
        self.fb = []
        self.sb = []
        # self.angle0 = [1]
        # self.last_move = ['']
        # self.speed = [500]

    def move(self, obj, touch):
        self.platform.bind(on_touch_up=self.move)
        if not self.img_pause.collide_point(*touch.pos):
            if touch.pos[0] >= 0.05 * self.wid and touch.pos[0] <= 0.95 * self.wid:
                self.platform.pos = (touch.pos[0] - 0.05 * self.wid, 0)
            elif touch.pos[0] < 0.05 * self.wid:
                self.platform.pos = (0, 0)
            else:
                self.platform.pos = (0.9 * self.wid, 0)
            if not self.game_status:
                self.game_status = 1
                if self.balls[0].pos[1] == 0.025 * self.wid:
                    if touch.pos[0] > self.wid/2:
                        self.up_right(self.balls[0].pos, 1, ball=self.balls[0])
                    else:
                        self.up_left(self.balls[0].pos, 1, ball=self.balls[0])
                else:
                    for ball in self.balls:
                        lm = ball.last_move
                        ud = "up" if lm[0] == "u" else "down"
                        lr = "left" if lm[1] == "l" else "right"
                        exec(f"self.{ud}_{lr}(ball.pos, angle=ball.angle, ball=ball)")
                    for bust in self.fb:
                        fb_anim = Animation(y=-0.015 * self.wid, d=(bust.pos[1] + 0.015 * self.wid)/200)
                        fb_anim.start(bust)
                        fb_anim.bind(on_progress=self.first_bust)
                        pass

    def up_right(self, pos, angle, ball):
        x0, y0 = pos
        ball.angle = angle
        dx = 0.99 * self.wid - x0
        dy = 0.99 * self.hei - y0
        # print(dx, dy)
        if dy/dx < angle:
            y = self.hei - 0.01 * self.wid
            x = x0 + dy / angle - 0.01 * self.wid
        elif dy/dx > angle:
            x = 0.99 * self.wid
            y = y0 + dx * angle - 0.01 * self.wid
        else:
            x = 0.99 * self.wid
            y = self.hei - 0.01 * self.wid
        dx = x - x0
        dy = y - y0
        anim = Animation(x=x, y=y, d=((dx * dx + dy * dy) ** 0.5) / ball.speed)
        anim.start(ball)
        ball.last_move = "ur"
        anim.bind(on_complete=self.find_angle)
        anim.bind(on_progress=self.brake)
        anim.bind(on_progress=self.out_border)

    def up_left(self, pos, angle, ball):
        x0, y0 = pos
        ball.angle = angle
        dx = x0 - 0.01 * self.wid
        dy = 0.99 * self.hei - y0
        # print(dx, dy)
        if dy / dx < angle:
            y = self.hei - 0.01 * self.wid
            x = x0 - dy / angle
        elif dy / dx > angle:
            x = 0
            y = y0 + dx * angle - 0.01 * self.wid
        else:
            x = 0
            y = self.hei - 0.01 * self.wid
        dx = x - x0
        dy = y - y0
        anim = Animation(x=x, y=y, d=((dx * dx + dy * dy) ** 0.5) / ball.speed)
        anim.start(ball)
        ball.last_move = "ul"
        anim.bind(on_complete=self.find_angle)
        anim.bind(on_progress=self.brake)
        anim.bind(on_progress=self.out_border)

    def down_right(self, pos, angle, ball):
        x0, y0 = pos
        ball.angle = angle
        dx = 0.99 * self.wid - x0
        dy = y0 - 0.025 * self.wid
        # print(dx, dy)
        if dy / dx < angle:
            y = 0.025 * self.wid
            x = x0 + dy / angle - 0.01 * self.wid
        elif dy / dx > angle:
            x = 0.99 * self.wid
            y = y0 - dx * angle - 0.01 * self.wid
        else:
            x = 0.99 * self.wid
            y = 0.025 * self.wid
        dx = x - x0
        dy = y - y0
        anim = Animation(x=x, y=y, d=((dx * dx + dy * dy) ** 0.5) / ball.speed)
        anim.start(ball)
        ball.last_move = "dr"
        anim.bind(on_complete=self.find_angle)
        anim.bind(on_progress=self.brake)
        anim.bind(on_progress=self.out_border)

    def down_left(self, pos, angle, ball):
        x0, y0 = pos
        ball.angle = angle
        dx = x0 - 0.01 * self.wid
        dy = y0 - 0.025 * self.wid
        # print(dx, dy)
        if dy / dx < angle:
            y = 0.025 * self.wid
            x = x0 - dy / angle
        elif dy / dx > angle:
            x = 0
            y = y0 - dx * angle - 0.01 * self.wid
        else:
            x = 0
            y = 0.025 * self.wid
        dx = x - x0
        dy = y - y0
        anim = Animation(x=x, y=y, d=((dx * dx + dy * dy) ** 0.5) / ball.speed)
        anim.start(ball)
        ball.last_move = "dl"
        anim.bind(on_complete=self.find_angle)
        anim.bind(on_progress=self.brake)
        anim.bind(on_progress=self.out_border)

    def out_border(self, anim, obj, prog):
        lm = obj.last_move
        if obj.pos[0] < -0.02 * self.wid:
            anim.stop(obj)
            obj.pos[0] += 0.02 * self.wid
            self.up_right(obj.pos, angle=obj.angle, ball=obj) if lm == 'ul' else self.down_right(obj.pos,
                                                                                                 angle=obj.angle,
                                                                                                 ball=obj)
        elif obj.pos[0] > self.wid:
            anim.stop(obj)
            obj.pos[0] -= 0.02 * self.wid
            self.up_left(obj.pos, angle=obj.angle0, ball=obj) if lm == 'ur' else self.down_left(obj.pos,
                                                                                                angle=obj.angle,
                                                                                                ball=obj)


    def brake(self, anim, obj, prog):
        lm = obj.last_move
        for block in self.blocks:
            if obj.collide_widget(block):
                if obj.bust:
                    self.fl.remove_widget(block)
                    self.blocks.remove(block)
                    obj.bust -= 1
                    lm = obj.last_move
                    ud = "up" if lm[0] == "u" else "down"
                    lr = "left" if lm[1] == "l" else "right"
                    exec(f"self.{ud}_{lr}(obj.pos, angle=obj.angle, ball=obj)")
                    break
                else:
                    obj.source = "ball0.png"
                anim.stop(obj)
                # self.fl.remove_widget(block)
                # self.blocks.remove(block)
                # print("Before:", self.ball.pos, block.pos, lm)
                self.change_color(block, obj)
                if not len(self.blocks):
                    anim.stop(obj)
                    time.sleep(5)
                    self.main_menu()
                else:
                    # print("After:", self.ball.pos, block.pos, lm)
                    x1, y1 = obj.pos
                    x2, y2 = block.pos
                    if lm == "ur":
                        if x2 - x1 < y2 - y1:
                            self.down_right(obj.pos, angle=obj.angle, ball=obj)
                        elif x2 - x1 > y2 - y1:
                            self.up_left(obj.pos, angle=obj.angle, ball=obj)
                        else:
                            self.down_left(obj.pos, angle=obj.angle, ball=obj)
                    elif lm == "ul":
                        if (x1 + obj.size[0]) - (x2 + block.size[0]) < y2 - y1:
                            self.down_left(obj.pos, angle=obj.angle, ball=obj)
                        elif (x1 + obj.size[0]) - (x2 + block.size[0]) > y2 - y1:
                            self.up_right(obj.pos, angle=obj.angle, ball=obj)
                        else:
                            self.down_right(obj.pos, angle=obj.angle, ball=obj)
                    elif lm == "dr":
                        if x2 - x1 < (y1 + obj.size[1]) - (y2 + block.size[1]):
                            self.up_right(obj.pos, angle=obj.angle, ball=obj)
                        elif x2 - x1 > (y1 + obj.size[1]) - (y2 + block.size[1]):
                            self.down_left(obj.pos, angle=obj.angle, ball=obj)
                        else:
                            self.up_left(obj.pos, angle=obj.angle, ball=obj)
                    else:
                        if (x1 + obj.size[0]) - (x2 + block.size[0]) < (y1 + obj.size[1]) - (
                                y2 + block.size[1]):
                            self.up_left(obj.pos, angle=obj.angle, ball=obj)
                        elif (x1 + obj.size[0]) - (x2 + block.size[0]) > (y1 + obj.size[1]) - (
                                y2 + block.size[1]):
                            self.down_right(obj.pos, angle=obj.angle, ball=obj)
                        else:
                            self.up_right(obj.pos, angle=obj.angle, ball=obj)
                    '''self.down_left(obj.pos, angle=self.angle0) if lm == "ul"\
                        else self.down_right(obj.pos, angle=self.angle0) if lm == "ur"\
                        else self.up_left(obj.pos, angle=self.angle0) if lm == "dl"\
                        else self.up_right(obj.pos, angle=self.angle0)'''
                break
        pass

    def change_color(self, block, ball):
        self.sound_brick.play()
        '''if block.background_color == [139 / 255, 0, 1, 1]:
            block.background_color = [0, 0, 1, 1]
        elif block.background_color == [0, 0, 1, 1]:
            block.background_color = [0, 191 / 255, 1, 1]
        elif block.background_color == [0, 191 / 255, 1, 1]:
            block.background_color = [0, 1, 0, 1]
        elif block.background_color == [0, 1, 0, 1]:
            block.background_color = [1, 1, 0, 1]
        elif block.background_color == [1, 1, 0, 1]:
            block.background_color = [1, 102 / 255, 0, 1]
        elif block.background_color == [1, 102 / 255, 0, 1]:
            block.background_color = [1, 0, 0, 1]
        elif block.background_color == [1, 0, 0, 1]:
            block.opacity = 0'''
        brick = block.children[0]
        hp = int(brick.source[5:6])
        if hp == 1:
            block.opacity = 0
        else:
            brick.source = f"brick{hp - 1}hp1.png"
        x1, y1 = ball.pos
        x2, y2 = block.pos
        lm = ball.last_move
        if lm == "ur":
            if x2 - x1 < y2 - y1:
                ball.pos[1] = block.pos[1] - ball.size[1] - 10 ** -5
            elif x2 - x1 > y2 - y1:
                ball.pos[0] = block.pos[0] - ball.size[0] - 10 ** -5
            else:
                ball.pos[0] = block.pos[0] - ball.size[0] - 10 ** -5
                ball.pos[1] = block.pos[1] - ball.size[1] - 10 ** -5
        elif lm == "ul":
            if (x1 + ball.size[0]) - (x2 + block.size[0]) < y2 - y1:
                ball.pos[1] = block.pos[1] - ball.size[1] - 10 ** -5
            elif (x1 + ball.size[0]) - (x2 + block.size[0]) > y2 - y1:
                ball.pos[0] = block.pos[0] + block.size[0] + 10 ** -5
            else:
                ball.pos[0] = block.pos[0] + block.size[0] + 10 ** -5
                ball.pos[1] = block.pos[1] - ball.size[1] - 10 ** -5
        elif lm == "dr":
            if x2 - x1 < (y1 + ball.size[1]) - (y2 + block.size[1]):
                ball.pos[1] = block.pos[1] + block.size[1] + 10 ** -5
            elif x2 - x1 > (y1 + ball.size[1]) - (y2 + block.size[1]):
                ball.pos[0] = block.pos[0] - ball.size[0] - 10 ** -5
            else:
                ball.pos[0] = block.pos[0] - ball.size[0] - 10 ** -5
                ball.pos[1] = block.pos[1] + block.size[1] + 10 ** -5
        else:
            if (x1 + ball.size[0]) - (x2 + block.size[0]) < (y1 + ball.size[1]) - (y2 + block.size[1]):
                ball.pos[1] = block.pos[1] + block.size[1] + 10 ** -5
            elif (x1 + ball.size[0]) - (x2 + block.size[0]) > (y1 + ball.size[1]) - (y2 + block.size[1]):
                ball.pos[0] = block.pos[0] + block.size[0] + 10 ** -5
            else:
                ball.pos[0] = block.pos[0] + block.size[0] + 10 ** -5
                ball.pos[1] = block.pos[1] + block.size[1] + 10 ** -5
        '''if self.last_move[0] == "u":
            self.ball.pos[1] -= self.wid * 0.01
        else:
            self.ball.pos[1] += self.wid * 0.01'''
        if block.opacity == 0:
            self.fl.remove_widget(block)
            self.blocks.remove(block)
            bust = randint(2, 2)
            if bust == 1:
                first_bust = Image(source='first_bust.png', size_hint=(0.03, 0.015 * self.razm))
                first_bust.pos = (block.pos[0] + (block.size[0] - 0.03 * self.wid) / 2, block.pos[1])
                self.fl.add_widget(first_bust)
                fb_anim = Animation(y=-0.015 * self.wid, d=(block.pos[1] + 0.015 * self.wid) / 200)
                fb_anim.start(first_bust)
                fb_anim.bind(on_progress=self.first_bust)
                self.fb.append(first_bust)
                pass
            elif bust == 2:
                second_bust = Image(source='second_bust.png', size_hint=(0.03, 0.0375 * self.razm))
                second_bust.pos = (block.pos[0] + (block.size[0] - 0.03 * self.wid) / 2, block.pos[1])
                self.fl.add_widget(second_bust)
                fb_anim = Animation(y=-0.0375 * self.wid, d=(block.pos[1] + 0.0375 * self.wid) / 200)
                fb_anim.start(second_bust)
                fb_anim.bind(on_progress=self.second_bust)
                self.sb.append(second_bust)
        pass

    def first_bust(self, anim, obj, progress):
        if obj.collide_widget(self.platform):
            anim.stop(obj)
            ball = Ball()
            ball.pos = obj.pos
            self.fl.remove_widget(obj)
            self.balls.append(ball)
            self.fl.add_widget(ball)
            xp = self.platform.pos[0] + 0.05 * self.wid
            x = obj.pos[0]
            if x > xp:
                ball.angle = 0.07 * self.wid / (x - xp)
                self.up_right(ball.pos, ball.angle, ball)
            elif x < xp:
                ball.angle = 0.07 * self.wid / (xp - x)
                self.up_left(ball.pos, ball.angle, ball)
            else:
                ball.angle = 10**(-10)
                self.up_right(ball.pos, ball.angle, ball)
        pass

    def second_bust(self, anim, obj, progress):
        if obj.collide_widget(self.platform):
            anim.stop(obj)
            self.platform.source = "fireplatform0.png"
            self.fl.remove_widget(obj)
        pass

    def find_angle(self, anim, obj):
        x, y = obj.pos
        lm = obj.last_move
        angle = obj.angle
        if x >= 0.98 * self.wid:
            obj.pos[0] = self.wid - obj.size[0] - 10 ** -5
            if lm == "ur":
                self.up_left([x, y], angle, ball=obj)
            elif lm == "dr":
                self.down_left([x, y], angle, ball=obj)
        elif x <= 0:
            obj.pos[0] = 10 ** -5
            if lm == "ul":
                self.up_right([x, y], angle, ball=obj)
            elif lm == "dl":
                self.down_right([x, y], angle, ball=obj)
        elif y >= self.hei - 0.02 * self.wid:
            obj.pos[1] = self.hei - 0.02 * self.wid - 10 ** -5
            if lm == "ur":
                self.down_right([x, y], angle, ball=obj)
            elif lm == "ul":
                self.down_left([x, y], angle, ball=obj)
        elif y <= 0.025 * self.wid:
            obj.pos[1] = 0.025 * self.wid + 10 ** -5
            '''
            self.speed += 5
            self.sound_ball.play()
            if lm == "dr":
                self.up_right([x, y], angle)
            elif lm == "dl":
                self.up_left([x, y], angle)
            '''
            xp = self.platform.pos[0] + 0.05 * self.wid  # 0.02 + 0.05 + 0.05 + 0.02
            if abs(x - xp) < 0.07 * self.wid:
                obj.speed += 5
                self.sound_platform.play()
                if self.platform.source == "fireplatform0.png":
                    obj.bust = 5
                    obj.source = "fireball0.png"
                    self.platform.source = "platform0.png"
                    pass
                if lm == "dr":
                    # self.up_right([x, y], angle)
                    if x == xp:
                        self.up_right([x, y], angle, ball=obj)
                    elif x - xp > 0:
                        angle = (0.07 * self.wid / (x - xp))
                        self.up_right([x, y], angle, ball=obj)
                    else:
                        angle = (0.07 * self.wid / (xp - x))
                        self.up_left([x, y], angle, ball=obj)
                elif lm == "dl":
                    # self.up_left([x, y], angle)
                    if x == xp:
                        self.up_left([x, y], angle, ball=obj)
                    elif x - xp > 0:
                        angle = (0.07 * self.wid / (x - xp))
                        self.up_right([x, y], angle, ball=obj)
                    else:
                        angle = (0.07 * self.wid / (xp - x))
                        self.up_left([x, y], angle, ball=obj)
            else:
                dy = 0.026 * self.wid
                dx = dy / angle
                anim = Animation(x=x - dx if lm == "dl" else x + dx, y=-0.02 * self.wid,
                                 d=((dx * dx + dy * dy) ** 0.5) / 500)
                anim.bind(on_complete=self.lose)
                anim.start(obj)

    def lose(self, anim, obj):
        if len(self.balls) == 1:
            self.sound_background.stop()
            sound_slime = SoundLoader.load("slime.mp3")
            sound_slime.play()
            self.game_status = 0
            lose = Image(source="slime.png", size_hint=(1, 1), pos=(0, 0), anim_delay=1/30)
            self.fl.add_widget(lose)
            self.platform.unbind(on_touch_up=self.move)
            self.platform.unbind(on_touch_move=self.move)
            self.img_pause.unbind(on_touch_down=self.pause)
            lose.bind(on_touch_up=self.main_menu_after_pause)
        else:
            self.fl.remove_widget(obj)
            try:
                self.balls.remove(obj)
            except:
                pass

    def start_options(self):
        self.balls[0].opacity = self.platform.opacity = 1
        self.platform.source = "platform0.png"
        self.img_pause.opacity = 0.5
        self.platform.pos = (0.45 * self.wid, 0)
        self.platform.bind(on_touch_move=self.move)
        self.img_pause.bind(on_touch_down=self.pause)

    def generate(self):
        self.fl.clear_widgets()
        self.fl.add_widget(self.background)
        self.balls = [Ball()]
        self.start_options()
        self.fl.add_widget(self.platform)
        self.fl.add_widget(self.balls[0])
        self.blocks = []
        # colors = [[1, 0, 0, 1], [1, 102/255, 0, 1], [1, 1, 0, 1], [0, 1, 0, 1], [0, 191/255, 1, 1], [0, 0, 1, 1],
        #           [139/255, 0, 1, 1]]
        brick_hp = [f"brick{i}hp1.png" for i in range(1, 8)]
        free_x = (self.wid - 800) / 11
        for i in range(70):
            '''self.blocks.append(Button(background_down='', background_normal='',
                                      background_color=([139/255, 0, 1, 1] if i//10 == 0 else [0, 0, 1, 1] if i//10 == 1
                                      else [0, 191/255, 1, 1] if i//10 == 2 else [0, 1, 0, 1] if i//10 == 3
                                      else [1, 1, 0, 1] if i//10 == 4 else [1, 102/255, 0, 1] if i//10 == 5
                                      else [1, 0, 0, 1]), size_hint=(0.08, 0.02 * self.razm),
                                      pos=((0.01 + (i % 10) * 0.1) * self.wid, self.hei - (0.03 + (i//10) * 0.04) * self.wid)))'''
            self.blocks.append(Button(background_down='', background_normal='',
                                      background_color=[1, 1, 1, 0], size_hint=(0.08, 0.02 * self.razm),
                                      pos=(free_x + (i % 10) * (free_x + 80),
                                           self.hei - (free_x + 20 + (i // 10) * (free_x + 20)))))
            self.blocks[i].add_widget(Image(source=brick_hp[randint(1, 6)], size=(80, 20), pos=self.blocks[i].pos))
            self.fl.add_widget(self.blocks[i])
        self.fl.add_widget(self.anch_pause)

    def online(self):
        online = Button(text="Онлайн\nДоступны рейтинг и\nсохранение в облаке", halign="center", background_normal="",
                        background_color=[0.75, 0.75, 0.75, 1], font_size=30,
                        background_down="", size_hint=(0.5, 1),
                        pos=(0.5 * self.wid, 0), opacity=0.5)
        online_image = Image(source="wifi.png", size_hint=(0.25, 0.25 * self.razm),
                             pos=(5 * self.wid/8, 5 * self.hei/8))
        offline = Button(text="Оффлайн\nПрогресс сохраняется локально", halign="center", background_normal="",
                         background_color=[0.25, 0.25, 0.25, 1], font_size=30,
                         background_down="", size_hint=(0.5, 1),
                         pos=(0, 0), opacity=0.5)
        offline_image = Image(source="nowifi.png", size_hint=(0.25, 0.25 * self.razm),
                              pos=(1 * self.wid / 8, 5 * self.hei / 8))
        online.bind(on_press=self.on_internet)
        offline.bind(on_press=self.off_internet)
        self.fl.add_widget(self.background)
        self.fl.add_widget(online)
        self.fl.add_widget(online_image)
        self.fl.add_widget(offline)
        self.fl.add_widget(offline_image)

    def on_internet(self, *args):
        self.online_status = 1
        with open("info.json") as f:
            nick = json.load(f)['nickname']
        if nick:
            self.main_menu()
        else:
            self.start()

    def off_internet(self, *args):
        self.online_status = 0
        with open("info.json") as f:
            nick = json.load(f)['nickname']
        if nick:
            self.main_menu()
        else:
            self.start()

    def start(self):
        self.fl.clear_widgets()
        self.fl.add_widget(self.background)
        lbl = Label(text="Введите никнейм. Внимание!\nЕго можно будет изменить в будущем",
                    halign="center", font_size=30, pos=(0, self.hei/4))
        name_input = TextInput(text="", size_hint=(0.6, 0.07), pos=(self.wid * 0.2, self.hei * 0.6), multiline=False,
                               halign="center", font_size=30, opacity=0.5)
        name_input.bind(on_text_validate=self.enter)
        self.fl.add_widget(name_input)
        self.fl.add_widget(lbl)

    def enter(self, obj):
        # print(obj.text)
        with open("info.json") as f:
            inf = json.load(f)
            inf['nickname'] = obj.text
        with open("info.json", "w") as f:
            f.write(json.dumps(inf))
        # Махинации с именем и сохранением его в БД
        self.main_menu()

    def pause(self, obj, touch):
        if obj.collide_point(*touch.pos):
            for ball in self.balls:
                Animation.stop_all(ball)
            for bust in self.fb:
                Animation.stop_all(bust)
            obj.opacity = 0
            self.game_status = 0
            self.img_pause.unbind(on_touch_up=self.pause)
            self.platform.unbind(on_touch_up=self.move)
            self.platform.unbind(on_touch_move=self.move)
            for child in self.fl.children:
                if child != self.background and child != obj:
                    child.opacity = 0.5
                    pass
            if self.online_status:
                chain = Image(source="chain1.png", size_hint=(0.007, 0.3), pos=(self.wid * 0.4965, self.hei * 1.5),
                              fit_mode="fill")
                contin = Image(source="continue_pause.png", size_hint=(7 / 30, 0.1),
                               pos=(self.wid * 23 / 60, self.hei * 1.4))
                rating = Image(source="rating_pause.png", size_hint=(7 / 30, 0.1),
                               pos=(self.wid * 23 / 60, self.hei * 1.3))
                setting = Image(source="setting_pause.png", size_hint=(7 / 30, 0.1),
                                pos=(self.wid * 23 / 60, self.hei * 1.2))
                store = Image(source="store_pause.png", size_hint=(7 / 30, 0.1),
                              pos=(self.wid * 23 / 60, self.hei * 1.1))
                main_menu = Image(source="main_menu_pause.png", size_hint=(7 / 30, 0.1),
                                  pos=(self.wid * 23 / 60, self.hei))
                self.fl.add_widget(chain)
                self.fl.add_widget(contin)
                self.fl.add_widget(rating)
                self.fl.add_widget(setting)
                self.fl.add_widget(store)
                self.fl.add_widget(main_menu)
                contin.bind(on_touch_down=self.continue_game)
                rating.bind(on_touch_down=self.rating)
                setting.bind(on_touch_down=self.setting)
                store.bind(on_touch_down=self.store)
                main_menu.bind(on_touch_down=self.main_menu_after_pause)
                main_menu.bind(on_touch_down=self.main_menu_after_pause)
                anim_chain = Animation(y=self.hei * 0.7, d=5)
                anim_contin = Animation(y=self.hei * 0.6, d=5)
                anim_rating = Animation(y=self.hei * 0.5, d=5)
                anim_setting = Animation(y=self.hei * 0.4, d=5)
                anim_store = Animation(y=self.hei * 0.3, d=5)
                anim_main_menu = Animation(y=self.hei * 0.2, d=5)
                anim_chain.start(chain)
                anim_contin.start(contin)
                anim_rating.start(rating)
                anim_setting.start(setting)
                anim_store.start(store)
                anim_main_menu.start(main_menu)
                self.sound_chain.play()
            else:
                chain = Image(source="chain1.png", size_hint=(0.007, 0.3), pos=(self.wid * 0.4965, self.hei * 1.4),
                              fit_mode="fill")
                contin = Image(source="continue_pause.png", size_hint=(7 / 30, 0.1),
                               pos=(self.wid * 23 / 60, self.hei * 1.3))
                setting = Image(source="setting_pause.png", size_hint=(7 / 30, 0.1),
                                pos=(self.wid * 23 / 60, self.hei * 1.2))
                store = Image(source="store_pause.png", size_hint=(7 / 30, 0.1),
                              pos=(self.wid * 23 / 60, self.hei * 1.1))
                main_menu = Image(source="main_menu_pause.png", size_hint=(7 / 30, 0.1),
                                  pos=(self.wid * 23 / 60, self.hei))
                self.fl.add_widget(chain)
                self.fl.add_widget(contin)
                self.fl.add_widget(setting)
                self.fl.add_widget(store)
                self.fl.add_widget(main_menu)
                contin.bind(on_touch_down=self.continue_game)
                setting.bind(on_touch_down=self.setting)
                store.bind(on_touch_down=self.store)
                main_menu.bind(on_touch_down=self.main_menu_after_pause)
                anim_chain = Animation(y=self.hei * 0.7, d=5)
                anim_contin = Animation(y=self.hei * 0.6, d=5)
                anim_setting = Animation(y=self.hei * 0.5, d=5)
                anim_store = Animation(y=self.hei * 0.4, d=5)
                anim_main_menu = Animation(y=self.hei * 0.3, d=5)
                anim_chain.start(chain)
                anim_contin.start(contin)
                anim_setting.start(setting)
                anim_store.start(store)
                anim_main_menu.start(main_menu)
                self.sound_chain.play()
        pass

    def continue_game(self, obj, touch):
        if obj.collide_point(*touch.pos):
            children = self.fl.children
            self.sound_chain.stop()
            if self.online_status:
                anim_chain = Animation(y=self.hei * 1.5, d=5)
                anim_contin = Animation(y=self.hei * 1.4, d=5)
                anim_rating = Animation(y=self.hei * 1.3, d=5)
                anim_setting = Animation(y=self.hei * 1.2, d=5)
                anim_store = Animation(y=self.hei * 1.1, d=5)
                anim_main_menu = Animation(y=self.hei, d=5)
                anim_chain.start(children[5])
                anim_contin.start(children[4])
                anim_rating.start(children[3])
                anim_setting.start(children[2])
                anim_store.start(children[1])
                anim_main_menu.start(children[0])
                anim_main_menu.bind(on_complete=self.delete_pause)
                self.sound_chain.play()
            else:
                anim_chain = Animation(y=self.hei * 1.4, d=5)
                anim_contin = Animation(y=self.hei * 1.3, d=5)
                anim_setting = Animation(y=self.hei * 1.2, d=5)
                anim_store = Animation(y=self.hei * 1.1, d=5)
                anim_main_menu = Animation(y=self.hei, d=5)
                anim_chain.start(children[4])
                anim_contin.start(children[3])
                anim_setting.start(children[2])
                anim_store.start(children[1])
                anim_main_menu.start(children[0])
                anim_main_menu.bind(on_complete=self.delete_pause)
                self.sound_chain.play()

    def delete_pause(self, anim, obj):
        children = self.fl.children
        for child in children:
            if child in self.blocks or child in self.balls or child == self.platform or child in self.fb:
                child.opacity = 1
        if self.online_status:
            for i in range(6):
                self.fl.remove_widget(self.fl.children[0])
        else:
            for i in range(5):
                self.fl.remove_widget(self.fl.children[0])
        self.img_pause.opacity = 0.5
        self.img_pause.bind(on_touch_up=self.pause)
        self.platform.bind(on_touch_move=self.move)

    def main_menu_after_pause(self, obj, touch):
        if obj.collide_point(*touch.pos):
            self.sound_chain.stop()
            self.main_menu()


    def main_menu(self):
        self.sound_background.play()
        self.fl.clear_widgets()
        self.fl.add_widget(self.background)
        with open("info.json") as f:
            nick = json.load(f)['nickname']
        name = Label(text=nick, halign="center", font_size=40, size_hint=(0.5, 0.1),
                     pos=(0.25 * self.wid, self.hei * 0.85), font_name='blackadderitc_regular.ttf')
        self.fl.add_widget(name)
        if self.online_status:
            '''start = Button(text="Начать игру", halign="center", font_size=30, size_hint=(0.6, 0.1),
                              pos=(self.wid * 0.2, self.hei * 0.7))
            rating = Button(text="Рейтинг", halign="center", font_size=30, size_hint=(0.6, 0.1),
                            pos=(self.wid * 0.2, self.hei * 0.575))
            setting = Button(text="Настройки", halign="center", font_size=30, size_hint=(0.6, 0.1),
                             pos = (self.wid * 0.2, self.hei * 0.45))
            store = Button(text="Магазин", halign="center", font_size=30, size_hint=(0.6, 0.1),
                           pos=(self.wid * 0.2, self.hei * 0.325))
            exit = Button(text="Выход", halign="center", font_size=30, size_hint=(0.6, 0.1),
                          pos=(self.wid * 0.2, self.hei * 0.2))'''
            start = Image(source="start.png", size_hint=(0.6, 0.1), pos=(self.wid * 0.2, self.hei * 0.7), opacity=0.7)
            rating = Image(source="rating.png", size_hint=(0.6, 0.1), pos=(self.wid * 0.2, self.hei * 0.575), opacity=0.7)
            setting = Image(source="setting.png", size_hint=(0.6, 0.1), pos=(self.wid * 0.2, self.hei * 0.45), opacity=0.7)
            store = Image(source="store.png", size_hint=(0.6, 0.1), pos=(self.wid * 0.2, self.hei * 0.325), opacity=0.7)
            exit = Image(source="exit.png", size_hint=(0.6, 0.1), pos=(self.wid * 0.2, self.hei * 0.2), opacity=0.7)
            rating.bind(on_touch_down=self.rating)
            self.fl.add_widget(rating)
            pass
        else:
            # start = Button(text="Начать игру", halign="center", font_size=30, size_hint=(0.6, 0.1),
            #                pos=(self.wid * 0.2, self.hei * 0.625))
            start = Image(source="start.png", size_hint=(0.6, 0.1), pos=(self.wid * 0.2, self.hei * 0.625), opacity=0.7)
            setting = Image(source="setting.png", size_hint=(0.6, 0.1), pos=(self.wid * 0.2, self.hei * 0.5), opacity=0.7)
            store = Image(source="store.png", size_hint=(0.6, 0.1), pos=(self.wid * 0.2, self.hei * 0.375), opacity=0.7)
            exit = Image(source="exit.png", size_hint=(0.6, 0.1), pos=(self.wid * 0.2, self.hei * 0.25), opacity=0.7)
        self.fl.add_widget(start)
        self.fl.add_widget(setting)
        self.fl.add_widget(store)
        self.fl.add_widget(exit)
        start.bind(on_touch_down=self.start_game)
        setting.bind(on_touch_down=self.setting)
        store.bind(on_touch_down=self.store)
        exit.bind(on_touch_down=self.exit)
        pass

    def start_game(self, obj, touch):
        if obj.collide_point(*touch.pos):
            self.generate()
        pass

    def rating(self, obj, touch):
        if obj.collide_point(*touch.pos):
            print("rating")
            pass
        pass

    def setting(self, obj, touch):
        if obj.collide_point(*touch.pos):
            print("setting")
            pass
        pass

    def store(self, obj, touch):
        if obj.collide_point(*touch.pos):
            print("store")
            pass
        pass

    def exit(self, obj, touch):
        if obj.collide_point(*touch.pos):
            Window.close()

    def build(self):
        try:
            with open("info.json") as f:
                test = f.read()
        except:
            test = 0
        if not test:
            inf = {'admin': False, 'nickname': "", 'score': 0, 'num_ball': 0, 'num_platform': 0,
                   'balls': [0], 'platforms': [0]}
            with open("info.json", "w") as f:
                f.write(json.dumps(inf))
        self.online()
        # self.generate()
        return self.fl


if __name__ == "__main__":
    # bd = sqlite3.connect("User.db")
    # cur = bd.cursor()
    # cur.execute('''CREATE TABLE User (Name VARCHAR(20), Score INT, Num_balls INT, Num_platforms INT, Admin INT, PRIMARY KEY(Name));''')
    # cur.execute('''INSERT INTO User VALUES ('Mr_fartam', 0, 0, 0, 0)''')
    # cur.execute('''SELECT * FROM User WHERE Score=0''')
    # print(cur.fetchall())
    MyApp().run()