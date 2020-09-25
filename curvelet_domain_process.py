import process
import browser
import digital_tile
import canvas
import pyct
import configparser
import PIL.Image as pilImage
import PIL.ImageChops as pilChops
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os
from PyQt5 import QtWidgets, QtCore, QtGui
import sys

class CDP(QtCore.QObject):
	def __init__(self):
		super().__init__()
		self.image_worker = process.Image()

	def load_image(self,path,crop=[800, 1800, 1650, 2650]):
		if os.path.splitext(path)[1] == '.nef':
			img_array = self.image_worker.get_image(16,path,False,20,50,crop)
			self.img = pilImage.fromarray(img_array)
		else:
			self.img = pilImage.open(path).convert('L')

	def set_fdct_parameters(self,nbs,nba,ac):
		if hasattr(self,'img'):
			self.fdct_worker = pyct.fdct2(n=self.img.size,nbs=nbs,nba=nba,ac=ac,norm=False,vec=True)
		else:
			print('Please load an image first!')

	def add_gaussian_noise(self,sigma):
		if hasattr(self,'img'):
			self.noise = pilChops.Image.eval(pilImage.effect_noise(self.img.size,sigma), lambda x: x-128)
			self.img_noisy = pilChops.add(self.img,self.noise)
		else:
			print('Please load an image first!')

	def show_images(self,*args):
		image_dict = {}
		if hasattr(self,'img'):
			image_dict['original'] = self.img
		if hasattr(self,'img_noisy'):
			image_dict['noisy'] = self.img_noisy
		if hasattr(self,'img_restore'):
			image_dict['restore'] = self.img_restore
		if hasattr(self,'img_diff'):
			image_dict['difference'] = self.img_diff
		image_list = []
		for arg in args:
			if arg in image_dict:
				image_list.append(arg)
			else:
				print(arg+" doesn't exist!")
		fig = plt.figure()
		grid = gridspec.GridSpec(1,len(image_list))
		for i in range(len(image_list)):
			ax = fig.add_subplot(grid[i])
			ax.imshow(image_dict[image_list[i]],cmap='gray')
			ax.set_title(image_list[i])
		plt.tight_layout()
		plt.show()

	def threshold_denoise(self, fact, sigma, show_structure = None):
		if hasattr(self,'fdct_worker'):
			Energy = self.fdct_worker.normstruct()
			if hasattr(self,'img_noisy'):
				C = self.fdct_worker.fwd(self.img_noisy)
				Sc = self.fdct_worker.struct(C)
				Sct = Sc
				nor,noc = len(Sc),max(len(Sc[x]) for x in range(len(Sc)))
				if show_structure == 'integrated':
					fig = plt.figure()
					grid = gridspec.GridSpec(nor,noc)
				for i in range(nor):
					thresh = fact*sigma
					for j in range(len(Sc[i])):
						if i == 0:
							mask = 1
						else:
							mask = (abs(Sc[i][j])>thresh*Energy[i][j])*1
						Sct[i][j] = Sc[i][j]*mask
						if show_structure == 'integrated':
							ax = fig.add_subplot(grid[i,j+(noc-len(Sc[i]))//2])
							ax.imshow(pilImage.fromarray(Sct[i][j]).convert('L'),cmap='hot')
							ax.set_title('({},{})'.format(i,j))
						elif show_structure == 'individual':
							fig = plt.figure()
							ax = fig.add_subplot(111)
							ax.imshow(pilImage.fromarray(Sct[i][j]).convert('L'),cmap='hot')
							ax.set_title('({},{})'.format(i,j))
				Ct = self.fdct_worker.vect(Sct)
				self.wedges = Sct
				self.img_restore = pilImage.fromarray(self.fdct_worker.inv(Ct)).convert('L')
				self.img_diff = pilImage.eval(pilChops.difference(self.img_noisy, self.img_restore),lambda x: x*10)
				if show_structure == 'integrated' or show_structure == 'individual':
					plt.tight_layout()
					plt.show()
			else:
				print('Please add noise to image first!')
		else:
			print('Please set up a fdct worker first!')

	def show_wedge(self,i,j):
		if hasattr(self,'wedges'):
			fig = plt.figure()
			ax = fig.add_subplot(111)
			ax.imshow(pilImage.fromarray(self.wedges[i][j]).convert('L'),cmap='hot')
			ax.set_title('({},{})'.format(i,j))
			plt.show()
		else:
			print('Please calculate the curvelet transform first!')

	def close_all(self):
		plt.close('all')

	def load(self,nbs,nba,ac):
		if hasattr(self,'img'):
			self.set_fdct_parameters(nbs,nba,ac)
			self.add_gaussian_noise(sigma=20)
			self.threshold_denoise(fact=1.4,sigma=20)
		else:
			print('Please load an image first!')

class Window(QtWidgets.QMainWindow):
	WEDGE_REQUESTED = QtCore.pyqtSignal(int,int)
	CLOSE_ALL = QtCore.pyqtSignal()
	LOAD_CURVELETS = QtCore.pyqtSignal(int,int, bool)
	IMAGE_CHOSEN = QtCore.pyqtSignal(str)
	
	def __init__(self):
		super(Window,self).__init__()
		self.image_worker = process.Image()
		self.image_crop = [800, 1800, 1650, 2650]
		config = configparser.ConfigParser()
		config.read('./configuration.ini')
		self.mainSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
		self.canvas = canvas.Canvas(self,config)
		self.digital_tile = digital_tile.DigTile(self)
		self.digital_tile.WEDGE_REQUESTED.connect(self.WEDGE_REQUESTED)
		self.controlPanel = QtWidgets.QWidget(self)
		self.controlPanelGrid = QtWidgets.QGridLayout(self.controlPanel)
		self.supportedFormates = {'*.3fr','*.ari','*.arw','*.srf', '*.sr2','*.bay','*.cri','*.crw', '*.cr2',     '*.cr3', '*.cap','*.iiq','*.eip',\
                               '*.dcs','*.dcr','*.drf','*.k25', '*.kdc','*.dng','*.erf','*.fff', '*.mef',     '*.mdc', '*.mos','*.mrw','*.nef',\
                               '*.nrw','*.orf','*.pef','*.ptx', '*.pxn','*.r3d','*.raf','*.raw', '*.rw2',     '*.rwl', '*.rwz','*.srw','*.x3f',\
                               '*.3FR','*.ARI','*.ARW','*.SRF', '*.SR2','*.BAY','*.CRI','*.CRW', '*.CR2',     '*.CR3', '*.CAP','*.IIQ','*.EIP',\
                               '*.DCS','*.DCR','*.DRF','*.K25', '*.KDC','*.DNG','*.ERF','*.FFF', '*.MEF',     '*.MDC', '*.MOS','*.MRW','*.NEF',\
                               '*.NRW','*.ORF','*.PEF','*.PTX', '*.PXN','*.R3D','*.RAF','*.RAW', '*.RW2',     '*.RWL', '*.RWZ','*.SRW','*.X3F',\
                               '*.bmp','*.eps','*.gif','*.icns','*.ico','*.im', '*.jpg','*.jpeg','*.jpeg2000','*.msp', '*.pcx','*.png','*.ppm',\
                               '*.sgi','*.tiff','*.tif','*.xbm','*.BMP','*.EPS','*.GIF','*.ICNS','*.ICO',     '*.IM',  '*.JPG','*.JPEG','*.JPEG2000',\
                               '*.MSP','*.PCX','*.PNG','*.PPM','*.SGI','*.TIFF','*.TIF','*.XBM'}

		self.open_label = QtWidgets.QLabel('Choose image file:\n')
		self.open_label.setMaximumHeight(100)
		self.open_button = QtWidgets.QPushButton('Browse...')
		self.open_button.clicked.connect(self.browse_image)
		self.browser_widget = browser.Browser(self,self.supportedFormates)
		self.IMAGE_CHOSEN.connect(self.browser_widget.tree_update)
		self.browser_widget.FILE_DOUBLE_CLICKED.connect(self.open_image)
		self.browser_widget.setMaximumHeight(400)

		self.nbs_label = QtWidgets.QLabel('Number of scales:')
		self.nba_label = QtWidgets.QLabel('Number of angles:')
		self.ac_label = QtWidgets.QLabel('Use curvet at the coarest scale?')
		self.nbs = QtWidgets.QComboBox()
		for s in range(3,20):
			self.nbs.addItem(str(s))
		self.nbs.setCurrentText('5')
		self.nba = QtWidgets.QComboBox()
		for a in [8,16,32,64]:
			self.nba.addItem(str(a))
		self.ac = QtWidgets.QCheckBox()
		self.ac.setChecked(True)

		self.cursor_selections_label = QtWidgets.QLabel('Cursor selection rule:')
		self.cursor_selections = QtWidgets.QComboBox()
		self.cursor_selections.addItem('cell')
		self.cursor_selections.addItem('level')
		self.cursor_selections.currentTextChanged.connect(self.digital_tile.set_cursor_selection_rule)
		self.click_functions_label = QtWidgets.QLabel('Click function:')
		self.click_functions = QtWidgets.QComboBox()
		self.click_functions.addItem('show')
		self.click_functions.addItem('select')
		self.click_functions.currentTextChanged.connect(self.digital_tile.set_click_function_rule)
		self.show_button = QtWidgets.QPushButton("Show Selected Cells")
		self.show_button.clicked.connect(self.digital_tile.show_selected_cells)
		self.close_button = QtWidgets.QPushButton("Close All")
		self.close_button.clicked.connect(self.CLOSE_ALL)
		self.load_button = QtWidgets.QPushButton("Load Curvelet Transform")
		self.load_button.clicked.connect(self.load_curvelet_transform)
		self.controlPanelGrid.setAlignment(QtCore.Qt.AlignTop)
		self.controlPanelGrid.addWidget(self.open_label,0,0,1,2)
		self.controlPanelGrid.addWidget(self.open_button,1,0,1,2)
		self.controlPanelGrid.addWidget(self.browser_widget,2,0,1,2)
		self.controlPanelGrid.addWidget(self.nbs_label,10,0,1,1)
		self.controlPanelGrid.addWidget(self.nbs,10,1,1,1)
		self.controlPanelGrid.addWidget(self.nba_label,11,0,1,1)
		self.controlPanelGrid.addWidget(self.nba,11,1,1,1)
		self.controlPanelGrid.addWidget(self.ac_label,12,0,1,1)
		self.controlPanelGrid.addWidget(self.ac,12,1,1,1)
		self.controlPanelGrid.addWidget(self.cursor_selections_label,20,0,1,1)
		self.controlPanelGrid.addWidget(self.cursor_selections,20,1,1,1)
		self.controlPanelGrid.addWidget(self.click_functions_label,21,0,1,1)
		self.controlPanelGrid.addWidget(self.click_functions,21,1,1,1)
		self.controlPanelGrid.addWidget(self.show_button,22,0,1,1)
		self.controlPanelGrid.addWidget(self.close_button,22,1,1,1)
		self.controlPanelGrid.addWidget(self.load_button,23,0,1,2)
		self.controlPanelGrid.addWidget(self.digital_tile,100,0,1,2)

		self.mainSplitter.addWidget(self.canvas)
		self.mainSplitter.addWidget(self.controlPanel)
		self.mainSplitter.setSizes([800,400])
		self.mainSplitter.setStretchFactor(0,1)
		self.mainSplitter.setStretchFactor(1,1)
		self.mainSplitter.setCollapsible(0,False)
		self.mainSplitter.setCollapsible(1,False)
		self.setCentralWidget(self.mainSplitter)

	def get_img_path(self):
	    supportedRawFormats = {'.3fr','.ari','.arw','.srf','.sr2','.bay','.cri','.crw','.cr2','.cr3','.cap','.iiq','.eip',\
	                        '.dcs','.dcr','.drf','.k25','.kdc','.dng','.erf','.fff','.mef','.mdc','.mos','.mrw','.nef',\
	                        '.nrw','.orf','.pef','.ptx','.pxn','.r3d','.raf','.raw','.rw2','.rwl','.rwz','.srw','.x3f',\
	                        '.3FR','.ARI','.ARW','.SRF','.SR2','.BAY','.CRI','.CRW','.CR2','.CR3','.CAP','.IIQ','.EIP',\
	                        '.DCS','.DCR','.DRF','.K25','.KDC','.DNG','.ERF','.FFF','.MEF','.MDC','.MOS','.MRW','.NEF',\
	                        '.NRW','.ORF','.PEF','.PTX','.PXN','.R3D','.RAF','.RAW','.RW2','.RWL','.RWZ','.SRW','.X3F'}
	    supportedImageFormats = {'.bmp','.eps','.gif','.icns','.ico','.im','.jpg','.jpeg','.jpeg2000','.msp','.pcx', \
	                                  '.png','.ppm','.sgi','.tiff','.tif','.xbm','.BMP','.EPS','.GIF','.ICNS','.ICO','.IM','.JPG','.JPEG','.JPEG2000','.MSP','.PCX', \
	                                  '.PNG','.PPM','.SGI','.TIFF','.TIF','.XBM'}
	    fileDlg = QtWidgets.QFileDialog(self)
	    fileDlg.setDirectory('./')
	    path = fileDlg.getOpenFileName(filter="All Files (*.*);;Nikon (*.nef;*.nrw);;Sony (*.arw;*.srf;*.sr2);;Canon (*.crw;*.cr2;*.cr3);;JPEG (*.jpg;*.jpeg;*.jpeg2000);;GIF (*.gif);;PNG (*.png);;TIF (*.tif;*.tiff);;BMP (*.bmp)")[0]
	    if not path == '':
	        if not (os.path.splitext(path)[1] in supportedRawFormats or os.path.splitext(path)[1] in supportedImageFormats):
	            self.raise_error("Not supported image type!")
	            return ''
	        else:
	            return path
	    else:
	        return ''

	def browse_image(self):
		path = self.get_img_path()
		if path:
			self.open_image(path)

	def open_image(self,path):
		self.open_label.setText('The image file path is:\n'+path)
		img_array = self.image_worker.get_image(16,path,False,20,50,self.image_crop)
		qImg = QtGui.QImage(np.uint8(img_array),img_array.shape[1],img_array.shape[0],img_array.shape[1], QtGui.QImage.Format_Grayscale8)
		qPixImg = QtGui.QPixmap(qImg.size())
		QtGui.QPixmap.convertFromImage(qPixImg,qImg,QtCore.Qt.MonoOnly)
		self.canvas.set_photo(qPixImg)
		self.IMAGE_CHOSEN.emit(path)

	def load_curvelet_transform(self):
		self.LOAD_CURVELETS.emit(int(self.nbs.currentText()),int(self.nba.currentText()),self.ac.isChecked())
		self.digital_tile.initialize_tiles(int(self.nbs.currentText()),int(self.nba.currentText()),\
			self.ac.isChecked(),self.cursor_selections.currentText(),self.click_functions.currentText())

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	curvelet_domain_processor = CDP()
	window = Window()
	window.WEDGE_REQUESTED.connect(curvelet_domain_processor.show_wedge)
	window.CLOSE_ALL.connect(curvelet_domain_processor.close_all)
	window.IMAGE_CHOSEN.connect(curvelet_domain_processor.load_image)
	window.LOAD_CURVELETS.connect(curvelet_domain_processor.load)
	window.showMaximized()
	sys.exit(app.exec_())