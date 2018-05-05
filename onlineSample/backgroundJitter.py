#-*- coding:utf-8 -*-
import math
from PIL import Image, ImageDraw, ImageFont
from random import randint as RDI

class BgJitter:
    def __init__(self, cfg):
        
        self.img = cfg['img']
        self.font = u'simsun.ttc'
        import sys
        if sys.platform != 'win32':
            self.font = u'c059033l.pfb'
        self.jitters = []
        if 'rotate' in cfg and cfg['rotate']:
            self.jitters.append(self.rotate)
        if 'crop' in cfg and cfg['crop']:
            self.jitters.append(self.crop)
        if 'lines' in cfg and cfg['lines']:
            self.jitters.append(self.random_line)
        if 'character' in cfg and cfg['character']:
            self.jitters.append(self.random_character)
    def jitter(self):
        w, h = self.img.size
        for j in self.jitters:
            j()
        self.img = self.img.resize((w, h))
        return self.img 
        
    def rotate(self):
        options = [
            Image.FLIP_LEFT_RIGHT,
            Image.FLIP_TOP_BOTTOM,
            Image.ROTATE_90,
            Image.ROTATE_180,
            Image.ROTATE_270
        ]
        option = RDI(0,5)
        if option < 5:
            option = options[option]
            self.img = self.img.transpose(option)
    
    def crop(self):
        op = RDI(0,5)
        if op < 5:
            w, h = self.img.size
            left = RDI(0, w-50)
            top = RDI(0, h-50)
            self.img = self.img.crop((left, top, w, h))
    
    def random_line(self):
        if RDI(0,5) < 3:
            return 0
            
        w, h = self.img.size
        draw = ImageDraw.Draw(self.img)
        for count in range(1):
            rol = RDI(0, max(20, h - 50))
            col = RDI(0, max(20,w - 50))
            delta_x = RDI(100, 500)
            delta_y = RDI(0, 100)
            x_step = 10 #RDI(0, 50)
            y_step = RDI(0, 10)
            x1 = col
            y1 = rol
            for iter in range(RDI(60, 100)):
                x2 = (x1 + delta_x) % w - 1
                y2 = (y1 + delta_y) % h - 1
                
                draw.line([(x1, y1), (x2, y2)], fill=(0,0,0), width=RDI(1,x_step))
                
                x1 += x_step
                y1 += y_step
        
        del draw
    
    def random_character(self):
        if RDI(0,5) < 3:
            return 0
            
        w, h = self.img.size
        draw = ImageDraw.Draw(self.img)
        
        maxx = max(0, w-100)
        if maxx == 0:
            maxx = w / 2
        maxy = max(0, w-100)    
        if maxy == 0:
            maxy = h / 2
        maxx = int(maxx)
        maxy = int(maxy)
        for iter in range(10):
            pos_x = RDI(0, maxx)
            pos_y = RDI(0, maxy)
            #font = ImageFont.truetype(u'simsun.ttc', RDI(20,100))
            font = ImageFont.truetype(self.font, RDI(20,100))
            draw.text(
                (pos_x, pos_y), 
                self.__gen_rand_str(None),
                font = font,
                fill = (RDI(0,255),RDI(0,255), RDI(0,255)))
        del draw
        
    def __gen_rand_str(self, size=None):
        if size is None:
            size = RDI(11,50)
        rand_str = [chr(RDI(0,255)) for x in range(size)]
        while '\n' in rand_str:
            rand_str.pop(rand_str.index('\n'))
        return "".join(rand_str)