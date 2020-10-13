import matplotlib.pyplot as plt
import matplotlib as mpl
from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np

class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=15, height=12, dpi=400, pos=111):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.pos = pos
        self.axes = self.fig.add_subplot(self.pos)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        mpl.rcParams['axes.linewidth'] = 0.4

    def clear(self):
        self.fig.clear()
        self.axes = self.fig.add_subplot(self.pos)

    def save_as_file(self,directory, name):
        self.fig.savefig(directory+name)

class DynamicViewer(QtWidgets.QWidget):

    UPDATE_LOG = QtCore.pyqtSignal(str)

    def __init__(self,image,fontname,fontsize,colormap,log_scale=True, pos=111, kwargs={}):
        super(DynamicViewer,self).__init__()
        self.pos = pos
        self.figure = MplCanvas(self,pos=self.pos)
        self.image = image
        self.log_scale = log_scale
        self.fontname = fontname
        self.fontsize = fontsize
        self.colormap = colormap
        self.minimum_log_intensity = -5
        self.previous_gain = 1
        self.kwargs = kwargs
        self.window_layout = QtWidgets.QGridLayout(self)
        self.toolbar = NavigationToolbar(self.figure,self)
        self.window_layout.addWidget(self.figure,0,0)
        self.window_layout.addWidget(self.toolbar,1,0)
        self.setMaximumWidth(1600)
        if self.kwargs.get('save_as_file', False):
            pass
        self.original_min = np.amin(np.amin(image))
        self.original_max = np.amin(np.amax(image))
        self.show_plot()

    def show_plot(self):
        self.replot(self.image,self.colormap)
        if self.kwargs.get('save_as_file', False):
            pass

    def refresh_font_size(self,fontsize):
        self.fontsize = fontsize
        font_dict = {'fontname':self.fontname, 'fontsize':self.fontsize}
        plt.ion()
        self.figure.axes.set_xlabel('x',font_dict)
        self.figure.axes.set_ylabel('y',font_dict)
        self.figure.axes.set_aspect(1)
        self.figure.axes.set_frame_on(False)
        self.figure.axes.tick_params(width = 0.1, length = 1, which='both', labelsize=self.fontsize)
        if self.log_scale:
            self.cbar.ax.set_ylabel("Intensity",font_dict)
            self.cbar.set_ticks(np.linspace(self.log_min,self.log_max,self.log_max-self.log_min+1))
            self.cbar.set_ticklabels(list('$10^{{{}}}$'.format(i) for i in range(self.log_min,self.log_max+1,1)))
        else:
            self.cbar.ax.set_ylabel("Intensity",font_dict)
        self.cbar.ax.tick_params(width = 0.1, length = 1, labelsize=self.fontsize)
        self.cbar.outline.set_linewidth(0.1)
        self.figure.draw()

    def refresh_font_name(self,fontname):
        self.fontname = fontname
        font_dict = {'fontname':self.fontname, 'fontsize':self.fontsize}
        plt.ion()
        self.figure.axes.set_xlabel('x',font_dict)
        self.figure.axes.set_ylabel('y',font_dict)
        self.figure.axes.set_aspect(1)
        self.figure.axes.set_frame_on(False)
        self.figure.axes.tick_params(width = 0.1, length = 1, which='both', labelsize=self.fontsize)
        if self.log_scale:
            self.cbar.ax.set_ylabel("Intensity",font_dict)
            self.cbar.set_ticks(np.linspace(self.log_min,self.log_max,self.log_max-self.log_min+1))
            self.cbar.set_ticklabels(list('$10^{{{}}}$'.format(i) for i in range(self.log_min,self.log_max+1,1)))
        else:
            self.cbar.ax.set_ylabel("Intensity",font_dict)
        self.cbar.ax.tick_params(width = 0.1, length = 1, labelsize=self.fontsize)
        self.cbar.outline.set_linewidth(0.1)
        self.figure.draw()

    def replot(self,image,colormap):
        self.colormap = colormap
        self.figure.clear()
        self.figure.axes.invert_yaxis()
        self.x_linear,self.y_linear = np.meshgrid(np.linspace(0,len(image)-1,len(image)), np.linspace(0,len(image[0])-1,len(image[0])))
        if self.log_scale:
            self.log_max = int(np.log10(np.amax(np.amax(image))))
            int_min = np.amin(np.amin(image))
            if int_min <= 0:
                self.log_min = self.minimum_log_intensity
            else:
                self.log_min = max(int(np.log10(int_min)),self.minimum_log_intensity)
            self.cs = self.figure.axes.contourf(self.x_linear,self.y_linear,np.clip(np.log10(image.T),self.log_min,self.log_max),1000,cmap=self.colormap,origin='upper')
        else:
            self.cs = self.figure.axes.contourf(self.x_linear,self.y_linear,image.T,1000, vmin=self.original_min, vmax=self.original_max, cmap=self.colormap,origin='upper')
        self.cbar = self.figure.fig.colorbar(self.cs,format='%3.1f')
        self.refresh_font_name(self.fontname)
        self.refresh_font_size(self.fontsize)

    def save_FFT(self,path):
        try:
            output = open(path,mode='w')
            output.write('Time: \n')
            output.write(QtCore.QDateTime.currentDateTime().toString("MMMM d, yyyy  hh:mm:ss ap")+"\n\n")
            results = "\n".join(str(self.FFT[0][i])+'\t'+str(self.FFT[1][i]) for i in range(1000))
            output.write(results)
            output.close()
        except:
            pass

    def refresh_gain(self,gain,unit):
        if unit == 'scalar':
            factor = float(gain)
        elif unit == 'dB':
            factor = 10**(float(gain)/20)
        if factor > 0:
            self.image *= factor/self.previous_gain
            self.replot(self.image,self.colormap)
            self.previous_gain = factor
        else:
            self.UPDATE_LOG.emit('[ERROR] Invalid gain value!')

    def refresh_colormap(self,colormap):
        self.colormap = colormap
        self.replot(self.image,self.colormap)

    def refresh_scale(self,state):
        if not self.log_scale and state == 2:
            self.log_scale = True
            self.replot(self.image,self.colormap)
        elif self.log_scale and state == 0:
            self.log_scale = False
            self.replot(self.image,self.colormap)

class CurveletControl(QtWidgets.QWidget):
    UPDATE_LOG = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.wedge_count = 0
        self.grid = QtWidgets.QGridLayout(self)
        self.appearance = QtWidgets.QGroupBox("Appearance")
        self.appearance.setMaximumHeight(200)
        self.appearance.setStyleSheet('QGroupBox::title {color:blue;}')
        self.appearanceGrid = QtWidgets.QGridLayout(self.appearance)
        self.fontListLabel = QtWidgets.QLabel("Change Font")
        self.fontList = QtWidgets.QFontComboBox()
        self.fontList.setCurrentFont(QtGui.QFont("Monospace"))
        self.fontSizeLabel = QtWidgets.QLabel("Adjust Font Size ({})".format(5))
        self.fontSizeLabel.setFixedWidth(250)
        self.fontSizeSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.fontSizeSlider.setMinimum(1)
        self.fontSizeSlider.setMaximum(10)
        self.fontSizeSlider.setValue(5)
        self.gainLabel = QtWidgets.QLabel("Gain")
        self.gainLabel.setFixedWidth(250)
        self.gainEdit = QtWidgets.QLineEdit('1')
        self.gainUnit = QtWidgets.QComboBox()
        self.gainUnit.addItem('scalar')
        self.gainUnit.addItem('dB')
        self.previous_gain_unit = 'scalar'
        self.gainUnit.currentTextChanged.connect(self.gain_unit_changed)
        self.gainApply = QtWidgets.QPushButton("Apply")
        self.appearanceGrid.addWidget(self.fontListLabel,0,0,1,4)
        self.appearanceGrid.addWidget(self.fontList,0,4,1,4)
        self.appearanceGrid.addWidget(self.fontSizeLabel,1,0,1,4)
        self.appearanceGrid.addWidget(self.fontSizeSlider,1,4,1,4)
        self.appearanceGrid.addWidget(self.gainLabel,2,0,1,4)
        self.appearanceGrid.addWidget(self.gainEdit,2,4,1,1)
        self.appearanceGrid.addWidget(self.gainUnit,2,5,1,1)
        self.appearanceGrid.addWidget(self.gainApply,2,6,1,2)
            
        self.plotOptions = QtWidgets.QGroupBox("Contour Plot Options")
        self.plotOptions.setStyleSheet('QGroupBox::title {color:blue;}')
        self.plotOptionsGrid = QtWidgets.QGridLayout(self.plotOptions)
        self.colormapLabel = QtWidgets.QLabel("Colormap")
        self.colormap = QtWidgets.QComboBox()
        for cm in plt.colormaps():
            self.colormap.addItem(cm,cm)
        self.colormap.setCurrentText('bwr')
        self.logScaleLabel = QtWidgets.QLabel("Log scale")
        self.logScale = QtWidgets.QCheckBox()
        self.plotOptionsGrid.addWidget(self.colormapLabel,0,0)
        self.plotOptionsGrid.addWidget(self.colormap,0,1)
        self.plotOptionsGrid.addWidget(self.logScaleLabel,1,0)
        self.plotOptionsGrid.addWidget(self.logScale,1,1)
        self.plotOptionsGrid.setAlignment(QtCore.Qt.AlignTop)

        self.mainTab = QtWidgets.QTabWidget()
        self.mainTab.setContentsMargins(0,0,0,0)
        self.mainTab.setTabsClosable(True)
        self.mainTab.currentChanged.connect(self.switch_tab)
        self.mainTab.tabCloseRequested.connect(self.close_tab)
        self.mainTab.setFixedWidth(1600)
        self.tabClosed = False
        self.tab_index_dict = {}
        self.tab_info_dict = {}

        self.grid.addWidget(self.appearance,0,1,1,1)
        self.grid.addWidget(self.plotOptions,1,1,1,1)
        self.grid.addWidget(self.mainTab,0,0,2,1)

    def add_wedge(self,structure,i,j):
        self.mainTab.disconnect()
        viewer = DynamicViewer(structure[i][j],self.fontList.currentFont().family(),\
            self.fontSizeSlider.value(),self.colormap.currentText(),self.logScale.isChecked())
        viewer.UPDATE_LOG.connect(self.UPDATE_LOG)
        index = self.mainTab.addTab(viewer,'({},{})'.format(i,j))
        self.current_wedge_index = (i,j)
        self.tab_index_dict[index] = (i,j)
        self.tab_info_dict[(i,j)] = [self.fontList.currentText(),\
            self.fontSizeSlider.value(),self.colormap.currentText(),self.logScale.isChecked(),\
            self.gainEdit.text(), self.gainUnit.currentText()]
        self.mainTab.currentChanged.connect(self.switch_tab)
        self.mainTab.tabCloseRequested.connect(self.close_tab)
        if self.wedge_count == 0:
            self.reconnect_viewer(viewer)
            self.show_window()
        self.wedge_count += 1

    def disconnect_viewer(self):
        self.gainApply.disconnect()
        self.fontList.disconnect()
        self.fontSizeSlider.disconnect()
        self.colormap.disconnect()
        self.logScale.disconnect()

    def reconnect_viewer(self,viewer):
        self.fontList.currentTextChanged.connect(viewer.refresh_font_name)
        self.fontSizeSlider.valueChanged.connect(viewer.refresh_font_size)
        self.gainApply.clicked.connect(self.apply_gain)
        self.colormap.currentTextChanged.connect(viewer.refresh_colormap)
        self.logScale.stateChanged.connect(viewer.refresh_scale)

    def show_window(self):
        self.setWindowTitle('Curvelet Domain Wedges')
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.showNormal()

    def apply_gain(self):
        self.mainTab.currentWidget().refresh_gain(self.gainEdit.text(),self.gainUnit.currentText())

    def gain_unit_changed(self,unit):
        if self.previous_gain_unit == 'scalar' and unit == 'dB':
            value = 20*np.log10(float(self.gainEdit.text()))
            self.gainEdit.setText('{:.8f}'.format(value).rstrip('0').rstrip('.'))
        elif self.previous_gain_unit == 'dB' and unit == 'scalar':
            value = 10**(float(self.gainEdit.text())/20)
            self.gainEdit.setText('{:.8f}'.format(value).rstrip('0').rstrip('.'))
        self.previous_gain_unit = unit

    def reset(self):
        self.fontList.setCurrentText(QtGui.QFont("Monospace").family())
        self.fontSizeSlider.setValue(5)
        self.colormap.setCurrentText('bwr')
        self.logScale.setChecked(False)
        self.gainEdit.setText('1')
        self.gainUnit.setCurrentText('scalar')

    def switch_tab(self,index):
        if index >= 0:
            self.disconnect_viewer()
            #self.UPDATE_LOG.emit('[ACTION] switching from tab{} to tab {}'.format(self.current_wedge_index, index))
            self.tab_info_dict[self.current_wedge_index] = [self.fontList.currentText(),\
                self.fontSizeSlider.value(),self.colormap.currentText(),self.logScale.isChecked(),\
                self.gainEdit.text(), self.gainUnit.currentText()]
            self.current_wedge_index = self.tab_index_dict[index]
            self.fontSizeSlider.valueChanged.connect(lambda x: self.fontSizeLabel.setText("Adjust Font Size ({})".format(x)))
            self.fontList.setCurrentText(QtGui.QFont(self.tab_info_dict[self.current_wedge_index][0]).family())
            self.fontSizeSlider.setValue(self.tab_info_dict[self.current_wedge_index][1])
            self.colormap.setCurrentText(self.tab_info_dict[self.current_wedge_index][2])
            self.logScale.setChecked(self.tab_info_dict[self.current_wedge_index][3])
            self.previous_gain_unit = self.tab_info_dict[self.current_wedge_index][5]
            self.gainEdit.setText(self.tab_info_dict[self.current_wedge_index][4])
            self.gainUnit.setCurrentText(self.tab_info_dict[self.current_wedge_index][5])
            if self.mainTab.count() > 0:
                self.reconnect_viewer(self.mainTab.currentWidget())
            if self.tabClosed:
                self.tabClosed = False

    def close_tab(self,index):
        wedge_index = self.tab_index_dict[index]
        if index == self.mainTab.currentIndex() and not self.mainTab.count()== 1:
            self.mainTab.setCurrentIndex(index+1)
            if index != self.mainTab.count()-1:
                for i in range(index,self.mainTab.count()-1):
                    self.tab_index_dict[i] = self.tab_index_dict[i+1]
            del self.tab_index_dict[self.mainTab.count()-1]
            self.mainTab.widget(index).deleteLater()
            self.mainTab.removeTab(index)
        elif self.mainTab.count()==1:
            self.mainTab.widget(index).deleteLater()
            self.mainTab.clear()
            del self.tab_index_dict[0]
            self.reset()
            self.wedge_count = 0
        else:
            for i in range(index,self.mainTab.count()-1):
                self.tab_index_dict[i] = self.tab_index_dict[i+1]
            del self.tab_index_dict[self.mainTab.count()-1]
            self.mainTab.widget(index).deleteLater()
            self.mainTab.removeTab(index)
        del self.tab_info_dict[wedge_index]
        self.tabClosed = True