import os
import platform
import numpy as np
import cv2
import copy
import json
import math
import time, datetime
from onlineSample import sampleGen
from threading import Lock, Thread

CPICKLE = None
VERSION = platform.python_version()
if VERSION.split('.')[0] == '2':
	import cPickle
	CPICKLE = cPickle
else:  
	import pickle
	CPICKLE = pickle
	xrange = range

class BarcodeDS(object):
    
    def __init__(self,
                background_dir, 
                barocode_width,
                barcode_per_img,
                image_size,
                label_size,
                batch_size
                ):
        
        self.bg_dir = background_dir
        self.barocode_width = barocode_width
        self.barcode_per_img = barcode_per_img
        
        self.batch_size = batch_size
        print ("batchsize:%d"%self.batch_size) 
        self.image_size = image_size
        self.label_size = label_size
        self.label_depth = 7
        self.cursor = 0
        self.gt_labels = []
        self.current_imgs = []
        self.current_labels = []
        self.sample_count_min = 3
        self.sample_prepare = Lock()
        self.prepare_enabled = Lock()
        self.generated_thread = None
        self.running = False
        self.batch_count = 10
        self.prepare()
        self.batch_count = 20
        
    def get_current_imgs(self):
        return self.current_imgs
    
    def get_current_labels(self):
        return self.current_labels
    
    def get(self):
        images = np.zeros((self.batch_size, self.image_size, self.image_size, 1))
        labels = np.zeros((self.batch_size, self.label_size, self.label_size, self.label_depth))
        count = 0
        self.current_imgs = []
        self.current_labels = []
        
        while len(self.gt_labels) <= 1:
            time.sleep(1)
            
        samples = self.gt_labels.pop()
        for sample in samples:
            self.current_imgs.append(sample['image'])
            image = self.image_adjust(sample['image'])
            label = sample['label']
            self.current_labels.append(sample['info'])
            #image, label = self.jitter.random_jitter(image, label, self.jittered)
            images[count, :, :, :] = np.reshape(image,(self.image_size, self.image_size, 1))
            labels[count, :, :, :] = label
            
            self.cursor += 1
            if len(self.gt_labels) <= 20:
                self.prepare()
                self.cursor = 0
        return images, labels

    def image_adjust(self, image):
        #print(imname)
        #image = cv2.resize(image, (self.image_size, self.image_size))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
        image = (image / 255.0) * 2.0 - 1.0
        return image

    def stop(self):
        print("dataset stop ...")
        self.prepare_enabled.acquire()
        #print('1')
        self.running = False
        print('2')
        self.sample_prepare.release()
        #self.generated_thread.join(1)
        print("dataset stoped")
        
    def prepare(self):
        if self.prepare_enabled.acquire(False):
            if self.generated_thread is None:
                self.generated_thread = Thread(
                                target= self.sample_prepare_func
                                )
                self.running = True
                self.generated_thread.start()
            else:
                self.sample_prepare.release()

    def sample_prepare_func(self):
        while self.running:
            self.sample_prepare.acquire()
            if not self.running:
                break
                
            for c in range(self.batch_count):
                if not self.running:
                    break
                samples = sampleGen.sample_get(
                    (self.image_size, self.image_size),
                    self.bg_dir,
                    self.barocode_width,
                    self.barcode_per_img,
                    self.batch_size, True, True
                    )
                for index, s in enumerate(samples):    
                    samples[index]['label'] = self.load_labels(samples[index]['info'])
                self.gt_labels.append(samples)
                #print(c)
            #print("%d x %d generated"%(self.batch_size, self.batch_count))
            self.prepare_enabled.release()
            
    def load_labels(self, label):
        record = json.loads(label)
        label, num = self.load_barcode_annotation(record)  
        return label

    def point_in_range(self, point, points, vectors, threshold = -5):
        pvectors = []
        pvectors.append(point - points[0])
        pvectors.append(point - points[1])
        pvectors.append(point - points[2])
        pvectors.append(point - points[3])
        for pv, xpv in zip(pvectors, vectors):
            if np.dot(pv, xpv) < threshold:
                return False
        return True
        
    def label_mark(self, label, bbox, points):
        vectors = []
        vectors.append(points[1] - points[0])
        vectors.append(points[2] - points[1])
        vectors.append(points[3] - points[2])
        vectors.append(points[0] - points[3])
        
        for y in xrange( int(bbox[1]), int(bbox[3]) ):
            for x in xrange( int(bbox[0]), int(bbox[2])):
                if self.point_in_range((x,y), points, vectors):
                    label[y][x][1] = 1
                    label[y][x][0] = 0
        
    def load_barcode_annotation(self, record):
        """
        Load image and bounding boxes info from json file in the barcode record
        format.
        {"count": 1, "barcodes": [{"code": "145896100819", "right": 147, "angle": 113, 
        "w": 80, "bottom": 436, "h": 106, "top": 330, "type": "ean13", 
        "points": [[109.34322325881226, 330], [147, 416.5274562245294], 
        [103.72872607799172, 436], [67, 347.9736319105066]],
        "left": 67}], "filename": "0.png"}
        """
        h_ratio = 1.0 * self.label_size / self.image_size
        w_ratio = 1.0 * self.label_size / self.image_size

        #labels = []
        #background = np.ones((self.label_size, self.label_size))
        #barcodes = np.zeros((self.label_size, self.label_size))
        label = np.zeros([self.label_size, self.label_size, self.label_depth])
        #label[:, :, 0] = 1
        objs = record['barcodes']
        #if len(objs) == 0:
        #    print("%s withou label!"%record['filename']) 
        
        for i,obj in enumerate(objs):
            #label = []
            # Make pixel indexes 0-based
            '''
            points = obj['points']
            scale = np.array([w_ratio, h_ratio])
            p1 = np.array(points[0]) * scale
            p2 = np.array(points[1]) * scale
            p3 = np.array(points[2]) * scale
            p4 = np.array(points[3]) * scale
            '''
            #x1 = max(min((float(obj['left']) - 1) * w_ratio, self.image_size - 1), 0)
            #y1 = max(min((float(obj['top']) - 1) * h_ratio, self.image_size - 1), 0)
            #x2 = max(min((float(obj['right']) - 1) * w_ratio, self.image_size - 1), 0)
            #y2 = max(min((float(obj['bottom']) - 1) * h_ratio, self.image_size - 1), 0)
            x1 = obj['left']
            y1 = obj['top']
            x2 = obj['right']
            y2 = obj['bottom']
            center_x = 1.0 * (x1 + x2) / 2.0 * w_ratio
            center_y = 1.0 * (y1 + y2) / 2.0 * h_ratio
            i_cx = int(center_x)
            i_cy = int(center_y)
            label[i_cy, i_cx, 0] = 1
            #label[i_cy, i_cx, 1] = 1
            #print("label:%d,%d"%(i_cx, i_cy))
            angle = obj['angle'] % 180
            if angle > 90:
                label[i_cy, i_cx, 1] = 1
                angle -= 90
            angle = int(angle/10)
            label[i_cy, i_cx, 2] = angle
            label[i_cy, i_cx, 3] = center_x - i_cx
            label[i_cy, i_cx, 4] = center_y - i_cy
            ratio = 1.4 * obj['w'] / self.image_size
            '''
            if ratio < 0.92:
                ratio += 0.08
            '''
            if  ratio >= 1.0:
                label[i_cy, i_cx, 5] = 9
                label[i_cy, i_cx, 6] = 0.9
            else:
                label[i_cy, i_cx, 5] = int(ratio * 10)
                label[i_cy, i_cx, 6] = ratio * 10 - label[i_cy, i_cx, 5]
            #self.label_mark(label, (x1, y1, x2, y2), (p1, p2, p3, p4))
        return label, len(objs)