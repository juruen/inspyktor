#! /usr/bin/env python
# Copyright (c) 2010 Javier Uruen (juruen@warp.es)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from inspyktor import centralwidget
from PyKDE4 import kdeui
from PyQt4 import  QtGui


class MainWindow(kdeui.KXmlGuiWindow):
    def __init__(self):
        kdeui.KXmlGuiWindow.__init__(self)
        self.central_widget = centralwidget.CentralWidget(self)
        self.setCentralWidget(self.central_widget)
        self.setupGUI()

    def init_actions(self):
        action_collection = self.actionCollection()
        self.action_about = kdeui.KStandardAction.aboutApp(
             kdeui.KAboutApplicationDialog(None, self).show,
             actionCollection)
        self.action_about.setShortcutConfigurable(False)
