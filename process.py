import glob
import itertools
import math
import numpy as np
import os
import PIL.Image as pilImage
import PIL.ImageChops as pilChops
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import rawpy
import random
import sys
import time
from dynamic_viewer import CurveletControl
from math import pi as Pi
import pyct
from PyQt5 import QtCore, QtGui, QtWidgets
import copy

class Image(object):

    def __init__(self):
        super(Image,self).__init__()
        self.supportedRawFormats = {'.3fr','.ari','.arw','.srf','.sr2','.bay','.cri','.crw','.cr2','.cr3','.cap','.iiq','.eip', \
                            '.dcs','.dcr','.drf','.k25','.kdc','.dng','.erf','.fff','.mef','.mdc','.mos','.mrw','.nef', \
                            '.nrw','.orf','.pef','.ptx','.pxn','.r3d','.raf','.raw','.rw2','.rwl','.rwz','.srw','.x3f', \
                            '.3FR','.ARI','.ARW','.SRF','.SR2','.BAY','.CRI','.CRW','.CR2','.CR3','.CAP','.IIQ','.EIP', \
                            '.DCS','.DCR','.DRF','.K25','.KDC','.DNG','.ERF','.FFF','.MEF','.MDC','.MOS','.MRW','.NEF', \
                            '.NRW','.ORF','.PEF','.PTX','.PXN','.R3D','.RAF','.RAW','.RW2','.RWL','.RWZ','.SRW','.X3F'}
        self.supportedImageFormats = {'.bmp','.eps','.gif','.icns','.ico','.im','.jpg','.jpeg','.jpeg2000','.msp','.pcx',\
                                      '.png','.ppm','.sgi','.tiff','.tif','.xbm','.BMP','.EPS','.GIF','.ICNS','.ICO','.IM','.JPG','.JPEG','.JPEG2000','.MSP','.PCX',\
                                      '.PNG','.PPM','.SGI','.TIFF','.TIF','.XBM'}

    def get_image(self,bit_depth,img_path,EnableAutoWB, Brightness, UserBlack, image_crop,img_type='numpy_array'):
        pathExtension = os.path.splitext(img_path)[1]
        if pathExtension in self.supportedRawFormats:
            img_raw = rawpy.imread(img_path)
            img_rgb = img_raw.postprocess(demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD, output_bps = bit_depth, use_auto_wb = EnableAutoWB,bright=Brightness/100,user_black=UserBlack)
            img_bw = (0.21*img_rgb[:,:,0])+(0.72*img_rgb[:,:,1])+(0.07*img_rgb[:,:,2])
            if image_crop:
                crop0 = max(0,image_crop[0])
                crop1 = min(len(img_bw)-1,image_crop[1])
                crop2 = max(0,image_crop[2])
                crop3 = min(len(img_bw[0])-1,image_crop[3])
                img_array = img_bw[crop0:crop1,crop2:crop3]
            if bit_depth == 16:
                img_array = np.uint8(img_array/256)
            if bit_depth == 8:
                img_array = np.uint8(img_array)
        elif pathExtension in self.supportedImageFormats:
            img = pilImage.open(img_path)
            img_rgb = np.fromstring(img.tobytes(),dtype=np.uint8)
            img_rgb = img_rgb.reshape((img.size[1],img.size[0],3))
            img_array = (0.21*img_rgb[:,:,0])+(0.72*img_rgb[:,:,1])+(0.07*img_rgb[:,:,2])
        if img_type == 'numpy_array':
            return img_array
        elif img_type == 'pillow_image':
            return self.nparray2pilImg(img_array)
        elif img_type == 'QImage':
            return self.nparray2qImg(img_array)
        elif img_type == 'QPixmap':
            return self.nparray2qPixImg(img_array)

    def nparray2qPixImg(self,img_array):
        qImg = QtGui.QImage(np.uint8(img_array),img_array.shape[1],img_array.shape[0],img_array.shape[1], QtGui.QImage.Format_Grayscale8)
        qPixImg = QtGui.QPixmap(qImg.size())
        QtGui.QPixmap.convertFromImage(qPixImg,qImg,QtCore.Qt.MonoOnly)
        return qPixImg

    def pilImg2nparray(self,pilImg):
        return np.asarray(pilImg)

    def pilImg2qPixImg(self,pilImg):
        img_array = np.asarray(pilImg)
        qImg = QtGui.QImage(np.uint8(img_array),img_array.shape[1],img_array.shape[0],img_array.shape[1], QtGui.QImage.Format_Grayscale8)
        qPixImg = QtGui.QPixmap(qImg.size())
        QtGui.QPixmap.convertFromImage(qPixImg,qImg,QtCore.Qt.MonoOnly)
        return qPixImg

    def pilImg2qImg(self,pilImg):
        img_array = np.asarray(pilImg)
        qImg = QtGui.QImage(np.uint8(img_array),img_array.shape[1],img_array.shape[0],img_array.shape[1], QtGui.QImage.Format_Grayscale8)
        return qImg
    
    def nparray2pilImg(self,img_array):
        return pilImage.fromarray(img_array).convert('L')

    def nparray2qImg(self,img_array):
        qImg = QtGui.QImage(np.uint8(img_array),img_array.shape[1],img_array.shape[0],img_array.shape[1], QtGui.QImage.Format_Grayscale8)
        return qImg

    def add_gaussian_noise(self,img,sigma):
        noise = pilChops.Image.eval(pilImage.effect_noise(img.size,sigma), lambda x: x-128)
        img_noisy = pilChops.add(img,noise)
        return img_noisy

    def get_line_scan(self,start,end,img,scale_factor,normalize_to_img_max=True):
        x0,y0,x1,y1 = start.x(),start.y(),end.x(),end.y()
        K_length = max(int(abs(x1-x0)+1),int(abs(y1-y0)+1))
        Kx = np.linspace(x0,min(x1,len(img[0])-1),K_length)
        Ky = np.linspace(y0,min(y1,len(img)-1),K_length)
        LineScanIntensities = np.zeros(len(Kx))
        for i in range(0,len(Kx)):
            try:
                LineScanIntensities[i] = img[int(Ky[i]),int(Kx[i])]
            except:
                pass
        LineScanRadius = np.linspace(0,math.sqrt((x1-x0)**2+(y1-y0)**2),len(Kx))
        normalization_factor = np.amax(np.amax(img)) if normalize_to_img_max else 1
        return LineScanRadius/scale_factor,LineScanIntensities/normalization_factor

    def get_integral(self,start,end,width,img,scale_factor,normalize_to_img_max=True):
        x0,y0,x1,y1 = start.x(),start.y(),end.x(),end.y()
        K_length = max(int(abs(x1-x0)+1),int(abs(y1-y0)+1))
        int_width = int(width)
        Kx = np.linspace(x0,min(x1,len(img[0])-int_width-1),K_length)
        Ky = np.linspace(y0,min(y1,len(img)-int_width-1),K_length)
        LineScanIntensities = np.zeros(len(Kx))
        LineScanRadius = np.linspace(0,math.sqrt((x1-x0)**2+(y1-y0)**2),len(Kx))
        if y1 == y0:
            for i in range (0,len(Kx)): 
                try:
                    LineScanIntensities[i] = np.sum(img[int(Ky[i])-int_width:int(Ky[i])+\
                                        int_width,int(Kx[i])])
                except:
                    pass
        elif x1 == x0:
            for i in range (0,len(Kx)): 
                try:
                    LineScanIntensities[i] = np.sum(img[int(Ky[i]),int(Kx[i])-int_width:\
                                        int(Kx[i])+int_width])
                except:
                    pass
        else:
            slope =(x0-x1)/(y1-y0)
            if abs(slope) > 1:
                try:
                    index = np.asarray([[np.linspace(Ky[i]-int_width,Ky[i]+int_width+1,2*int_width+1),\
                                     np.linspace(Kx[i]-int_width/slope,Kx[i]+(int_width+1)/slope,2*int_width+1)] for i in range(len(Kx))],dtype=int)
                except:
                    pass
            else:
                try:
                    index = np.asarray([[np.linspace(Ky[i]-int_width*slope,Ky[i]+(int_width+1)*slope,2*int_width+1),\
                                     np.linspace(Kx[i]-int_width,Kx[i]+int_width+1,2*int_width+1)] for i in range(len(Kx))],dtype=int)
                except:
                    pass
            try:
                LineScanIntensities = np.sum([img[index[i,0,:],index[i,1,:]] for i in range(len(Kx))],axis=1)
            except:
                pass
        normalization_factor = np.amax(np.amax(img)) if normalize_to_img_max else 1
        return LineScanRadius/scale_factor,LineScanIntensities/2/width/normalization_factor

    def get_chi_scan(self,center,radius,width,chiRange,tilt,img,chiStep=1,normalize_to_img_max=True):
        x0,y0 = center.x(),center.y()
        if int(chiRange/chiStep)>2:
            ChiTotalSteps = int(chiRange/chiStep)
        else:
            ChiTotalSteps = 2
        ChiAngle = np.linspace(-chiRange/2-tilt+90,chiRange/2-tilt+90,ChiTotalSteps+1)
        ChiAngle2 = np.linspace(-chiRange/2,chiRange/2,ChiTotalSteps+1)
        x1 = x0 + (radius+width)*np.cos(ChiAngle[1]*np.pi/180)
        y1 = y0 + (radius+width)*np.sin(ChiAngle[1]*np.pi/180)
        x2 = x0 + (radius-width)*np.cos(ChiAngle[1]*np.pi/180)
        y2 = y0 + (radius-width)*np.sin(ChiAngle[1]*np.pi/180)
        x3 = x0 + (radius-width)*np.cos(ChiAngle[0]*np.pi/180)
        y3 = y0 + (radius-width)*np.sin(ChiAngle[0]*np.pi/180)
        x4 = x0 + (radius+width)*np.cos(ChiAngle[0]*np.pi/180)
        y4 = y0 + (radius+width)*np.sin(ChiAngle[0]*np.pi/180)
        indices = np.array([[0,0]])
        cit = 0
        if ChiAngle[0] <= 90. and ChiAngle[0+1] > 90.:
            y5 = y0 + radius + width
        else:
            y5 = 0
        for i in range(int(np.amin([y1,y2,y3,y4])),int(np.amax([y1,y2,y3,y4,y5]))+1):
            for j in range(int(np.amin([x1,x2,x3,x4])),int(np.amax([x1,x2,x3,x4]))+1):
                if (j-x0)**2+(i-y0)**2 > (radius-width)**2 and\
                   (j-x0)**2+(i-y0)**2 < (radius+width)**2 and\
                   (j-x0)/np.sqrt((i-y0)**2+(j-x0)**2) < np.cos(ChiAngle[0]*np.pi/180) and\
                   (j-x0)/np.sqrt((i-y0)**2+(j-x0)**2) > np.cos(ChiAngle[1]*np.pi/180):
                       indices = np.append(indices,[[i,j]],axis=0)
                       cit+=1
        RotationTensor = np.array([[[-np.sin((theta-ChiAngle[0])*np.pi/180),np.cos((theta-ChiAngle[0])*np.pi/180)],\
                                    [np.cos((theta-ChiAngle[0])*np.pi/180), np.sin((theta-ChiAngle[0])*np.pi/180)]] for theta in ChiAngle])
        ImageIndices =np.tensordot(RotationTensor,(indices[1:-1]-[y0,x0]).T,axes=1).astype(int)
        try:
            ChiProfile = np.sum([img[ImageIndices[i,1,:]+int(y0),ImageIndices[i,0,:]+int(x0)] for i in range(ChiTotalSteps+1)], axis=1)/cit
        except IndexError:
            ChiProfile = []
        normalization_factor = np.amax(np.amax(img)) if normalize_to_img_max else 1
        return np.flip(ChiAngle2,axis=0),ChiProfile/normalization_factor

class Diffraction(object):

    def __init__(self):
        super(Diffraction,self).__init__()

    def G_matrix(self,a,b,c,alpha,beta,gamma):
        return np.array([[a**2, a*b*np.cos(gamma/180*np.pi), a*c*np.cos(beta/180*np.pi)],
                        [a*b*np.cos(gamma/180*np.pi), b**2, b*c*np.cos(alpha/180*np.pi)],
                        [a*c*np.cos(beta/180*np.pi), b*c*np.cos(alpha/180*np.pi), c**2]])

    def G_star(self,a,b,c,alpha,beta,gamma):
        return 2*np.pi*np.linalg.inv(self.G_matrix(a,b,c,alpha,beta,gamma))

    def conversion_matrix(self,a,b,c,alpha,beta,gamma):
        c1 = c*np.cos(beta/180*np.pi)
        c2 = c*(np.cos(alpha/180*np.pi)-np.cos(gamma/180*np.pi)*np.cos(beta/180*np.pi))/np.sin(gamma/180*np.pi)
        c3 = np.sqrt(c**2-c1**2-c2**2)
        return np.array([[a, b*np.cos(gamma/180*np.pi), c1],
                         [0, b*np.sin(gamma/180*np.pi), c2],
                         [0, 0,                         c3]])

    def is_permitted(self,h,k,l,space_group_number):
        if space_group_number == 167:
            return ((-h+k+l)%3 == 0 and h!=-k) or ((h+l)%3==0 and l%2==0 and h==-k)
        elif space_group_number == 216:
            return (h+k)%2==0 and (k+l)%2==0 and (h+l)%2==0

class CurveletStructure(QtCore.QObject):

    def __init__(self,structure):
        super(CurveletStructure,self).__init__()
        self.original_structure = structure
        self.structure = structure
        self.control_panel = CurveletControl()

    def size(self):
        nor,noc = len(self.structure),max(len(self.structure[i]) for i in range(len(self.structure)))
        return nor, noc

    def apply_hard_threshold(self,energy,threshold,wedges=None):
        nor = len(self.structure)
        new_structure = copy.deepcopy(self.original_structure)
        if not wedges:
            for i in range(nor):
                for j in range(len(self.structure[i])):
                    if i == 0:
                        mask = 1
                    else:
                        mask = (abs(self.original_structure[i][j])>threshold*energy[i][j])*1
                    new_structure[i][j] = self.original_structure[i][j]*mask
        else:
            for i,j in wedges:
                if i == 0:
                    mask = 1
                else:
                    mask = (abs(self.original_structure[i][j])>threshold*energy[i][j])*1
                new_structure[i][j] = self.original_structure[i][j]*mask
        self.structure = new_structure

    def show_wedge(self,i,j,interactive):
        if not interactive:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.imshow(pilImage.fromarray(self.structure[i][j]).convert('L'),cmap='hot')
            ax.set_title('({},{})'.format(i,j))
            plt.show()
        else:
            if not hasattr(self,'control_panel'):
                self.control_panel = CurveletControl()
            self.control_panel.add_wedge(self.structure,i,j)
    
    def close_all(self):
        plt.close('all')
        self.control_panel.close()
        self.control_panel.deleteLater()
        del self.control_panel