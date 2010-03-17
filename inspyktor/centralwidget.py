#! /usr/bin/env python
# Copyright (c) 2010 Javier Uruen (juruen@warp.es)
# Licensed under the terms of the MIT license

from inspyktor  import systemcall
from inspyktor.ui import centralwidget
from PyQt4 import QtGui, QtCore


class CentralWidget(QtGui.QWidget, centralwidget.Ui_CentralWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.sysCallModel = systemcall.SystemCallModel()
        self.sysCallView.setModel(self.sysCallModel)
