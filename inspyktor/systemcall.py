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

class SystemCallInfo:
    FIELDS = ['Line', 'Time', 'Name', 'Paramaters', 'Return', 'Errno']

    FIELD_BY_INDEX = [
        'line',
        'time',
        'name',
        'parameters',
        'return_value',
        'errno',
        'elapsed_time'
    ]

    INDEX_BY_FIELD = {
        'line': 0,
        'time': 1,
        'name': 2,
        'parameters': 3,
        'return_value': 4,
        'errno': 5,
        'elapsed_time':6
    }

    @staticmethod
    def param_by_index(syscall, index):
       params = syscall['parameters'].split(',')
       return params[index]

class FdTracker:
    def __init__(self):
        self.fds = {}
        for i, v in enumerate(['STDIN', 'STDOUT', 'STDERR']):
            self.fds[i] = [{
                'open_time': 0,
                'path': v,
                'mode': '',
                'open': True,
                'write_bytes_attempt': 0,
                'write_bytes_success': 0,
                'write_access':0
            }]

    def add_open(self, syscall):
        fd = int(syscall['return_value'])
        if int(fd) < 0:
            return

        fd_ops = self._fd_operations(fd)

        parm_func = SystemCallInfo.param_by_index
        fd_ops.append(
            {
                'open_time': syscall['time'],
                'path': parm_func(syscall, 0),
                'mode': parm_func(syscall, 1),
                'open': True,
                'write_bytes_attempt': 0,
                'write_byts_success': 0,
                'write_access':0
            }
        )

    def add_write(self, syscall):
        fd = int(SystemCallInfo.param_by_index(syscall, 0))
        attempt = int(SystemCallInfo.param_by_index(syscall, 0))
        success = int(syscall['return_value'])
        fd_operations = self._fd_operations(fd)
        if not fd_operations:
            return
        last_op = fd_operations[-1]
        print last_op
        last_op['write_access'] +=  1
        last_op['write_bytes_attempt'] += attempt
        last_op['write_bytes_success'] +=  success
        print last_op

    def _fd_operations(self, fd):
        if not fd in self.fds:
            self.fds[fd] = []
        return self.fds[fd]


class SystemCallDecoder:
    def __init__(self):
        self.fd_tracker = FdTracker()

    def decode(self, syscalls_info):
        for syscall in syscalls_info:
            name = syscall['name']
            if name == 'open':
                self._decode_open(syscall)
            elif name == 'write':
                self._decode_write(syscall)

    def _decode_open(self, syscall):
        self.fd_tracker.add_open(syscall)

    def _decode_write(self, syscall):
        self.fd_tracker.add_write(syscall)

#    def _decode_write(self, syscall):
 #       return _decode_helper(['file', 'text', 'text'])

class SystemCallModel(QAbstractTableModel):
    def __init__(self):
        QAbstractTableModel.__init__(self, None)
        self._syscalls = []
        self.decoder = SystemCallDecoder()

    def set_strace_runner(self, strace_runner):
        self.strace_runner = strace_runner
        self.connect(self.strace_runner,
            QtCore.SIGNAL('syscall_parsed'), self._slot_syscall_parsed)

    def rowCount(self, parent=None):
        return len(self._syscalls)

    def columnCount(self, parent=None):
        return len(SystemCallInfo.FIELDS)

    def data(self, index, role):
        line = self._syscalls[index.row()]

        if role == Qt.TextColorRole and self._syscall_failed(index):
            return QtGui.QColor("red")

        if role != Qt.DisplayRole:
            return  QtCore.QVariant()

        return line[SystemCallInfo.FIELD_BY_INDEX[index.column()]]

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == Qt.Horizontal:
            return SystemCallInfo.FIELDS[section]
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
        self.decoder.decode(syscall_info)
