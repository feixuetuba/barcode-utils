#-*- coding:utf-8 -*-
import cv2
import numpy as np
import os
import json

def point_in_range(point, points, scale, threshold = 0): 
        p1 = np.array(points[0]) * scale
        p2 = np.array(points[1]) * scale
        p3 = np.array(points[2]) * scale
        p4 = np.array(points[3]) * scale
        vectors = []
        vectors.append(p2 - p1)
        vectors.append(p3 - p2)
        vectors.append(p4 - p3)
        vectors.append(p1 - p4)
        
        point = np.array(point)
        pvectors = []
        pvectors.append(point - p1)
        pvectors.append(point - p2)
        pvectors.append(point - p3)
        pvectors.append(point - p4)
        for pv, xpv in zip(pvectors, vectors):
            if np.dot(pv, xpv) < threshold:
                return False
        return True

def l2t(data, scale):
    return (data[0], data[1])
        
def barkcode_mark(mask, barcode_info, scale):
    for barcode in barcode_info['barcodes']:
        left = int(barcode['left'] * scale[0])
        right = int(barcode['right'] * scale[0])
        top = int(barcode['top'] * scale[1])
        bottom = int(barcode['bottom'] * scale[1])
        #cv2.rectangle(img, (left, top), (right, bottom), (0,0,255), thickness=2)
        
        ps = barcode['points']
        #cv2.line(img, l2t(ps[0]), l2t(ps[1]), (0,255,0), thickness=2)
        #cv2.line(img, l2t(ps[1]), l2t(ps[2]), (0,255,0), thickness=2)
        #cv2.line(img, l2t(ps[2]), l2t(ps[3]), (0,255,0), thickness=2)
        #cv2.line(img, l2t(ps[3]), l2t(ps[0]), (0,255,0), thickness=2)
        
        top = max(top - 1, 0)
        bottom = min(bottom + 1, 112)
        left = max(left -1, 0)
        right = min(right + 1, 112)
        for rol in range(top, bottom):
            for col in range(left, right):
                if point_in_range((col, rol), barcode['points'], scale):
                    mask[rol, col, :] = (0, 0, 0)
    return mask
    
if __name__ == '__main__':
    dirname = r'G:\test'
    record = os.path.join(dirname, '_record.txt')
    with open(record, 'r') as fd:
        for line in fd.readlines():
            mask = np.ones([112, 112, 3], dtype=np.uint8)
            info = json.loads(line)
            img = cv2.imread(os.path.join(dirname, info['filename']))
            #img = cv2.resize(img, (112, 112))
            mask = barkcode_mark(mask, info, np.array([112.0/112, 112.0/112]))
            
            mask = cv2.resize(mask, (112, 112))
            cv2.imshow('test', img * mask)
            key = cv2.waitKey(0)
            cv2.destroyAllWindows()
            if key & 0xFF == 27:
                exit()
            
           