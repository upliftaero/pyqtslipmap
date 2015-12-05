
import sys
from PyQt4 import QtGui
from PyQtMap import *
from geo import *

STARTLAT = 37.422325
STARTLON = -122.176118
STARTZOOM = 3
class App(QtGui.QMainWindow):

    def __init__(self):
        super(App, self).__init__()
        self.setGeometry(100, 100, 600, 600)
        self.setWindowTitle('QSlipMap Test App')

        self.statusBar().showMessage('Ready')



        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        centerWidget = QWidget(self)
        centerWidget.setLayout(vbox)
        self.setCentralWidget(centerWidget)

        self.map = QSlipMap(self)
        self.map.setCenterCoordinate(QLatLon(STARTLAT, STARTLON))
        self.map.setZoom(STARTZOOM)
        vbox.addWidget(self.map)

        hbox1 = QHBoxLayout()
        self.lat_box = QDoubleSpinBox(self)
        self.lon_box = QDoubleSpinBox(self)
        self.lat_box.setRange(-90.0, 90.0)
        self.lon_box.setRange(-180.0, 180.0)
        self.lat_box.setValue(STARTLAT)
        self.lon_box.setValue(STARTLON)
        self.btn_changepos = QPushButton('Reset &Position', self)
        self.btn_changepos.clicked.connect(self.on_button_change_position)
        hbox1.addWidget(self.lat_box)
        hbox1.addWidget(self.lon_box)
        hbox1.addWidget(self.btn_changepos)

        self.slider_zoom = QSlider(Qt.Horizontal)
        self.slider_zoom.setMinimum(1)
        self.slider_zoom.setMaximum(16)
        self.slider_zoom.setValue(STARTZOOM)
        self.slider_zoom.valueChanged.connect(self.on_zoom_changed)
        vbox.addWidget(self.slider_zoom)


        vbox.addLayout(hbox1)


        self.show()

    def on_button_change_position(self):
        self.map.setCenterCoordinate(QPointF(self.lat_box.value(), self.lon_box.value()))

    def on_zoom_changed(self):
        self.map.setZoom(self.slider_zoom.value())

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())