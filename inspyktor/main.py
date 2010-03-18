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

import inspyktor
import sys

from PyQt4 import QtGui, QtCore
from PyKDE4 import kdeui, kdecore
from inspyktor import stracerunner, mainwindow


def main():
    _ = kdecore.ki18n

    emptyloc = kdecore.KLocalizedString()

    about_data = kdecore.KAboutData(
            inspyktor.__appname__,
            "",
            _(inspyktor.__progname__),
            inspyktor.__version__,
            _(inspyktor.__description__),
            kdecore.KAboutData.License_GPL_V3,
            _(inspyktor.__copyright__),
            emptyloc,
            inspyktor.__homepage__,
            inspyktor.__bts__)

    options = kdecore.KCmdLineOptions()
    options.add("command <command>", _("Command to trace"))
    options.add("pid <pid>", _("PID of existing process to trace"))

    kdecore.KCmdLineArgs.init(sys.argv, about_data)
    kdecore.KCmdLineArgs.addCmdLineOptions(options)

    args = kdecore.KCmdLineArgs.parsedArgs()

    a = kdeui.KApplication()

    strace_runner = stracerunner.StraceRunner()

    if args.isSet("command"):
        split_str = str(args.getOption("command")).split()
        strace_runner.set_trace_command(split_str[0], split_str[1:])
        QtCore.QTimer.singleShot(0, strace_runner.slot_trace_command)

    main_window = mainwindow.MainWindow()
    main_window.show()
    main_window.central_widget.sysCallModel.set_strace_runner(strace_runner)

    sys.exit(a.exec_())
