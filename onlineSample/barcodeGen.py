#-*- coding:utf-8 -*-
from io import BytesIO as BIO
from PIL import Image, ImageDraw
import barcode
from barcode.writer import ImageWriter
from PIL import ImageFilter as IFilter
from random import randint as RDI

class BarcodeGen(object):
    def __init__(self):
        self.encodings = ['ean13', 'ean8', 'code39', 'isbn', 'upc']
        self.code39_charsets = [chr(65 + x) for x in range(0, 26)]
        self.code39_charsets += [str(x) for x in range(0, 10)]
        self.code39_charsets += ['-', '.', ' ', '$', '/', '+', '%']
        self.cellw = 5
        pass
    
    def gen(self, encoding, code = None, mode = "FULL"):
        #encodings = ['ean13']
        if encoding is None:
            encoding = self.encodings[RDI(0, len(self.encodings) - 1)]
        if type(code) is not str:
            code = self.__gen_rand_str(encoding)
        bclass = barcode.get_barcode_class(encoding)
        writer=ImageWriter()
        writer.set_options({"module_width":0.1})
        result = bclass(code, writer=writer)
        img = self.__get_image(result)
        core = self.__get_core(img, encoding, mode)
        return encoding, code, core
    
    def __get_image(self, barcode):
        bio = BIO()
        barcode.write(bio)
        bio = BIO(bio.getvalue())
        bio.seek(0)
        return Image.open(bio).convert('RGBA') 
        
    def __get_core(self, barcode_img, encoding, mode = "FULL"):
        width, height = barcode_img.size
        w = width / self.cellw
        h = height / self.cellw
        left = 0
        top = 0
        right = width
        bottom = height
        
        scales ={
            "FULL":1
            ,"LITE":0.5
            ,"None":0
        }
        
        s = scales[mode]
        if encoding == 'ean13' or encoding == 'ean8' or encoding == 'ean':
            left = 14 * s * self.cellw      
            top = 2 * s * self.cellw
            right = (w-12*s) * self.cellw
            bottom = (h - 18*s) * self.cellw
        elif encoding == "code39":
            left = 6 * s * self.cellw
            top = 2 * s * self.cellw
            right = (w-6*s) * self.cellw
            bottom = (h - 18*s) * self.cellw
        elif encoding == 'isbn':
            left = 15 * s * self.cellw
            top = 2 * s * self.cellw
            right = (w-14*s) * self.cellw
            bottom = (h - 18*s) * self.cellw

        barcode_img = barcode_img.crop((left, top, right, bottom))
        width, height = barcode_img.size
        ratio = 1.0 * height /width
        if ratio < 0.6:
            height = int(width * RDI(6, 9) / 10)
        return barcode_img.resize((width, height), Image.ANTIALIAS)
        
    def __gen_rand_str(self, encoding):
        code = []
        if encoding in ['ean13','ean8', 'ean', 'upc']:
            code = [str(RDI(0, 10)) for _ in range(11)]
        elif encoding == 'code39':
            length = RDI(11, 15)
            code = [self.code39_charsets[RDI(0, 42)] for _ in range(length)]
        elif encoding == 'isbn':
            code = ['9', '7', str(RDI(8, 9))]
            _code = [str(RDI(0, 10)) for _ in range(10)]
            code += _code
        return ''.join(code)
        
if __name__ == '__main__':
    import cv2
    import numpy as np
    import os
    import time
    from random import randint as RDI
    bgen = BarcodeGen()
    '''
    dest_dir = r'G:\dataset\experiment\classify\train'
    for btype in ['ean13', 'ean8', 'code39', 'isbn', 'upc']:
        startt = time.time()
        for x in range(50000):
            encoding, code, image = bgen.gen(btype, mode=False)
            #angle = RDI(0, 30)
            #image = image.rotate(angle, expand=1)
            
            image = np.asarray(image)
            rol, col, chanel = image.shape
            fname = "%s_%d.jpg"%(btype, x)  
            image = image = cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2GRAY)
            image = image[100:101, :]
            image = cv2.resize(image, (112, 1))
            cv2.imwrite(os.path.join(dest_dir, fname), image)
        elapse = time.time() - startt
        print('%s avg:%s/per'%(btype, elapse/ 5000))
    '''
    btype = 'ean'
    encoding, code, image = bgen.gen(btype, mode = 'FULL')
    image = cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)
    #h, w, _ = image.shape
    #w = 56 
    #h = int (56.0 /w * h)
    #image = cv2.resize(image, (h, w))
    cv2.imshow("test", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    