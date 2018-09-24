# @package SoundEffectorView.py
# @brief SoundEffectorのView
# @author Nakashima
# @date 2018/9/22
# @version 0.0.1
# @

import sys
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui

## View
# @brief 画面表示用クラス
class SoundEffectorView(QtGui.QWidget):
    def __init__(self, model, parent = None):
        super(SoundEffectorView, self).__init__(parent)
        """ Model """
        self.model = model
        """ Data """
        self.freq = np.linspace(0,44100,self.model.BUFFERSIZE)
        self.plotdata = np.zeros(self.model.CHUNK)
        self.update_msec = 10
        """ Window """
        self.setWindowTitle("test")
        """ Label Widget """
        self.label = QtGui.QLabel("SoundEffector")
        """ Graph Widget """
        self.graph = pg.PlotWidget(title="WaveForm")
        self.graphplt = self.graph.plotItem
        self.graphplt.setXRange(0,self.model.BUFFERSIZE)
        self.graphplt.setYRange(-1,1)
        self.graphcurve = self.graphplt.plot()
        """ Spectrum Widget """
        self.spectrum = pg.PlotWidget(title="Spectrum")
        self.specplt = self.spectrum.plotItem
        self.specplt.setXRange(0,5000)
        self.specplt.setYRange(0,10**12)
#        self.specplt.setYRange(0,20)
        self.speccurve = self.specplt.plot()
        """ Cepstrum Widget """
        self.cepstrum = pg.PlotWidget(title="Cepstrum")
        self.cepsplt = self.cepstrum.plotItem
        self.cepsplt.setXRange(0,5000)
        self.cepsplt.setYRange(-1,1)
        self.cepscurve = self.cepsplt.plot()
        """ Layout Box """
        self.graphBox = QtGui.QGridLayout()
        self.graphBox.addWidget(self.graph,0,0)
        self.graphBox.addWidget(self.spectrum,1,0)
        self.graphBox.addWidget(self.cepstrum,2,0)
        self.setLayout(self.graphBox)
        """ timer """
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.update_msec)

    def update(self):
        """ Processing """
        self.model.main(self.model.stream)
        """ Rewriting GraphPlot"""
        self.plotdata = np.append(self.plotdata, self.model.plotdata)
        if len(self.plotdata) > self.model.BUFFERSIZE:
            self.plotdata = self.plotdata[self.model.CHUNK:]
        self.graphcurve.setData(self.plotdata)
        """ Rewriting Spectrum """
        self.specdata = abs(self.model.power)
        self.speccurve.setData(self.freq, self.specdata)
        """ Rewriting Cepstrum """
        self.cepsdata = self.model.cepstrum
        self.cepscurve.setData(self.cepsdata)
