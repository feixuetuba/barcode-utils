#-*- coding:utf-8 -*-
from io import BytesIO as BIO
from PIL import Image, ImageDraw, ImageFont
from random import randint as RDI
try:
    from onlineSample.backgroundJitter import BgJitter
except:
    from backgroundJitter import BgJitter
import os

          
class NetworkImgLoader(object):
    def __init__(self, uri):
        pass
#***********************************************************************       
class LocalImgLoader(object):
    def __init__(self, dirname):
        self.dirname = dirname
        self.index = 0
        self.current_image = ""
        
        if not os.path.isdir(dirname):
            raise Exception('Image dir %s no found!'%dirname)
            
        self.file_list = []
        image_subfix = ['jpg', 'jpeg', 'png']
        for f in os.listdir(dirname):
            subfix = f.split('.')[-1]
            if subfix not in image_subfix:
                continue
            else:
                self.file_list.append(f)
                
        self.file_count = len(self.file_list)
    
    def get(self, randbg = True):
        index = self.index
        if randbg:
            index = RDI(0, self.file_count - 1)
        else:
            self.index = (index + 1) % self.file_count
        
        imname = self.file_list[index]
        full_path = os.path.join(self.dirname, imname)
        self.current_image = full_path
        return Image.open(full_path)

#***********************************************************************        
class BackgroundGen(object):
    def __init__(self, uri, method="local", randbg = True):
        self.img_loader = None
            
        if method == 'local':
            self.img_loader  = LocalImgLoader(uri)
        else:
            self.img_loader = NetworkImgLoader(uri)
        self.randbg = randbg
        
    def gen(self, bgparam):
        dest_size = None
        if 'dest_size' in bgparam:
            dest_size = bgparam['dest_size']
        bg = self.img_loader.get(self.randbg)
        bgparam["img"] = bg
        bg = BgJitter(bgparam).jitter()
        if dest_size is not None and bgparam['resize']:
            bg = bg.resize(dest_size)
        return bg
if __name__ == '__main__':  
    import cv2
    import numpy as np
    bgg = BackgroundGen(r"E:\zm\backgrounds", 'local', True)
    '''
    for x in range(10):
        bg = bgg.gen(
            dest_size = (120, 50),
            random_line = True,
            random_text = True
        )
    '''    
    dest = r'I:\barcodes\background'    
    for x in range(50000):
        bg = bgg.gen(
            {'dest_size': (96, 96), 'resize': True}
        )
        bg = cv2.cvtColor(np.asarray(bg),cv2.COLOR_RGB2BGR)
        fname = os.path.join(dest, 'bg_%d.jpg'%x)
        cv2.imwrite(fname, bg)
    #cv2.imshow('test',bg)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    