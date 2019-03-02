# @package SoundEffectorView.py
# @brief SoundEffectorのView
# @author Nakashima
# @date 2018/9/22
# @version 0.0.1
# @

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtWidgets

dir(QtWidgets.QSlider.minimum)


## View
# @brief 画面表示用クラス
class SoundEffectorView(QtGui.QWidget):
    def __init__(self, model, parent=None):
        super(SoundEffectorView, self).__init__(parent)
        """ Model """
        self.model = model
        """ Data """
        self.freq = np.linspace(0, 44100, self.model.ANALYZEDSIZE)
        self.plotdata = np.zeros(self.model.CHUNK)
        self.update_msec = 10
        """ Window """
        self.setWindowTitle("SoundEffector")
        """ Create Box """
        self.effectBox = self.create_effect_box()
        self.graphBox = self.create_graph_box()
        """ Set Layout Box """
        self.layoutBox = QtGui.QGridLayout()
        self.layoutBox.addLayout(self.effectBox, 0, 0)
        self.layoutBox.addLayout(self.graphBox, 0, 1)
        self.setLayout(self.layoutBox)
        """ Update """
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.update_msec)

    """ -----------------------------------------------------------------------
    Create Effect Control Widgets
    ----------------------------------------------------------------------- """
    def create_effect_box(self):
        effectBox = QtGui.QGridLayout()
        """ pre_booster """
        pre_booster_switch, pre_booster_bar = self.create_pre_booster_widget()
        effectBox.addWidget(pre_booster_switch, 0, 0)
        effectBox.addWidget(pre_booster_bar, 1, 0)
        """ distortion """
        distortion_switch, distortion_bar = self.create_distortion_widget()
        effectBox.addWidget(distortion_switch, 2, 0)
        effectBox.addWidget(distortion_bar, 3, 0)
        """ phaser """
        phaser_switch = self.create_phaser_widget()
        effectBox.addWidget(phaser_switch, 4, 0)
        """ post_booster """
        post_booster_switch, post_booster_bar = self.create_post_booster_widget()
        effectBox.addWidget(post_booster_switch, 5, 0)
        effectBox.addWidget(post_booster_bar, 6, 0)
        return effectBox

    def create_pre_booster_widget(self):
        pre_booster_switch = QtWidgets.QCheckBox("PER-BOOSTER", self)
        pre_booster_switch.stateChanged.connect(self.toggle_pre_booster)
        pre_booster_bar = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        pre_booster_bar.setMinimum(1)
        pre_booster_bar.setMaximum(10)
        pre_booster_bar.valueChanged.connect(self.control_pre_booster)
        return pre_booster_switch, pre_booster_bar

    def create_distortion_widget(self):
        distortion_switch = QtWidgets.QCheckBox("DISTORTION", self)
        distortion_switch.stateChanged.connect(self.toggle_distortion)
        distortion_bar = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        distortion_bar.setMinimum(10)
        distortion_bar.setMaximum(50)
        distortion_bar.valueChanged.connect(self.control_distortion)
        return distortion_switch, distortion_bar

    def create_phaser_widget(self):
        phaser_switch = QtWidgets.QCheckBox("PHASER", self)
        phaser_switch.stateChanged.connect(self.toggle_phaser)
        return phaser_switch

    def create_post_booster_widget(self):
        post_booster_switch = QtWidgets.QCheckBox("POST-BOOSTER", self)
        post_booster_bar = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        post_booster_bar.setMinimum(1)
        post_booster_bar.setMaximum(10)
        post_booster_switch.stateChanged.connect(self.toggle_post_booster)
        post_booster_bar.valueChanged.connect(self.control_post_booster)
        return post_booster_switch, post_booster_bar

    """ -----------------------------------------------------------------------
    Create Graph View Widgets
    ----------------------------------------------------------------------- """
    def create_graph_box(self):
        self.create_graph_widgets()
        graphBox = QtGui.QGridLayout()
        graphBox.addWidget(self.graph, 0, 0)
        graphBox.addWidget(self.spectrum, 1, 0)
        graphBox.addWidget(self.cepstrum, 2, 0)
        return graphBox

    def create_graph_widgets(self):
        """ Graph Widget """
        self.graph = pg.PlotWidget(title="WaveForm")
        self.graphplt = self.graph.plotItem
        self.graphplt.setXRange(0, self.model.ANALYZEDSIZE)
        self.graphplt.setYRange(-1, 1)
        self.graphcurve = self.graphplt.plot()
        """ Spectrum Widget """
        self.spectrum = pg.PlotWidget(title="Spectrum")
        self.specplt = self.spectrum.plotItem
        self.specplt.setXRange(0, 5000)
        self.specplt.setYRange(0, 10**12)
        self.speccurve = self.specplt.plot()
        """ Cepstrum Widget """
        self.cepstrum = pg.PlotWidget(title="Cepstrum")
        self.cepsplt = self.cepstrum.plotItem
        self.cepsplt.setXRange(1019, 1029)
        self.cepsplt.setYRange(-3, 3)
        self.cepscurve = self.cepsplt.plot()

    """ -----------------------------------------------------------------------
    Update GUI
    ----------------------------------------------------------------------- """
    def update(self):
        """ Processing """
        self.model.main(self.model.stream)
        """ Rewriting GraphPlot"""
        self.plotdata = np.append(self.plotdata, self.model.plotdata)
        if len(self.plotdata) > self.model.ANALYZEDSIZE:
            self.plotdata = self.plotdata[self.model.CHUNK:]
        self.graphcurve.setData(self.plotdata)
        """ Rewriting Spectrum """
        self.specdata = abs(self.model.power)
        self.speccurve.setData(self.freq, self.specdata)
        """ Rewriting Cepstrum """
        self.cepsdata = self.model.phase
        self.cepscurve.setData(self.cepsdata)

    """ -----------------------------------------------------------------------
    Effector On/Off
    ----------------------------------------------------------------------- """
    def toggle_pre_booster(self, state):
        if state == QtCore.Qt.Checked:
            self.model.pre_booster_on = 1
        else:
            self.model.pre_booster_on = 0

    def toggle_distortion(self, state):
        if state == QtCore.Qt.Checked:
            self.model.distortion_on = 1
        else:
            self.model.distortion_on = 0

    def toggle_phaser(self, state):
        if state == QtCore.Qt.Checked:
            self.model.phaser_on = 1
        else:
            self.model.phaser_on = 0

    def toggle_post_booster(self, state):
        if state == QtCore.Qt.Checked:
            self.model.post_booster_on = 1
        else:
            self.model.post_booster_on = 0

    """ -----------------------------------------------------------------------
    Effector control
    ----------------------------------------------------------------------- """
    def control_pre_booster(self, value):
        self.model.pre_booster_amp = value

    def control_distortion(self, value):
        self.model.distortion_thresh = value

    def control_post_booster(self, value):
        self.model.post_booster_amp = value

    """ -----------------------------------------------------------------------
    key event
    ----------------------------------------------------------------------- """
    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
