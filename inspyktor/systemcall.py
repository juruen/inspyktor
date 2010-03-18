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

from PyQt4.QtCore import QAbstractTableModel, Qt
from PyQt4 import QtCore, QtGui


class SystemCallModel(QAbstractTableModel):
    FIELDS = ['Line', 'Time', 'Name', 'Paramaters', 'Return', 'Errno']
    FIELD_NUMBER = ['line', 'time', 'name', 'parameters',
                'return_value', 'errno', 'elapsed_time']

    def __init__(self):
        QAbstractTableModel.__init__(self, None)
        self._syscalls = []

    def set_strace_runner(self, strace_runner):
        print "Setting strace runner"
        self.strace_runner = strace_runner
        self.connect(self.strace_runner,
            QtCore.SIGNAL('syscall_parsed'), self._slot_syscall_parsed)

    def rowCount(self, parent=None):
        return len(self._syscalls)

    def columnCount(self, parent=None):
        return len(self.FIELDS)

    def data(self, index, role):
        line = self._syscalls[index.row()]

        if role == Qt.TextColorRole and self._syscall_failed(index):
            return QtGui.QColor("red")

        if role != Qt.DisplayRole:
            return  QtCore.QVariant()

        return line[self.FIELD_NUMBER[index.column()]]

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == Qt.Horizontal:
            return self.FIELDS[section]
        else:
            return QtCore.QVariant()

    def clearData(self):
        self._syscalls = []

    def _syscall_failed(self, index):
        row = index.row()
        if len(self._syscalls) <= row:
            return False
        try:
            return_value = int(self._syscalls[row]['return_value'])
        except:
            return False

        return (return_value < 0)

    def _slot_syscall_parsed(self, syscall_info):
        self._syscalls.extend(syscall_info)
        self.reset()
