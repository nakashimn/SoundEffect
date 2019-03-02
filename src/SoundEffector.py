# @package SoundEffectorModel.py
# @brief 入力音声にエフェクトをかけ波形・スペクトラム・ケプストラムを表示します
# @author Nakashima
# @date 2018/9/22
# @version 0.0.1
# @

# import os
import sys
from pyqtgraph.Qt import QtGui
import SoundEffectorModel
import SoundEffectorView
import SoundEffectorController

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    model = SoundEffectorModel.SoundEffectorModel()
    view = SoundEffectorView.SoundEffectorView(model)
    controller = SoundEffectorController.SoundEffectController(view, model)
    try:
        view.show()
        sys.exit(app.exec_())
    except Exception as e:
        print("Error: {}".format(e.argv[1]))
        model.delete()
