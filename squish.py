#!/usr/bin/env python
# coding: utf-8

import os,sys,pygame
from pygame.locals import *
import config,object

#这个模块包含游戏的主要逻辑

class State:
    '''
    范型游戏状态类，可以处理事件并在给定的表面上显示自身
    '''
    def handle(self,event):
    #只处理退出事件的默认事件处理

        if event.type == QUIT:
            sys.exit()
        if event.type == KEYDOWN and event.key == K_ESCAPE:
            sys.exit()

    def firstDisplay(self,screen):
        '''
        用于第一次显示状态。使用背景色填充屏幕
        '''
        screen.fill(config.Background_color)
        #记得调用flip，让更改可见
        pygame.display.flip()
    def display(self,screen):
        '''
        用于在已经显示过一次状态后再次显示，默认的行为是什么都不做
        '''
        pass
class Level(State):
    '''
    游戏等级。用于计算已经下落的秤砣，移动子图形以及其他和游戏逻辑相关的任务
    '''
    def __init__(self,number=1):
        self.number = number
        #本关内还要落下多少秤砣？
        self.remaining =config.Weights_per_level
        speed = config.Drop_speed
        #为每个大于1等级的秤砣都增加一个 speed increase
        speed += (self.number-1)+config.Speed_increase
        #创建秤砣和香蕉
        self.weight = object.Weight(speed)
        self.banana = object.Banana()
        both = self.weight, self.banana #这个能包含更多的Sprites
        self.sprites = pygame.sprite.RenderUpdates(both)
    def update(self,game):
        '''
        从前一帧更新游戏状态
        '''
        #更新所有子图形
        self.sprites.update()
        #如果香蕉碰到了秤砣，那么告诉游戏切换到GameOver状态
        if self.banana.touches(self.weight):
            game.nextState = GameOver()
        #否则在秤砣落地时将其复位
        #如果本关内所有的秤砣落下了，则让游戏切换到LevelCleared状态
        elif self.weight.landed:
            self.weight.reset()
            self.remaining -= 1
            if self.remaining == 0:
                game.nextState = LevelCleared(self.number)
    def display(self,screen):
        '''
        在第一次显示（只清空屏幕）后显示状态。与firstDisplay不同，这个方法使用pygame.display.update
        对self.sprites.draw提供的、需要更新的矩形列表进行更新
        '''
        screen.fill(config.Background_color)
        updates = self.sprites.draw(screen)
        pygame.display.update(updates)

class Paused(State):
    '''
    简单的暂停游戏状态，按下键盘上任意键或者点击鼠标都会结束这个状态
    '''
    finished = 0 #用户结束暂停了吗？
    image = None #如果需要图片，在这里设置文件名
    text = '' #设置暂停的文本信息

    def handle(self,event):
        '''
        通过对State进行委托（一般处理退出事件），以及对按键和鼠标点击做出反应来处理事件。
        如果键被按下，或者鼠标点击，将self.finished 设置为真。
        '''
        State.handle(self,event)
        if event.type in [MOUSEBUTTONDOWN,KEYDOWN]:
            self.finished = 1
    def update(self,game):
        '''
        更新等级。如果按键按下或者鼠标被点击（比如self.finished为真）
        那么告诉游戏切换到了下一个由self.nextState()表示的状态（应该由子类实现）
        '''
        if self.finished:
            game.nextState = self.nextState()
    def firstDisplay(self,screen):
        '''
        暂停状态第一次出现时，绘制图像（如果有的画）并且生成文本
        '''
        #首先，使用填充背景色的方式清空屏幕
        screen.fill(config.Pause_Background)
        #使用默认的外观和指定大小创建Font对象
        font = pygame.font.Font(None,config.font_size)
        #获取self.text中的文本行，忽略开头和结尾的空行
        lines = self.text.strip().splitlines()
        #计算文本的高度（使用font.get_linessize()）以获取每行文本的高度
        height = len(lines) *font.get_linesize()
        #计算文本的放置位置（屏幕中心）：
        center,top =screen.get_rect().center
        top -= height // 2
        #如果要有图片显示的话。。。
        if self.image:
            #载入图片：
            image = pygame.image.load(os.path.join(self.image)).convert()
            #获取它的rect:
            r = image.get_rect()
            #将图像向下移动其高度的一半的距离
            top += r.height // 2
            #将图片放置在文本上面20像素处：
            r.midbottom = center, top -20
            #将图像移动到屏幕上
            screen.blit(image,r)
        antialias = 1 #让文本更美观一点
        black = 0,0,0 #让文本上色

        #生成所有行，从计过的top开始，并且对于每一行向下移动font.get_linessize()像素
        for line in lines:
            text = font.render(line.strip(),antialias,black)
            r = text.get_rect()
            r.midtop = center, top
            screen.blit(text,r)
            top += font.get_linesize()

        #显示所有更改
        pygame.display.flip()

class Info(Paused):
    '''
    简单的暂停状态，显示有关游戏的信息，在level状态后显示
    '''
    nextState = Level
    text = '''
    in this game you are a Hippo.
    trying to survive a course in 
    self-defense against defecate,where the
    participants will "defend"themselves
    against you with many defecate
            '''
class Startup(Paused):
    '''
    显示展示图片和欢迎信息的暂停状态。在Info状态后显示
    '''
    nextState = Info
    image =  config.Splash_image
    text = '''
    Welcome to Squlish,
    the game of Hippo against the defecate
            '''
class LevelCleared(Paused):
    '''
    提示用户通关的暂停状态。在next level后显示。
    '''
    def __init__(self,number):
        self.number = number
        self.text ='''level %i cleared
        Click to start next level'''% self.number

    def nextState(self):
        return Level(self.number+1)
class GameOver(Paused):
    '''
    提示用户输掉游戏的状态，在firstlevel后显示
    '''

    nextState = Level
    text = '''
    Game Over
    Click to Restart,Esc to Quit'''
class Game:
    '''负责主事件循环的游戏对象，任务包括在不同状态切换'''

    def __init__(self):
        #获取游戏和图像放置的目录
        path = os.path.abspath('.')
        dir = os.path.split(path)[0]
        #移动那个目录（这样图片文件可以在随后打开）
        os.chdir(dir)
        #无状态方式启动
        self.state = None
        #在第一个事件循环迭代中移动到Startup
        self.nextState = Startup()
    def run(self):
        '''
        此方法动态设置变量，进行一些重要的初始化工作，并且进入主事件循环。
        '''
        pygame.init() #初始化pygame模块
        #窗口还是全屏
        flag = 0            #默认窗口模式
        if config.full_screen:
            flag = FULLSCREEN  #全屏模式
        screen_size = config.Screen_size
        screen = pygame.display.set_mode(screen_size,flag)
        pygame.display.set_caption('Fruit Self Defense')
        pygame.mouse.set_visible(False)

        #主循环
        while True:
            #1,如果nextState被修改了，那么移动到新状态，并且显示它（第一次）：
            if self.state != self.nextState:
                self.state = self.nextState
                self.state.firstDisplay(screen)
            #2,代理当前状态的事件处理：
            for event in pygame.event.get():
                self.state.handle(event)
            #3,更新当前状态：
            self.state.update(self)
            #4,显示当前状态：
            self.state.display(screen)

if __name__ == '__main__':
    game = Game()
    game.run()
    game.__init__()