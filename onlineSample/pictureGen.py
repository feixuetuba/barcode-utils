#-*- coding:utf-8 -*-
#generate barcode image

import math
from random import randint as RDI
try:
    from onlineSample.barcodeGen import BarcodeGen as BGen
    from onlineSample.backgroundGen import BackgroundGen as BgGen
except:
    from barcodeGen import BarcodeGen as BGen
    from backgroundGen import BackgroundGen as BgGen
#from PIL import Image, ImageDraw

class PictureGen:
    def __init__(self, try_count, overlap, bgen, bggen):
        self.bgen = bgen
        self.try_count = try_count
        self.bggen = bggen
        self.overlap = overlap
        
    def gen(self, barcode_per_img, dest_size, bsize, bgen_param, bggen_param):
        
        bg = self.bggen.gen(bggen_param)
        bg_w, bg_h = bg.size
        _bsize = bsize
        if bsize is None:
            v = min(bg_w, bg_h)
            v = int(v * 0.8)
            _bsize = (v, v)
        
        w_ratio = 1.0 * dest_size[0] / bg_w
        h_ratio = 1.0 * dest_size[1] / bg_h
        records = []
        temp_r = []
        for index in range(barcode_per_img):
            record = {}
            encoding, code, barcode = self.bgen.gen(**bgen_param)
            b_w, b_h = barcode.size
            for trail in range(self.try_count):
                _barcode_img = self.__resize(barcode, _bsize)
                raw_w, raw_h = _barcode_img.size                 #PIL return w and h
                
                angle, _barcode = self.__rotate(_barcode_img)
                roated_w, rotated_h = _barcode.size
                delta = 0
                '''
                while bg_w < roated_w or bg_h < rotated_h:
                    minv = min(bg_w, bg_h) - delta
                    _barcode = self.__resize(_barcode, [minv/2, minv])
                    roated_w, rotated_h = _barcode.size
                    delta += 10
                '''
                #print("bg:(%d,%d), barcode:(%d,%d)"%(bg_w, bg_h, roated_w, rotated_h))
                pos_x, pos_y, success = self.__get_valid_pos(
                                                            temp_r,
                                                            bg_w, bg_h,
                                                            roated_w,
                                                            rotated_h)
                if success == True:
                    left = pos_x
                    top = pos_y
                    
                    temp_r.append({
                        'left': pos_x,
                        'right': pos_x + roated_w,
                        'top': pos_y,
                        'bottom': pos_y + rotated_h
                        }
                    )
                    bg.paste(_barcode, (pos_x, pos_y), _barcode)
                    left = int(pos_x * w_ratio) 
                    top = int(pos_y * h_ratio)
                    roated_w = int(w_ratio * roated_w)
                    rotated_h = int (h_ratio * rotated_h)
                    raw_w = int(raw_w * w_ratio)
                    raw_h = int(raw_h * h_ratio)
                    right = left + roated_w
                    bottom = top + rotated_h
                    points = self.__cal_points(angle, left, top, right, bottom, raw_w, raw_h)
                    records.append({
                        'code': code,
                        'type':encoding,
                        'angle': angle,
                        'w':raw_w,
                        'h':raw_h,
                        'left': left,
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                        'points': points
                    })
                    break
        
        return {'im_w':dest_size[0], 'im_h':dest_size[1], 'barcodes':records}, bg.resize(dest_size)
            
        
    def __rotate(self, image, angle=None):
        if angle is None:   
            angle = RDI(0, 360)
        dest = image.rotate(angle, expand=1)
        return angle, dest
    
    def __resize(self, image, barcode_size):
        if barcode_size != None:
            _w, _h = image.size
            w = RDI(*barcode_size)
            h = int(1.0 * _h * w / _w)#RDI(*barcode_size)
            image = image.resize((w, h))
        return image 
        
    def __get_valid_pos(self, records, max_x, max_y, w, h):
        if max_x < w or max_y < h:
            return None, None, False
        for i in range(self.try_count):
            x = RDI(0, max_x - w)
            y = RDI(0, max_y - h)
            if x < 0 or y < 0:
                return None, None, False
                
            r = x + w
            b = y + h
            if self.__pos_is_valid(records, (x, y, r, b)):
                return x, y, True
        return None, None, False

    def __pos_is_valid(self, records, bbox):
        if self.overlap is True:
            return True
        l1 = bbox[0]
        t1 = bbox[1]
        r1 = bbox[2]
        b1 = bbox[3]
        #infos = [str(bbox)]
        for r in records:
            l2 = r['left']
            t2 = r['top']
            r2 = r['right']
            b2 = r['bottom']
            #infos.append(str([l2, t2, r2, b2]))
            if b1 <= t2 or t1 >= b2:
                continue
            if l2 <= l1 and l1 < r2:
                return False
            elif l1 <= l2 and l2 <= r1:
                return False
        #LOGGER.info(" ".join(infos))
        return True 
    
    def __cal_points(self, angle, left, top, right, bottom, raw_w, raw_h):
        points = []
        if angle > 180:
            angle -= 180
        if angle <= 90:
            angle = 1.0 * angle / 180.0 * math.pi
            cos_angle = math.cos(angle)
            sin_angle = math.sin(angle)
            points.append((int(left + raw_w * cos_angle), top))
            points.append((right, int(top + raw_h * cos_angle)))
            points.append((int(right - raw_w * cos_angle), bottom))
            points.append((left, int(top + raw_w * sin_angle)))
        else:
            angle = 180 - angle
            angle = 1.0 * angle / 180.0 * math.pi
            cos_angle = math.cos(angle)
            sin_angle = math.sin(angle)
            points.append((int(left + raw_h * sin_angle), top))
            points.append((right, int(top + raw_w * sin_angle)))
            points.append((left + int(raw_w * cos_angle), bottom))
            points.append((left, top + int(raw_h * cos_angle)))
        return points

if __name__ == '__main__':
    import cv2
    import numpy as np
    
    bg_param = {
         'dest_size': (640, 480), 
         'random_line': True, 
         'random_text': True
    }
    
    barcode_parm = {
        'encoding': 'ean',
        'code': None
    }
    
    bg_gen = BgGen(
        uri = r'G:\dataset\data\images\backgrounds',
        method = 'local',
        randbg = True
    )
    
    barcode_gen = BGen()
    pgen = PictureGen(5, False, barcode_gen, bg_gen)
    info, image = pgen.gen(
        barcode_per_img = 5, 
        dest_size = (640, 480), 
        bsize = (32, 32), 
        bgen_param = barcode_parm, 
        bggen_param = bg_param
    )
    image = cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)
    
    w_ratio = 112. / 640
    h_ratio = 112. / 480
    '''
    cv2.imshow('test',image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    exit()
    '''
    #test label
    for barcode in info['barcodes']:
        left = int(barcode['left'] )
        right = int(barcode['right'])
        top = int(barcode['top'])
        bottom = int(barcode['bottom'])
        cv2.rectangle(image, (left, top), (right, bottom), (0,0,255), thickness=2)
        
        ps = barcode['points']
        cv2.line(image, ps[0], ps[1], (0,255,0), thickness=2)
        cv2.line(image, ps[1], ps[2], (0,255,0), thickness=2)
        cv2.line(image, ps[2], ps[3], (0,255,0), thickness=2)
        cv2.line(image, ps[3], ps[0], (0,255,0), thickness=2)
        
        center_x = (left + right) / 2
        center_y = (top + bottom) / 2
        cv2.circle(image, (center_x, center_y), 3, (255, 0, 0), thickness=2)
        
    cv2.imshow('test',image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()