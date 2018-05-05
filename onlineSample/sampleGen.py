#-*- coding:utf-8 -*-
import os
import time, datetime
import cv2
import json
import platform
import json
from optparse import OptionParser
import numpy as np
try:
    from onlineSample.barcodeGen import BarcodeGen as BGen
    from onlineSample.backgroundGen import BackgroundGen as BgGen
    from onlineSample.pictureGen import PictureGen as PGen
except :
    from barcodeGen import BarcodeGen as BGen
    from backgroundGen import BackgroundGen as BgGen
    from pictureGen import PictureGen as PGen
from random import randint as RDI

CPICKLE = None
ATOI = None
VERSION = platform.python_version()
if VERSION.split('.')[0] == '2':
    import cPickle
    import string
    CPICKLE = cPickle
    ATOI = string.atoi
else:  
    import pickle
    CPICKLE = pickle
    xrange = range
    ATOI = int




def sample_get(
    dest_size,
    background_dir,
    barcode_width_range,
    barcode_num_per_img,
    count,
    random_line = False,
    random_text = False,
    random_rotate = True,
    random_crop = True,
    
    bg_resize = False,
    ):


    bg_param = {
        'dest_size': dest_size, 
        'lines': random_line, 
        'character': random_text,
        'rotate': random_rotate,
        'resize': bg_resize
    }

    
    bg_gen = BgGen(
        uri = background_dir,
        method = 'local',
        randbg = True
    )
    
    barcode_gen = BGen()
    pgen = PGen(5, False, barcode_gen, bg_gen)
    
    samples = []
    barcode_count_range = 0
    if type(barcode_num_per_img) is tuple:
        barcode_count_range = barcode_num_per_img
    else:
        barcode_count_range = (barcode_num_per_img, barcode_num_per_img)
    btypes = ['ean13','ean8', 'isbn', 'ean', 'upc']\

    for x in range(1, count+1):
        barcode_parm = {
            'encoding': None,
            'code': None,
            'mode':'LITE'
        }
        info, image = pgen.gen(
            barcode_per_img = RDI(barcode_count_range[0], barcode_count_range[1]), 
            dest_size = dest_size, 
            bsize = barcode_width_range, 
            bgen_param = barcode_parm, 
            bggen_param = bg_param
        )
       
        #image = cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)
        samples.append({
            'image': image,
            'info': info
        })
        
    return samples
    
if __name__ == '__main__':
    count = 1000                    #生成多少张图片
    report_iter = 10                #汇报间隔
    start_index = 0               #图片名称起始值
    dest_dir = r'I:\barcodes\valid'    #图片输出目录
    background_dir = r'I:\barcodes\background'      #背景图片目录
    barcode_count = (3,5)               #每张图片的条码个数上限
    dest_img_size = (448, 448)      #目标图片大小
    barcode_size = (100, 300)       #图片中条码长度,为None表示按实际大小
    random_line = False              #是否在背景中加入随机线条
    random_text = False               #是否在背景中加入随机文字
    random_rotate = False            #是否对背景进行随机旋转
    random_crop = False              #是否对背景进行随机裁剪
    bg_resize = True                #加入条码前是否对背景进行缩放
    batch_size = 5000
    
    
    record_file = os.path.join(dest_dir, '_record.txt')
    if os.path.isfile(record_file):
        record_file = open(record_file, 'a', buffering=20480)   #默认是行缓冲，这里改成字节缓冲
    else:
        record_file = open(record_file, 'w', buffering=20480)
    
    print ("start")
    start_time = time.time()
    try:
        i = 0
        bs = batch_size
        bs = min(batch_size, count - i)
        start_time = time.time()
        while bs > 0:
            samples = sample_get(
                        dest_img_size,
                        background_dir,
                        barcode_size,
                        barcode_count,
                        bs,
                        random_line, random_text,
                        random_rotate,random_crop,bg_resize
                        )
            total = time.time() - start_time            
            for sample in samples:
                file_name =  "%d.jpg"%(start_index + i)
                dest_file = os.path.join(dest_dir, file_name)
                sample['image'].save(dest_file)
                #cv2.imwrite(dest_file, sample[0]['image'])
                sample['info']['filename'] = file_name
                
                record_file.write("%s\n"%json.dumps(sample['info']))
                i += 1
            bs = min(batch_size, count - i)
            stop_time = time.time()
            elapse = stop_time - start_time
            avg = elapse / i
            remain = (count - i) * avg
            print("%d finished, remain:%s"%(i, str(datetime.timedelta(seconds=int(remain)))))
    except KeyboardInterrupt:
        record_file.close()