#-*- coding:utf-8 -*-
'''
条形码样本标注器，运行环境python3.6
依赖库:opencv-python
'''
import cv2
import math
import numpy as np
import os
import json
from threading import Thread
    
class Marker:
    def __init__(self, input_dir, output_dir, mode='create'):
        self.inputd = input_dir
        self.outputd = output_dir
        self.mode = mode
        self.recordf = os.path.join(output_dir, '_record.txt')
        self.ops = 0
        self.img_list = []
        self.pos_list = []
        self.barcodes = []
        self.records = []
        self.current_img = None
        self.mask = np.zeros((448, 448, 3), dtype=np.uint8)
        self.running = False
        self.tshow = Thread(target=self.imshow)
        self.cimname = "-"
        if mode == 'create':
            self.prepare()
            self.save = self.write_record
        elif mode == 'modify':
            self.mprepare()
            self.save = self.save_record
        
    def start(self):
        self.next()
        self.running = True
        self.tshow.start()
        
        
    def modify(self, imnames):
        if self.mode != "modify":
            raise('Mode should be "modify"')
        def pop_record(imname):
            for i,r in enumerate(self.records):
                if r['filename'] == imname:
                    return self.records.pop(i)
        if type(imnames) != list:
            imnames = [imnames]
        for im in imnames:
            record = pop_record(im)
        self.img_list = images
        self.inputd = self.outputd
        self.start()

    def showop(self, string):
        self.ops += 1
        print("[%d] %s"%(self.ops, string))
    
    def imread(self, impath):
        img = cv2.imread(impath)
        if img is None:
            return None
        img = cv2.resize(img, (448, 448))
        return img

    def cal_msic(self, points):
        delta_y = points[0][1] - points[1][1]
        delta_x = points[1][0] - points[0][0]
        if delta_x == 0:
            angle = 90
        else:
            angle = math.atan(delta_y / delta_x )/ math.pi * 180
            angle = int(angle)
            if angle < 0:
                angle = 180 + angle
        width = math.sqrt(pow(delta_x, 2) + pow(delta_y, 2))
        
        delta_y = points[3][1] - points[0][1]
        delta_x = points[3][0] - points[0][0]
        height = math.sqrt(pow(delta_x, 2) + pow(delta_y, 2))
        
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        left,top = (min(xs), min(ys))
        right,bottom = (max(xs), max(ys))
        return left,top,right,bottom,width,height,angle
    
    def imshow(self):
        
        cv2.namedWindow('Marker')
        cv2.setMouseCallback('Marker',self.on_click)
        while self.running:
            if type(self.current_img) != None :
                m = np.equal(self.mask, 0).astype(np.uint8)
                nim = self.current_img * m + self.mask
                cv2.imshow('Marker',nim)
                key = cv2.waitKey(1) & 0xFF
                self.on_key(key)
        cv2.destroyAllWindows()
    
    def on_key(self, key):
        if key == 27:
            self.finished()
        elif key == 13:
            self.save()
            self.next()
    
    def on_click(self, event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONUP:
            self.showop("add pos:(%d,%d)"%(x, y))
            self.pos_list.append([x,y])
            cv2.circle(self.mask, (x,y), 2, color=(0,255,0), thickness=2)
            if len(self.pos_list) == 4:
                self.add_barcode()
                self.pos_list = []
        elif event == cv2.EVENT_RBUTTONUP:
            if len(self.pos_list) > 0:
                self.ops += 1
                pos = self.pos_list.pop()
                print("[%d] remove pos:(%d,%d)"%(self.ops, pos[0], pos[1]))
                cv2.circle(self.mask, (pos[0],pos[1]), 2, color=(0,0,0), thickness=2)
            else:
                self.pos_list = self.remove_barcode()
                
    def add_barcode(self):
        left,top,right,bottom,width,height,angle = self.cal_msic(self.pos_list)
        barcode = {
            'code':'unknown',
            'type':'unknown',
            'angle':angle,
            'w':width,
            'h':height,
            'left':left,
            'top':top,
            'right':right,
            'bottom':bottom,
            "points":self.pos_list
        }
        cv2.rectangle(self.mask, (left, top), (right, bottom), (255,0,0), thickness=2)
        self.barcodes.append(barcode)
        
        self.showop("add barcode, angle:%d"%angle)
    
    def remove_barcode(self):
        self.showop("remove barcode")
        if len(self.barcodes) == 0:
            return []
        b = self.barcodes.pop()
        cv2.rectangle(self.mask, (b['left'], b['top']), (b['right'], b['bottom']), (0,0,0), thickness=2)
        ps = b['points']
        d = ps.pop()
        cv2.circle(self.mask, (d[0],d[1]), 2, color=(0,0,0), thickness=2)
        for d in ps:
            cv2.circle(self.mask, (d[0],d[1]), 2, color=(0,255,0), thickness=2)
        return b['points']
    
    def prepare(self):
        self.img_list = os.listdir(self.inputd)
        if os.path.isfile(self.recordf):
            with open(self.recordf, 'r') as fd:
                for line in fd.readlines():
                    record = json.loads(line)
                    fname = record['filename']
                    if fname in self.img_list:
                        idx = self.img_list.index(fname)
                        self.img_list.pop(idx)
        self.recordf = open(self.recordf, 'a')
    
    def mprepare(self):
        self.img_list = os.listdir(self.inputd)
        with open(self.recordf, 'r') as fd:
            for line in fd.readlines():
                self.records.append(json.loads(line))
    
    def next(self):
        if len(self.img_list) != 0:
            imname = self.img_list.pop(0)
            self.current_img = self.imread(os.path.join(self.inputd, imname))
            cv2.imwrite(os.path.join(self.outputd, imname), self.current_img)
            self.mask = self.mask * 0
            self.cimname = imname
        else:
            self.finished()
    
    def write_record(self):
        record = {
            'filename':self.cimname,
            'im_w':448,
            'im_h':448,
            'barcodes':self.barcodes
        }
        self.recordf.write("%s\n"%json.dumps(record))
        self.barcodes = []
        self.pos_list = []
        self.showop("save record")
    
    def save_record(self):
        record = {
            'filename':self.cimname,
            'im_w':448,
            'im_h':448,
            'barcodes':self.barcodes
        }
        self.records.append(record)
        self.barcodes = []
        self.pos_list = []
    
    def finished(self):
        if self.mode == 'create':
            self.recordf.close()
        elif self.mode == 'modify':
            with open(os.path.join(self.output_dir, '_record.txt'), 'w'):
                for r in self.records:
                    fd.write("%s\n"%json.dumps(r))
        self.running = False
        
def get_arg():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-m', '--mode', dest='mode', default='create', help='the running mode <crete|modify>')
    parser.add_argument('-i', '--input', dest='inputd', default=None, help='input directory ')
    parser.add_argument('-o', '--output', dest='outputd', default=None, help='the output directory')
    parser.add_argument('-f', '--filelist', dest='rfile', default=None, help='the file for modify filelist')
    return parser.parse_args()

def run():
    import sys
    args = get_arg()
    modify_fs = []
    if args.rfile != None:
        with open(args.rfile, 'r') as fd:
            modify_fs = []
            for line in fd.readlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                modify_fs.append(line)
    if args.outputd is None:
        raise Exception('use -o to specify output directory')
    if args.mode == 'create':
        if args.inputd is None:
            raise Exception('use -i to specify the input directory')
        m = Marker(args.inputd, args.outputd, args.mode)
        m.start()
    elif args.mode == 'modify':
        if len(modify_fs) == 0:
            raise Exception("no file should be modified!")
        m = Marker(args.inputd, args.outputd, args.mode)
        m.modify(modify_fs)
    else:
        print("No such mode:%s"%args.mode)
    
if __name__ == '__main__':
    print(u"请沿着条形码识读方向顺时针依次点击条码的个顶点，右击图像任意位置将依次删除角点，按回车键保存标注。")
    run()