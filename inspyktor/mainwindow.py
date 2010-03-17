#! /usr/bin/env python
# Copyright (c) 2010 Javier Uruen (juruen@warp.es)
# Licensed under the terms of the MIT license

from inspyktor import centralwidget
from PyKDE4 import kdeui


class MainWindow(kdeui.KMainWindow):
    def __init__(self):
        kdeui.KMainWindow.__init__(self)
        self.central_widget = centralwidget.CentralWidget(self)
        self.setCentralWidget(self.central_widget)
