import copy
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

class Window(QtWidgets.QMainWindow):
	IMAGE_CHOSEN = QtCore.pyqtSignal(str)
	def __init__(self):
		super(Window,self).__init__()
		self.image_worker = process.Image()
		self.image_crop = [800, 1800, 1650, 2650]
		self.current_status = {}
		self.canvas_config = configparser.ConfigParser()
		self.canvas_config.read('./configuration.ini')
		self.mainSplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
		self.topSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
		self.canvasFrame = QtWidgets.QWidget()
		self.canvasFrameGrid = QtWidgets.QHBoxLayout(self.canvasFrame)
		self.canvas = canvas.Canvas(self,self.canvas_config)
		self.digital_tile = digital_tile.DigTile(self)
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
		self.nbs.currentTextChanged.connect(self.nbs_changed)
		self.nba = QtWidgets.QComboBox()
		for a in [8,16,32,64]:
			self.nba.addItem(str(a))
		self.nba.currentTextChanged.connect(self.nba_changed)
		self.ac = QtWidgets.QCheckBox()
		self.ac.setChecked(True)
		self.ac.stateChanged.connect(self.ac_changed)
		self.wedge_index_label = QtWidgets.QLabel('Current wedge index:')

		self.threshold_label = QtWidgets.QLabel('Threshold ({})'.format(30))
		self.threshold_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.threshold_slider.setMinimum(0)
		self.threshold_slider.setMaximum(255)
		self.threshold_slider.setValue(30)
		self.threshold_slider.valueChanged.connect(self.threshold_changed)


		self.cursor_selections_label = QtWidgets.QLabel('Cursor selection rule:')
		self.cursor_selections = QtWidgets.QComboBox()
		self.cursor_selections.addItem('cell')
		self.cursor_selections.addItem('level')
		self.cursor_selections.currentTextChanged.connect(self.digital_tile.set_cursor_selection_rule)
		self.click_functions_label = QtWidgets.QLabel('Click function:')
		self.click_functions = QtWidgets.QComboBox()
		self.click_functions.addItem('select')
		self.click_functions.addItem('show')
		self.click_functions.currentTextChanged.connect(self.digital_tile.set_click_function_rule)
		self.previous_difference_scale_factor = 10
		self.difference_scale_factor_label = QtWidgets.QLabel('Difference gain ({})'.format(self.previous_difference_scale_factor))
		self.difference_scale_factor_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.difference_scale_factor_slider.setMinimum(1)
		self.difference_scale_factor_slider.setMaximum(100)
		self.difference_scale_factor_slider.setValue(self.previous_difference_scale_factor)
		self.difference_scale_factor_slider.valueChanged.connect(self.difference_scale_factor_changed)

		self.button_group = QtWidgets.QGroupBox()
		self.button_group_grid = QtWidgets.QVBoxLayout(self.button_group)
		self.show_selected_cells_button = QtWidgets.QPushButton("Show Selected Cells")
		self.show_selected_cells_button.clicked.connect(self.show_selected_cells)
		self.show_selected_cells_button.setEnabled(False)
		self.close_all_button = QtWidgets.QPushButton("Close All")
		self.close_all_button.setEnabled(False)
		self.close_all_button.clicked.connect(self.clear_all)
		self.load_curvelet_button = QtWidgets.QPushButton("Load Curvelet Digital Tile")
		self.load_curvelet_button.clicked.connect(self.load_curvelet_transform)
		self.load_curvelet_button.setEnabled(False)
		self.show_modified_image_button = QtWidgets.QPushButton("Show Results")
		self.show_modified_image_button.clicked.connect(self.show_modified)
		self.show_modified_image_button.setEnabled(False)
		self.apply_threshold_button = QtWidgets.QPushButton('Apply Threshold Denoise')
		self.apply_threshold_button.clicked.connect(self.threshold_denoise)
		self.apply_threshold_button.setEnabled(False)
		self.button_group_grid.addWidget(self.show_selected_cells_button)
		self.button_group_grid.addWidget(self.close_all_button)
		self.button_group_grid.addWidget(self.load_curvelet_button)
		self.button_group_grid.addWidget(self.show_modified_image_button)
		self.button_group_grid.addWidget(self.apply_threshold_button)
		self.button_group_grid.setAlignment(QtCore.Qt.AlignTop)

		self.controlPanelGrid.setAlignment(QtCore.Qt.AlignTop)
		self.controlPanelGrid.addWidget(self.open_label,0,0,1,6)
		self.controlPanelGrid.addWidget(self.open_button,1,0,1,6)
		self.controlPanelGrid.addWidget(self.browser_widget,2,0,1,6)
		self.controlPanelGrid.addWidget(self.nbs_label,10,0,1,2)
		self.controlPanelGrid.addWidget(self.nbs,10,2,1,4)
		self.controlPanelGrid.addWidget(self.nba_label,11,0,1,2)
		self.controlPanelGrid.addWidget(self.nba,11,2,1,4)
		self.controlPanelGrid.addWidget(self.ac_label,12,0,1,2)
		self.controlPanelGrid.addWidget(self.ac,12,2,1,4)
		self.controlPanelGrid.addWidget(self.threshold_label,13,0,1,2)
		self.controlPanelGrid.addWidget(self.threshold_slider,13,2,1,4)
		self.controlPanelGrid.addWidget(self.difference_scale_factor_label,14,0,1,2)
		self.controlPanelGrid.addWidget(self.difference_scale_factor_slider,14,2,1,4)
		self.controlPanelGrid.addWidget(self.cursor_selections_label,20,0,1,2)
		self.controlPanelGrid.addWidget(self.cursor_selections,20,2,1,4)
		self.controlPanelGrid.addWidget(self.click_functions_label,21,0,1,2)
		self.controlPanelGrid.addWidget(self.click_functions,21,2,1,4)
		self.controlPanelGrid.addWidget(self.wedge_index_label,22,0,1,6)
		self.controlPanelGrid.addWidget(self.digital_tile,30,0,1,5)
		self.controlPanelGrid.addWidget(self.button_group,30,5,1,1)

		self.statusBar = QtWidgets.QGroupBox("Log")
		self.statusBar.setStyleSheet('QGroupBox::title {color:blue;}')
		self.statusGrid = QtWidgets.QGridLayout(self.statusBar)
		self.progressBar = QtWidgets.QProgressBar()
		self.progressBar.setVisible(False)
		self.progressBar.setOrientation(QtCore.Qt.Horizontal)
		self.progressBarSizePolicy = self.progressBar.sizePolicy()
		self.progressBarSizePolicy.setRetainSizeWhenHidden(True)
		self.progressBarSizePolicy.setHorizontalPolicy(QtWidgets.QSizePolicy.Expanding)
		self.progressBar.setSizePolicy(self.progressBarSizePolicy)
		self.logBox = QtWidgets.QTextEdit(QtCore.QTime.currentTime().toString("hh:mm:ss")+\
		                            "\u00A0\u00A0\u00A0\u00A0Initialized!")
		self.logCursor = QtGui.QTextCursor(self.logBox.document())
		self.logCursor.movePosition(QtGui.QTextCursor.End)
		self.logBox.setTextCursor(self.logCursor)
		self.logBox.ensureCursorVisible()
		self.logBox.setAlignment(QtCore.Qt.AlignTop)
		self.logBox.setFrameShape(QtWidgets.QFrame.NoFrame)
		self.logBoxScroll = QtWidgets.QScrollArea()
		self.logBoxScroll.setWidget(self.logBox)
		self.logBoxScroll.setWidgetResizable(True)
		self.logBoxScroll.setFrameShape(QtWidgets.QFrame.NoFrame)
		self.statusGrid.addWidget(self.logBoxScroll,0,0)
		self.statusGrid.setAlignment(self.progressBar,QtCore.Qt.AlignRight)

		self.canvasFrameGrid.addWidget(self.canvas,1)
		self.topSplitter.addWidget(self.canvasFrame)
		self.topSplitter.addWidget(self.controlPanel)
		self.topSplitter.setSizes([800,400])
		self.topSplitter.setStretchFactor(0,1)
		self.topSplitter.setStretchFactor(1,1)
		self.topSplitter.setCollapsible(0,False)
		self.topSplitter.setCollapsible(1,False)
		self.mainSplitter.addWidget(self.topSplitter)
		self.mainSplitter.addWidget(self.statusBar)
		self.mainSplitter.setSizes([800,100])
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

	def update_wedge_index(self,i,j):
		self.wedge_index_label.setText('Current wedge index: ({},{})'.format(i,j))

	def update_chosen_wedges(self,state):
		self.show_selected_cells_button.setEnabled(state)
		if 'threshold_denoise' in self.current_status and self.digital_tile.chosen_wedge_indices != self.current_status['threshold_denoise'][1]:
			self.apply_threshold_button.setEnabled(True)
		elif not 'threshold_denoise' in self.current_status:
			self.apply_threshold_button.setEnabled(True)
		else:
			self.apply_threshold_button.setEnabled(False)

	def browse_image(self):
		path = self.get_img_path()
		if path:
			self.open_image(path)

	def open_image(self,path):
		self.open_label.setText('The image file path is:\n'+path)
		self.img_array = self.image_worker.get_image(16,path,False,20,50,self.image_crop)
		self.image = self.image_worker.nparray2pilImg(self.img_array)
		self.canvas.set_photo(self.image_worker.nparray2qPixImg(self.img_array))
		self.canvas.fit_canvas()
		if hasattr(self,'canvas_modified'):
			self.canvasFrameGrid.removeWidget(self.canvas_modified)
			self.canvas_modified.deleteLater()
			del self.canvas_modified
		if hasattr(self,'canvas_diff'):
			self.canvasFrameGrid.removeWidget(self.canvas_diff)
			self.canvas_diff.deleteLater()
			del self.canvas_diff
		self.load_curvelet_button.setEnabled(True)
		self.show_modified_image_button.setEnabled(True)
		self.show_selected_cells_button.setEnabled(False)
		self.close_all_button.setEnabled(False)
		self.show_modified_image_button.setEnabled(False)
		self.apply_threshold_button.setEnabled(False)

	def clear_all(self):
		if hasattr(self,'curvelet_structure'):
			self.curvelet_structure.close_all()
			self.close_all_button.setEnabled(False)

	def show_selected_cells(self):
		if hasattr(self,'digital_tile'):
			self.digital_tile.show_selected_cells()
			self.close_all_button.setEnabled(True)

	def click_show_wedge(self,i,j,interactive):
		self.curvelet_structure.show_wedge(i,j,interactive)
		self.close_all_button.setEnabled(True)

	def nbs_changed(self,text):
		if self.nbs.currentText() != self.current_status['curvelet_transform'][0]:
			self.load_curvelet_button.setEnabled(True)
		else:
			self.load_curvelet_button.setEnabled(False)

	def nba_changed(self,text):
		if self.nba.currentText() != self.current_status['curvelet_transform'][1]:
			self.load_curvelet_button.setEnabled(True)
		else:
			self.load_curvelet_button.setEnabled(False)

	def ac_changed(self,state):
		if self.ac.isChecked() != self.current_status['curvelet_transform'][2]:
			self.load_curvelet_button.setEnabled(True)
		else:
			self.load_curvelet_button.setEnabled(False)

	def load_curvelet_transform(self):
		if hasattr(self,'image'):
			self.fdct_worker = pyct.fdct2(n=self.image.size,nbs=int(self.nbs.currentText()),\
				nba=int(self.nba.currentText()),ac=self.ac.isChecked(),norm=False,vec=True)
			self.digital_tile.initialize_tiles(int(self.nbs.currentText()),int(self.nba.currentText()),\
				self.ac.isChecked(),self.cursor_selections.currentText(),self.click_functions.currentText())
			if not hasattr(self,'curvelet_structure'):
				self.digital_tile.WEDGE_REQUESTED.connect(self.click_show_wedge)
				self.digital_tile.WEDGE_ENTER.connect(self.update_wedge_index)
				self.digital_tile.WEDGE_CHOSEN.connect(self.update_chosen_wedges)
			self.curvelet_structure = process.CurveletStructure(self.fdct_worker.struct(self.fdct_worker.fwd(self.image)))
			self.curvelet_structure.control_panel.UPDATE_LOG.connect(self.update_log)
			self.current_status['curvelet_transform'] = (self.nbs.currentText(),self.nba.currentText(),self.ac.isChecked())
			self.apply_threshold_button.setEnabled(True)
			self.load_curvelet_button.setEnabled(False)
			self.update_log('[SUCCESS] Curvelet structure created!')
		else:
			self.update_log('[ERROR] Please load an image first!')

	def threshold_denoise(self):
		if hasattr(self,'curvelet_structure'):
			Energy = self.fdct_worker.normstruct()
			self.curvelet_structure.apply_hard_threshold(Energy,self.threshold_slider.value(),self.digital_tile.chosen_wedge_indices)
			self.current_status['threshold_denoise'] = (self.threshold_slider.value(),copy.deepcopy(self.digital_tile.chosen_wedge_indices))
			self.show_modified_image_button.setEnabled(True)
			self.apply_threshold_button.setEnabled(False)
			self.update_log('[SUCCESS] Threshold denoise applied!')

	def show_modified(self):
		if hasattr(self,'fdct_worker'):
			Ct = self.fdct_worker.vect(self.curvelet_structure.structure)
			self.image_modified = pilImage.fromarray(self.fdct_worker.inv(Ct)).convert('L')
			self.image_diff = pilImage.eval(pilChops.difference(self.image, self.image_modified),lambda x: x*self.difference_scale_factor_slider.value())
			if not hasattr(self,'canvas_modified'):
				self.canvas_modified = canvas.Canvas(self,self.canvas_config)
				self.canvas_diff = canvas.Canvas(self,self.canvas_config)
				self.canvas_modified.set_photo(self.image_worker.pilImg2qPixImg(self.image_modified)) 
				self.canvas_diff.set_photo(self.image_worker.pilImg2qPixImg(self.image_diff))
				self.canvas.WHEEL_EVENT.connect(self.canvas_modified.wheelEvent)
				self.canvas.WHEEL_EVENT.connect(self.canvas_diff.wheelEvent)
				self.canvas.verticalScrollBar().valueChanged.connect(self.canvas_modified.verticalScrollBar().setValue)
				self.canvas.horizontalScrollBar().valueChanged.connect(self.canvas_modified.horizontalScrollBar().setValue)
				self.canvas.verticalScrollBar().rangeChanged.connect(self.canvas_modified.verticalScrollBar().setRange)
				self.canvas.horizontalScrollBar().rangeChanged.connect(self.canvas_modified.horizontalScrollBar().setRange)
				self.canvas_modified.verticalScrollBar().valueChanged.connect(self.canvas.verticalScrollBar().setValue)
				self.canvas_modified.horizontalScrollBar().valueChanged.connect(self.canvas.horizontalScrollBar().setValue)
				self.canvas_modified.verticalScrollBar().rangeChanged.connect(self.canvas.verticalScrollBar().setRange)
				self.canvas_modified.horizontalScrollBar().rangeChanged.connect(self.canvas.horizontalScrollBar().setRange)
				self.canvas.verticalScrollBar().valueChanged.connect(self.canvas_diff.verticalScrollBar().setValue)
				self.canvas.horizontalScrollBar().valueChanged.connect(self.canvas_diff.horizontalScrollBar().setValue)
				self.canvas.verticalScrollBar().rangeChanged.connect(self.canvas_diff.verticalScrollBar().setRange)
				self.canvas.horizontalScrollBar().rangeChanged.connect(self.canvas_diff.horizontalScrollBar().setRange)
				self.canvas_diff.verticalScrollBar().valueChanged.connect(self.canvas.verticalScrollBar().setValue)
				self.canvas_diff.horizontalScrollBar().valueChanged.connect(self.canvas.horizontalScrollBar().setValue)
				self.canvas_diff.verticalScrollBar().rangeChanged.connect(self.canvas.verticalScrollBar().setRange)
				self.canvas_diff.horizontalScrollBar().rangeChanged.connect(self.canvas.horizontalScrollBar().setRange)
				self.canvas_modified.WHEEL_EVENT.connect(self.canvas.wheelEvent)
				self.canvas_modified.WHEEL_EVENT.connect(self.canvas_diff.wheelEvent)
				self.canvas_diff.WHEEL_EVENT.connect(self.canvas.wheelEvent)
				self.canvas_diff.WHEEL_EVENT.connect(self.canvas_modified.wheelEvent)
				self.canvasFrameGrid.addWidget(self.canvas_modified,1)
				self.canvasFrameGrid.addWidget(self.canvas_diff,1)
				self.canvas.fit_canvas()
				self.canvas_modified.fit_canvas()
				self.canvas_diff.fit_canvas()
				self.update_log('[SUCCESS] Modified image showed!')
			else:
				self.canvas_modified.set_photo(self.image_worker.pilImg2qPixImg(self.image_modified)) 
				self.canvas_diff.set_photo(self.image_worker.pilImg2qPixImg(self.image_diff))
				self.update_log('[SUCCESS] Modified image updated!')
			self.show_modified_image_button.setEnabled(False)
		else:
			self.update_log('[ERROR] Please load the curvelet transform first!')

	def difference_scale_factor_changed(self):
		self.difference_scale_factor_label.setText('Difference gain ({})'.format(self.difference_scale_factor_slider.value()))
		if hasattr(self,'canvas_diff'):
			self.image_diff = pilImage.eval(self.image_diff,lambda x: x*self.difference_scale_factor_slider.value()/self.previous_difference_scale_factor)
			self.canvas_diff.set_photo(self.image_worker.pilImg2qPixImg(self.image_diff))
		self.previous_difference_scale_factor = self.difference_scale_factor_slider.value()


	def threshold_changed(self):
		self.threshold_label.setText('Threshold ({})'.format(self.threshold_slider.value()))
		if self.threshold_slider.value() != self.current_status['threshold_denoise'][0]:
			self.apply_threshold_button.setEnabled(True)
		else:
			self.apply_threshold_button.setEnabled(False)

	def update_log(self,message):
	    self.logBox.append(QtCore.QTime.currentTime().toString("hh:mm:ss")+"\u00A0\u00A0\u00A0\u00A0"+message)

	def raise_error(self,message):
	    msg = QtWidgets.QMessageBox()
	    msg.setIcon(QtWidgets.QMessageBox.Warning)
	    msg.setText(message)
	    msg.setWindowTitle("Error")
	    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
	    msg.setEscapeButton(QtWidgets.QMessageBox.Close)
	    msg.exec()

	def raise_attention(self,information):
	    info = QtWidgets.QMessageBox()
	    info.setIcon(QtWidgets.QMessageBox.Information)
	    info.setText(information)
	    info.setWindowTitle("Information")
	    info.setStandardButtons(QtWidgets.QMessageBox.Ok)
	    info.setEscapeButton(QtWidgets.QMessageBox.Close)
	    info.exec()

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	window = Window()
	window.showMaximized()
	sys.exit(app.exec_())